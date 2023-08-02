''' Module contains public commands for Ziva VFX operations.
'''
import copy
import logging
import re
import zBuilder.builders.ziva as zva
from collections import defaultdict

from maya import cmds
from maya import mel
from zBuilder.utils.commonUtils import is_string, is_sequence, none_to_empty
from zBuilder.utils.mayaUtils import get_short_name, get_type, safe_rename, build_attr_list
from zBuilder.utils.vfxUtils import get_zSolver, isSolver, check_body_type
from zBuilder.utils.solverDisabler import SolverDisabler
from zBuilder.builders.skinClusters import SkinCluster
from zBuilder.builders.serialize import read, write

logger = logging.getLogger(__name__)

ZIVA_CLIPBOARD_ZBUILDER = None
ZIVA_CLIPBOARD_SELECTION = None
ZIVA_CLIPBOARD_CONTAINS_SOLVER_NODE = False

# All available Ziva nodes to be able to cleanup
ALL_ZIVA_NODES = [
    'zGeo',
    'zSolver',
    'zSolverTransform',
    'zIsoMesh',
    'zDelaunayTetMesh',
    'zTet',
    'zTissue',
    'zBone',
    'zCloth',
    'zSolver',
    'zCache',
    'zEmbedder',
    'zAttachment',
    'zMaterial',
    'zFiber',
    'zCacheTransform',
    'zFieldAdaptor',
    'zRivetToBone',
    'zRestShape',
]


def remove(nodes):
    # Safely remove the given Ziva nodes without worrying about breaking the scene.
    # A solver node can be specified either by its transform node or shape node (or both);
    # in any case, both are removed.
    # The following node types are safe to remove directly.
    safe_to_delete = ['zFiber', 'zAttachment']

    for node in nodes:
        # Check if node still exists.
        if not cmds.objExists(node):
            continue

        # Check if node is a solver, and if so, remove it first.
        if isSolver([node]):
            remove_solver(solvers=[node])

        # Check if node still exists.
        if not cmds.objExists(node):
            continue

        # Check if node is a body, and if so, remove it.
        # We do this first as this will remove other items.
        if check_body_type([node]):
            # If this is a zTissue of zTet, we need to select the mesh before we remove it:
            cmds.select(mel.eval('zQuery -m -l'))
            mel.eval('ziva -rm')
        # Check again if node exists after the body has been removed.
        if cmds.objExists(node):
            if get_type(node) in safe_to_delete:
                _disconnect_node([node])
                cmds.delete(node)


def remove_zRivetToBone_nodes(nodes):
    '''
    Remove zRivetToBone nodes and its connected zRivetToBoneLocator nodes
    according to input Maya scene nodes.

    Args:
        nodes: Maya nodes in the scene

    Return:
        None
    '''
    existed_nodes = {node for node in nodes if cmds.objExists(node)}
    if not existed_nodes:
        return

    def set_rivet(rivet):
        if rivet:
            if is_sequence(rivet):
                nodes_to_delete.extend(rivet)
            else:
                nodes_to_delete.append(rivet)
            locator_list = cmds.listConnections(rivet, type='zRivetToBoneLocator')
            nodes_to_delete.extend(locator_list)

    def set_rivet_locator(locator):
        nodes_to_delete.extend(cmds.listConnections(locator, type='zRivetToBone'))
        nodes_to_delete.extend(cmds.listRelatives(locator, parent=True))

    nodes_to_delete = []
    for node in existed_nodes:
        # 1/4 Collect zRivetToBone node connect to zBone/mesh nodes
        set_rivet(cmds.zQuery(node, rtb=True))

        node_type = cmds.nodeType(node)
        if 'zRivetToBone' == node_type:
            # 2/4 Collect zRivetToBone and its connected zRivetToBoneLocator transform node
            set_rivet(node)
        elif 'zRivetToBoneLocator' == node_type:
            # 3/4 Collect zRivetToBoneLocator transform and zRivetToBone node
            # through zRivetToBoneLocator node
            set_rivet_locator(node)
        elif 'transform' == node_type:
            # 4/4 Collect zRivetToBoneLocator transform and its connected zRivetToBone node
            shape_node = cmds.listRelatives(node)
            if ('zRivetToBoneLocator' == cmds.nodeType(shape_node)):
                set_rivet_locator(shape_node)

    if nodes_to_delete:
        _disconnect_node(nodes_to_delete)
        cmds.select(nodes_to_delete, r=True)
        mel.eval('doDelete')


def remove_solver(solvers=None, askForConfirmation=False):
    # Removes the entire Ziva rig from the solver(s).
    # If no solver is provided, it infers them from selection.
    # If no solver is provided, and nothing is selected, it returns an error.
    # Otherwise, the provided solvers are removed. Solvers can be provided either
    # as a solver transform node, or solver shape node.
    # The command also deletes the solver nodes themselves.
    if solvers is None:
        # If selection is empty, do not select any solvers. Therefore, an error message is printed.
        num_selected_objects = len(cmds.ls(selection=True))
        if num_selected_objects > 0:
            solvers = mel.eval('zQuery -t "zSolver" -l')
        else:
            mel.eval('error -n "Nothing is selected"')
            return
    if solvers is None:
        mel.eval('error -n "No solver selected"')
        return

    # Convert any solver transform nodes to solver shape nodes.
    solvers = mel.eval('zQuery -t "zSolver" -l ' + ' '.join(solvers))
    solver_transforms = mel.eval('zQuery -t "zSolverTransform" -l ' + ' '.join(solvers))

    message = 'This command will remove the solver(s): '
    message += ', '.join(cmds.ls(s)[0]
                         for s in solver_transforms)  # The transforms have nicer names.
    message += ', including all Ziva rigs in them. Proceed?'
    if askForConfirmation:
        response = cmds.confirmDialog(title='Remove Ziva solver(s)',
                                      message=message,
                                      button=['Yes', 'Cancel'],
                                      defaultButton='Yes',
                                      cancelButton='Cancel')
        if response != 'Yes':
            return

    to_erase = []
    meshes_to_unlock = []
    for node in ALL_ZIVA_NODES:
        nodes_in_scene = cmds.ls(type=node)
        for item in nodes_in_scene:
            solver_of_this_item = get_zSolver(item)
            if solver_of_this_item:
                solver_of_this_item = solver_of_this_item[0]
            if solver_of_this_item in solvers:
                to_erase.append(item)
                # unlock the transform attributes
                if (node == 'zTissue') or (node == 'zCloth'):
                    maya_mesh = mel.eval('zQuery -m ' + item)[0]
                    meshes_to_unlock.append(maya_mesh)

    # If anything is referenced, we won't be able to delete it.
    # So, don't start making any changes to the scene if we know it's going to fail.
    has_referenced = any(cmds.referenceQuery(node, isNodeReferenced=True) for node in to_erase)
    if has_referenced:
        mel.eval('error -n "Cannot delete solvers with referenced nodes"')
        return

    for maya_mesh in meshes_to_unlock:
        for attr in ['tx', 'ty', 'tz', 'rx', 'ry', 'rz', 'sx', 'sy', 'sz']:
            # unlock can fail on referenced transforms, so 'catchQuiet' to ignore that
            mel.eval('catchQuiet(`setAttr -lock 0 ' + maya_mesh + '.' + attr + '`)')

    remove_zRivetToBone_nodes(solvers)
    mel.eval('select -cl;')  # needed to avoid Maya error messages
    if len(to_erase) > 0:
        _disconnect_node(to_erase)
        cmds.delete(to_erase)


def remove_all_solvers(confirmation=False):
    # Removes all Ziva solvers from the scene, including all Ziva rigs.
    # All Ziva nodes are removed from the Maya scene.
    # The command also deletes the solvers themselves.
    if confirmation:
        response = cmds.confirmDialog(
            title='Remove all Ziva solvers',
            message=
            'This command will erase all Ziva nodes from the Maya scene. All Ziva nodes, including all solvers, will be erased. Proceed?',
            button=['Yes', 'Cancel'],
            defaultButton='Yes',
            cancelButton='Cancel')
        if response != 'Yes':
            return

    clean_scene()


def rig_cut_copy(cut=False):
    """    Cut or copy the Ziva rig available on currently selected objects into the Ziva clipboard.
    Selection cannot be empty; otherwise an error is reported.
    Selection can contain zero or one solver node; otherwise an error is reported
    (it does not matter if the solver node is a solver transform node, or solver shape node).
    The selected objects must all come from exactly one solver; otherwise an error is reported.


    Args:
        cut (bool, optional): If cut is True, the Ziva rig is removed from the selection after being
                              copied (i.e., perform a cut). Defaults to False.

    Returns:
        bool: True if successful
    """

    global ZIVA_CLIPBOARD_ZBUILDER
    global ZIVA_CLIPBOARD_SELECTION
    global ZIVA_CLIPBOARD_CONTAINS_SOLVER_NODE

    selection = cmds.ls(sl=True, l=True)
    if not selection:
        mel.eval('error -n "Selection is empty. Cut/copy needs a selection to operate on."')
        return False

    # Enforce that the selected objects come from exactly one solver.
    selected_solvers = mel.eval('zQuery -t "zSolver" -l')
    if selected_solvers is None:
        mel.eval('error -n "Selected objects are not connected to a solver."')
        return False
    if len(selected_solvers) >= 2:
        mel.eval(
            'error -n "Selected objects come from two or more solvers. Inputs to cut/copy must come from only one solver."'
        )
        return False

    # Record if selection contains a solver node.
    # We'll need this information when pasting.
    # Also check if selection contains two or more solver nodes. This is an error.
    num_solver_nodes = 0
    for item in selection:
        if isSolver([item]):
            num_solver_nodes = num_solver_nodes + 1
    if num_solver_nodes == 0:
        ZIVA_CLIPBOARD_CONTAINS_SOLVER_NODE = False
    elif num_solver_nodes == 1:
        ZIVA_CLIPBOARD_CONTAINS_SOLVER_NODE = True
    else:
        mel.eval('error -n "Selection contains more than one solver node. "')
        return False

    ZIVA_CLIPBOARD_ZBUILDER = zva.Ziva()
    ZIVA_CLIPBOARD_ZBUILDER.retrieve_from_scene_selection()

    ZIVA_CLIPBOARD_SELECTION = selection

    if cut:
        remove(selection)

    return True


def rig_cut():
    """ Cut selected.

    Returns:
        bool: True if successful
    """
    # Cut Ziva rig. See rig_cut_copy for instructions.
    result = rig_cut_copy(cut=True)
    return result


def rig_copy():
    """Copy selected.

    Returns:
        bool: True if successful
    """
    # Copy Ziva rig. See rig_cut_copy for instructions.
    result = rig_cut_copy(cut=False)
    return result


def rig_paste():
    # Paste the Ziva rig from the Ziva clipboard onto scene geometry.
    # If nothing is selected, or the Ziva clipboard contains an explicit solver node,
    # the Ziva rig is applied to scene geometry that is named inside the Ziva clipboard.
    # If something is selected, then:
    #   source selection 1 is pasted onto target selection 1;
    #   source selection 2 is pasted onto target selection 2; and so on.
    # The pasted Ziva rig is added to the solver that was used for the last cut/copy operation.
    # If such a solver does not exist any more in the Maya scene (because, say, it has been cut),
    # it is created.
    global ZIVA_CLIPBOARD_ZBUILDER
    global ZIVA_CLIPBOARD_SELECTION
    if ZIVA_CLIPBOARD_ZBUILDER is None:
        mel.eval('error -n "Ziva clipboard is empty. Need to cut/copy into it."')
        return

    # We need to do a deep copy of ziva_clipboard_zbuilder because we want to manipulate
    # it (using string_replace), and not change the original ziva_clipboard_zbuilder object.
    # In this way, we can paste the same clipboard multiple times.

    # Make the deepcopy
    builder = copy.deepcopy(ZIVA_CLIPBOARD_ZBUILDER)

    source_selection = ZIVA_CLIPBOARD_SELECTION
    target_selection = cmds.ls(sl=True, l=True)
    num_object_to_paste = min([len(source_selection), len(target_selection)])

    # If nothing is selected when we paste, or the clipboard contains a solver node,
    # we paste without any name substitution.
    # Otherwise, perform name substitution:
    #     source selection 1 is pasted onto target selection 1;
    #     source selection 2 is pasted onto target selection 2; and so on.
    if not (target_selection == [] or ZIVA_CLIPBOARD_CONTAINS_SOLVER_NODE):
        for i in range(0, num_object_to_paste):
            builder.string_replace(get_short_name(source_selection[i]),
                                   get_short_name(target_selection[i]))
    builder.build()


def rig_update(solvers=None):
    # Updates the Ziva rig in the solver(s).
    # This command can be used if you made geometry modifications and you'd like to re-use a previously
    # built Ziva rig on the modified geometry.
    # If no "solvers" are provided, they are inferred from selection.
    if solvers is None:
        solvers = mel.eval('zQuery -t "zSolver" -l')

    # zQuery gives an error if no solvers though it does not stop script
    # this is to stop script
    if solvers is None:
        raise Exception("No solver in scene.")

    for solver in solvers:
        # select the solver, and read the Ziva setup from solver into the zBuilder object
        cmds.select(solver)
        builder = zva.Ziva()
        builder.retrieve_from_scene()

        # remove existing solver
        remove_solver(solvers=[solver])

        # re-build the solver
        builder.build()


def rig_transfer(source_solver, prefix, target_solver=""):
    # Transfers the Ziva rig from 'sourceSolver' to another solver (targetSolver).
    # This command does not transfer the geometry. It assumes that a copy of the geometry from
    # sourceSolver is already available in the scene, prefixed by "prefix" (without the quotes).
    # For example, if sourceSolver is 'zSolver1', and prefix is 'warped_', and 'zSolver1' has a
    # tissue geometry (a mesh) called "tissue1", then this command assumes that there is a mesh
    # called "warped_tissue1" in the scene.
    # The command generates a Ziva rig on the 'warped_*' geometry, in the targetSolver.
    # If targetSolver is "", the command sets the targetSolver to sourceSolver + prefix.
    # If targetSolver does not exist yet, the command generates it.
    # Note that the targetSolver may be the same as the sourceSolver, in which case the rig
    # on the 'warped_*' geometry is added into the sourceSolver.
    if target_solver == "":
        target_solver = prefix + get_short_name(source_solver)  # default target solver

    cmds.select(source_solver)
    builder = zva.Ziva()
    builder.retrieve_from_scene()

    # rename to prefix
    builder.string_replace('^', prefix)
    builder.string_replace(
        '^' + prefix + get_short_name(source_solver),
        target_solver)  # rename the solver stored in the zBuilder to targetSolver

    builder.build()


def skincluster_transfer(prefix=""):
    """ Transfer the skin clusters for some selected meshes onto their warped counterparts
        and to connect the warped joint hierarchy.
        This requires both geometries (selected and warped) have the same topology.
        Also, the names of the warped meshes must be prefixed with "prefix".
        Note: Warp the source meshes and the corresponding joint hierarchy before running the command.
    """
    selected_nodes = cmds.ls(sl=True)
    if len(selected_nodes) == 0:
        cmds.error("Must select at least one mesh.\n")

    if prefix == "":
        cmds.error('Must specify a prefix.')

    builder = SkinCluster()
    builder.retrieve_from_scene()
    builder.string_replace('^', prefix)
    builder.build()


def load_rig(file_name, solver_name=None):
    # Load a Ziva rig from a file. Geometry must already be in the scene.
    # If solverName is not provided, the rig is applied to the solver stored in the zBuilder file.
    # If solverName is provided, replace the name of the solver stored in the zBuilder file
    # with a given solverName, and apply the rig to that solver.
    builder = zva.Ziva()
    read(file_name, builder)
    if solver_name != None:
        # replace the solver name stored in the .zBuilder file with solverName
        solver_name_in_file = builder.get_scene_items(type_filter='zSolverTransform')[0].name
        builder.string_replace(solver_name_in_file, solver_name)
    builder.build()


def save_rig(file_name):
    # Save a Ziva rig to a file.
    # If there is only one solver in the scene, it is saved.
    # If there is multiple solvers, save the first solver in the union
    # of selected solvers and the default solver.
    builder = zva.Ziva()
    builder.retrieve_from_scene()
    write(file_name, builder)


def copy_paste_with_substitution(regular_expression, string_to_substitute_matches_with):
    """ Copy/Pastes the Ziva objects of the selected objects onto non-Ziva-rigged objects
    whose names are defined using regular expressions.

    This is useful, for example, for mirroring a Ziva rig, rig one side of the character first,
    then use this command to automatically "copy" the rig to the other side.
    Of course, objects must follow a proper naming convention, such as l_humerus, r_humerus, or similar.

    The specific naming convention is defined via a regular expression
    and a string with which to replace any regular expression matches.
    For example, if regular expression is "^l_" and string to substitute with is "r\_",
    then all instances of geometry that begin with "r\_" will be rigged in the same way
    as the corresponding geometry that begins with "l\_".
    The selected objects should come from exactly one solver.
    Upon exiting, the command selects a few common Ziva node types (zTissue, zBone, zCloth),
    for better visual feedback to the user.
    """
    logger.warning(
        'This method is deprecated and will be removed in future. Use mirror() defined in zBuilder.commands instead.'
    )
    builder = zva.Ziva()
    builder.retrieve_from_scene_selection()
    builder.string_replace(regular_expression, string_to_substitute_matches_with)
    # TODO: pass mirror=True to let build know that its a mirror build. VFXACT-1111
    builder.build()

    # Select the new items that have been pasted, for better visual feedback to the user.
    # Look into the zBuilder object and find the meshes associated with a few common Ziva node
    # types:
    displayed_node_types = ['zTissue', 'zBone', 'zCloth']
    # clear selection
    cmds.select(cl=True)
    for displayed_node_type in displayed_node_types:
        for item in builder.get_scene_items(type_filter=displayed_node_type):
            # Add each mesh of this type to selection.
            cmds.select(item.nice_association, add=True)


# Begin merge_two_solvers() section
def _next_free_plug_in_array(dst_plug):
    # type: (str) -> str
    """ Use this to work around the fact that zSolver.iGeo (and other attrs)
    have indexMatters=True even though the index does n't matter. As a result,
    connectAttr(a,b,indexMatter=True) won't work on those attrs. We need to 
    find a specific array element to connect to instead.

    This function takes a plug name, and if it's an element of an array,
    sets the index to a free index. Else, it's the identity function.

    _next_free_plug_in_array('foo.bar[7]') --> 'foo.bar[42]'
    _next_free_plug_in_array('foo.bar') --> 'foo.bar'
    """

    array_match = re.search(r"(.*)\[\d+\]$", dst_plug)
    if array_match:
        plug = array_match.group(1)
        indices = cmds.getAttr(plug, multiIndices=True)
        new_index = indices[-1] + 1 if indices else 0  # [-1] assumes indices are sorted
        new_dst = '{}[{}]'.format(plug, new_index)
        return new_dst
    return dst_plug


def _list_connection_plugs(node, destination=True, source=True):
    # type: (str, bool, bool) -> List[Tuple[basestring,basestring]]
    """ Get all of the connections with 'node' as a list of pairs of plugs.
    The first plug in each pair is a plug on 'node'. The second plug in each
    pair is a plug the first is connected to. """
    assert is_string(node), 'Arguments #1 is not a string'
    assert isinstance(destination, bool), 'Arguments "destination" is not a bool'
    assert isinstance(source, bool), 'Arguments "source" is not a bool'
    plugs = cmds.listConnections(node,
                                 plugs=True,
                                 connections=True,
                                 source=source,
                                 destination=destination)
    plugs = plugs if plugs else []  # Convert Maya's None result to an empty list
    assert len(plugs) % 2 == 0, "List does not have an even number of elements " + str(plugs)
    return zip(plugs[0::2], plugs[1::2])


def merge_two_solvers(solver_transform1, solver_transform2):
    # type: (str, str) -> None
    """ 
    Given two solvers,
    take everything from the second solver and put it into the first solver.
    Then, delete the second solver.
    See 'merge_solvers' for details.
    e.g. merge_two_solvers('zSolver1', 'zSolver2')
    """
    ####################################################################
    # Checking inputs
    assert is_string(solver_transform1), 'Arguments #1 is not a string'
    assert is_string(solver_transform2), 'Arguments #2 is not a string'
    assert cmds.nodeType(
        solver_transform1) == 'zSolverTransform', 'Argument #1 is not a zSolverTransform'
    assert cmds.nodeType(
        solver_transform2) == 'zSolverTransform', 'Argument #2 is not a zSolverTransform'
    assert solver_transform1 != solver_transform2, 'The two solvers are not different'

    solver1 = mel.eval('zQuery -t zSolver {}'.format(solver_transform1))[0]
    solver2 = mel.eval('zQuery -t zSolver {}'.format(solver_transform2))[0]
    embedder1 = mel.eval('zQuery -t zEmbedder {}'.format(solver_transform1))[0]
    embedder2 = mel.eval('zQuery -t zEmbedder {}'.format(solver_transform2))[0]

    ####################################################################
    # For speed and to reduce noise, try to disable the solvers

    # SolverDisabler's __enter__ will do what we want for solver2,
    # but we're going to delete solver2, so we do not want __exit__ to be called. Thus:
    SolverDisabler(solver_transform2).__enter__()

    with SolverDisabler(solver_transform1):
        ####################################################################
        # logger.info('Re-wiring outputs of {} to come from {}'.format(solver2, solver1))
        for src, dst in _list_connection_plugs(solver2, source=False):
            cmds.disconnectAttr(src, dst)
            new_src = src.replace(solver2, solver1, 1)
            try:
                cmds.connectAttr(new_src, dst)
            except:
                logger.info('Skipped new connection {} {}'.format(src, dst))

        ####################################################################
        # logger.info('Re-wiring inputs of {} to go to {}'.format(solver2, solver1))
        for dst, src in _list_connection_plugs(solver2, destination=False):
            cmds.disconnectAttr(src, dst)
            new_dst = dst.replace(solver2, solver1, 1)
            new_dst = _next_free_plug_in_array(new_dst)
            try:
                cmds.connectAttr(src, new_dst)
            except:
                if not new_dst.endswith('iSolverParams'):  # We _expect_ this plug to fail.
                    logger.info('Skipped new connection {} {}'.format(src, new_dst))

        ####################################################################
        # logger.info('Re-wiring outputs of {} to come from {}'.format(solver_transform2, solver_transform1))
        for src, dst in _list_connection_plugs(solver_transform2, source=False):
            cmds.disconnectAttr(src, dst)
            new_src = src.replace(solver_transform2, solver_transform1, 1)
            try:
                cmds.connectAttr(new_src, dst)
            except:
                logger.info('Skipped new connection {} {}'.format(src, dst))

        ####################################################################
        # logger.info('Adding shapes from {} to {}'.format(embedder2, embedder1))

        # From embedder2, find all of the embedded meshes and which zGeoNode they're deformed by.
        tissue_geo_plugs = none_to_empty(
            cmds.listConnections('{}.iGeo'.format(embedder2),
                                 plugs=True,
                                 source=True,
                                 destination=False))
        meshes = none_to_empty(cmds.deformer(embedder2, query=True, geometry=True))
        indices = set(none_to_empty(cmds.deformer(embedder1, query=True, geometryIndices=True)))

        # Add all of the meshes from embedder2 onto embedder1, and connect up the iGeo to go with it.
        for mesh, geo_plug in zip(meshes, tissue_geo_plugs):
            cmds.deformer(embedder2, edit=True, remove=True, geometry=mesh)
            cmds.deformer(embedder1, edit=True, before=True,
                          geometry=mesh)  # "-before" for referencing
            # TODO: how do I get the index of a mesh without this mess?
            new_indices = set(cmds.deformer(embedder1, query=True, geometryIndices=True))
            new_index = list(new_indices - indices)[0]
            indices = new_indices
            cmds.connectAttr(geo_plug, '{}.iGeo[{}]'.format(embedder1, new_index))

        ####################################################################
        # logger.info('Trying to delete stale solver {}'.format(solver_transform2))

        for node in [solver2, solver_transform2, embedder2]:
            # Referenced nodes are 'readOnly; and cannot be deleted or renamed - leave them alone.
            if not cmds.ls(node, readOnly=True):
                cmds.delete(node)


# End merge_two_solvers() section


def merge_solvers(solver_transforms):
    # type: (List[str]) -> None
    """ 
    Given a list of zSolverTransform nodes, merge them all into the first solver.

    The zSolverTransform, zSolver, and zEmbedder nodes for all but the first solver
    in the list will be deleted. If that's not possible, such as when the solvers are
    referenced nodes, those solvers will remain in the scene but be empty.
    They will have no bones, tissues, cloth, attachments, etc.

    The first solver keeps all of its attribute values and connections.
    Any differences between this solver and the others is ignored.

    All other nodes (besides the zSolverTransform, zSolver, and zEmbedder) are
    re-wired to connect to the first solver. All existing attributes, connections,
    or any other properties remain unchanged.

    e.g. merge_solvers(['zSolver1', 'zSolver2', 'zSolver2'])
    """
    assert is_sequence(solver_transforms), 'Arguments #1 is not a list'

    if len(solver_transforms) < 2:
        return
    solver1 = solver_transforms[0]

    with SolverDisabler(solver1):
        for solver2 in solver_transforms[1:]:
            merge_two_solvers(solver1, solver2)


def clean_scene():
    """
    Deletes all Ziva nodes in scene.  Effectively cleaning it up.
    """
    solvers = cmds.ls(type='zSolver')
    remove_zRivetToBone_nodes(solvers)

    for node in ALL_ZIVA_NODES:
        in_scene = cmds.ls(type=node)
        if in_scene:
            _disconnect_node(in_scene)
            cmds.delete(in_scene)


def _disconnect_node(nodes):
    """
    if you have a utility node hooked up to the ziva rig, like a remap

    remap.outputX -> fiber1.excitation

    And the fiber is removed, maya tries to be efficient and it will delete the remap node.
    The solution is to disconnect any node connected to a ziva rig before we remove items.
    """
    for node in nodes:
        attrs = build_attr_list(node)
        # zRestShape attribute being used for zRBF connections
        attrs.append('targetWeight[0]')
        for attr in attrs:
            if cmds.objExists(node + '.' + attr):
                connection = cmds.listConnections(node + '.' + attr, p=True, c=True)
                if connection:
                    cmds.disconnectAttr(connection[1], connection[0])
                    logger.info('disconnecting {} -> {}'.format(connection[1], connection[0]))


# Begin rename_ziva_nodes() section
def _strip_namespace(node):
    return node.split(':')[-1]


def _is_default_name(node, node_type):
    """ This checks if the name matches the default name pattern.
    The default name pattern is node type followed by digits.

    zFiber21
    zMaterial1
    zAttachment45
    """
    if node_type == 'zRiveToBoneLocator':
        _type = 'zRivet'
    else:
        _type = node_type

    return re.search(_type + '\d+$', node)


def _znode_rename_helper(zNode, postfix, solver, suffix_to_remove, force=False):
    """ Renames all the zNodes of a zSolver.
    Args:
        zNode (string): node type
        postfix (string): postfix to use for renaming
        solver (string): solver name
        suffix_to_remove (list): list of strings to remove from the new name
    """
    meshes = mel.eval('zQuery -t "{}" -m "{}"'.format(zNode, solver))
    if meshes:
        for mesh in meshes:
            nodes = mel.eval('zQuery -t "{}" "{}"'.format(zNode, mesh))
            mesh = _strip_namespace(mesh)
            for r in suffix_to_remove:
                mesh = mesh.replace(r, '')

            for i, node in enumerate(nodes):
                if _is_default_name(node, cmds.objectType(node)) or force:
                    if zNode in ['zMaterial', 'zFiber']:
                        new_name = '{}_{}{}'.format(mesh, zNode, str(i + 1))
                    else:
                        new_name = '{}_{}'.format(mesh, zNode)
                    safe_rename(node, '{}{}'.format(new_name, postfix))


def _rivet_to_bone_rename_helper(rtbs, postfix, suffix_to_remove, force=False):
    """
    The same idea as for _znode_rename_helper but for zRivetToBone
    Args:
        rtbs (list): list of zRivetToBone nodes to rename
        postfix (string): postfix to use for renaming
        suffix_to_remove (list): list of strings to remove from the new name

    Returns:
        lists: old names, new names, (rivetToBone, curve) tuple
    """
    old_names = []
    new_names = []
    for rtb in rtbs:
        crv = cmds.listConnections(rtb + '.outputGeometry', shapes=True)
        # If curve has multiple zRivetToBone nodes, need to search zRivetToBone connections
        # until curve is found
        while crv:
            if cmds.nodeType(crv[0]) == 'nurbsCurve':
                break
            else:
                crv = cmds.listConnections(crv[0] + '.outputGeometry', shapes=True)
        crv = cmds.listRelatives(crv, p=True)
        if crv:
            crv = crv[0]
            for r in suffix_to_remove:
                crv = crv.replace(r, '')
            crv = _strip_namespace(crv)
            new_name_rtb = '{}_{}'.format(crv, 'zRivetToBone1')
            if rtb != new_name_rtb:
                if _is_default_name(rtb, 'zRivetToBone') or force:
                    new_name_rtb = safe_rename(rtb, '{}{}'.format(new_name_rtb, postfix))
                    if new_name_rtb:
                        old_names.append(rtb)
                        new_names.append(new_name_rtb)

    return old_names, new_names


def _rivet_to_bone_locator_rename_helper(rtbs, postfix, force=False):
    """
    Rename 'zRivetToBone' locator nodes.
    Args:
        rtbs (list): list of zRivetToBone nodes to rename
        postfix (string): postfix to use for renaming
    """
    for rtb in rtbs:
        rtb_locator = cmds.listConnections('{}.segments'.format(rtb))
        if _is_default_name(rtb_locator[0], 'zRiveToBoneLocator')  or force:
            cmds.rename(rtb_locator, '{}{}'.format(rtb.replace('zRivetToBone', 'zRivet'), postfix))

def _attachment_rename_helper(attachments, postfix, suffix_to_remove, force=False):
    """
    Rename 'zAttachment' nodes.  This names them based on the source and target mesh.
    example:
        r_bicep__r_humerus_zAttachment1
    Args:
        attachments (list): list of zAttachments nodes to rename
        postfix (string): postfix to use for renaming
        suffix_to_remove (list): list of strings to remove from the new name
    """
    record = defaultdict(list)
    for attachment in attachments:
        source = cmds.zQuery(attachment, attachmentSource=True)[0]
        for r in suffix_to_remove:
            source = source.replace(r, '')
        source = _strip_namespace(source)
        target = cmds.zQuery(attachment, attachmentTarget=True)[0]
        for r in suffix_to_remove:
            target = target.replace(r, '')
        target = _strip_namespace(target)
        new_name = '{}__{}_{}'.format(source, target, 'zAttachment')
        record[new_name].append(new_name)
        new_name = '{}__{}_{}{}'.format(source, target, 'zAttachment', len(record[new_name]))
        if _is_default_name(attachment, 'zAttachment') or force:
            safe_rename(attachment, '{}{}'.format(new_name, postfix))

def rename_ziva_nodes(replace=['_muscle', '_bone'], force=False):
    """ Renames zNodes based on mesh it's connected to.

    args:
        replace (list): subset of mesh name to replace with zNode name

    * zFiber: <meshName>_zFiber
    * zMaterial: <meshName>_zMaterial
    * zTet: <meshName>_zTet
    * zTissue: <meshName>_zTissue
    * zBone: <meshName>_zBone
    * zCloth: <meshName>_zCloth
    * zRestShape: <meshName>_zRestShape
    * zAttachment: <sourceMesh>__<destinationMesh>_zAttachment
    """
    sel = cmds.ls(sl=True)
    cmds.select(cl=True)
    solver = mel.eval('zQuery -t "zSolver"')

    if not solver:
        return

    zNodes = ['zTissue', 'zTet', 'zMaterial', 'zFiber', 'zBone', 'zCloth', 'zRestShape']

    for zNode in zNodes:
        # If you have multiple zMaterials on a mesh and it tries to name a material
        # same name as an existing material it will fail.  This is why we name in 2
        # passes to get rid of any potential name collisions.
        _znode_rename_helper(zNode, '00', solver[0], replace, force=force)
        _znode_rename_helper(zNode, '', solver[0], replace, force=force)

    # rename zLineOfAction nodes
    loas = mel.eval('zQuery -loa {}'.format(solver[0]))
    if loas:
        for loa in loas:
            crv = cmds.listConnections(loa + '.oLineOfActionData')
            if crv:
                crv = _strip_namespace(crv[0])
                new_name = crv + '_zLineOfAction'
                if _is_default_name(loa, 'zLineOfAction') or force:
                    new_name = safe_rename(loa, new_name)

    # rename zRivetToBone nodes
    rtbs = mel.eval('zQuery -rtb {}'.format(solver[0]))
    if rtbs:
        old_names, new_names = _rivet_to_bone_rename_helper(rtbs, '00', replace, force=force)
        _, new_names = _rivet_to_bone_rename_helper(new_names, '', replace, force=force)

        # zRivetToBones names have changed so we need to re-query.
        rtbs = mel.eval('zQuery -rtb {}'.format(solver[0]))
        # We need to run through the _rivet_to_bone_locator_rename_helper twice here.
        # If you have muscleA, muscleB and muscleC and want to rename muscleA to muscleC
        # there will be a name collision and renaming will not work.
        # By appending a '00' to name first, as below, we get around this name collision.
        _rivet_to_bone_locator_rename_helper(rtbs, '00', force=force)
        _rivet_to_bone_locator_rename_helper(rtbs, '', force=force)

    attachments = mel.eval('zQuery -t "{}" {}'.format('zAttachment', solver[0]))
    if attachments:
        _attachment_rename_helper(attachments, '00', replace, force=force)
        # since names have changed from first run we need to re-query the attachments.
        attachments = mel.eval('zQuery -t "{}" {}'.format('zAttachment', solver[0]))
        _attachment_rename_helper(attachments, '', replace, force=force)

    for s in sel:
        if cmds.objExists(s):
            cmds.select(s, add=True)
    logger.info('finished renaming.... ')


# End rename_ziva_nodes() section


def mirror(source_prefix='^l_', target_prefix='r_', center_prefix='c_', mirror_axis='X'):
    """ Mirrors a Ziva VFX setup.  Select the solver and run the command to mirror whole setup. Select a part of the rig
    to mirror a subset of the whole setup.

    Args:
        source_prefix (str): Prefix of geometry on the source side. Defaults to '^l_'
        target_prefix (str): Prefix of geometry on the target side. Defaults to 'r\_'
        center_prefix (str): Prefix of the geometry of the center. Defaults to 'c\_'
        mirror_axis (str): Axis to mirror on. Defaults to 'x'
    Usage:
    import zBuilder.commands as com
    com.mirror()
    """

    builder = zva.Ziva()
    builder.retrieve_from_scene_selection()

    # remove target side from zBuilder by filtering by target_prefix
    items_to_delete = []
    for item in builder.get_scene_items():
        if item.name.startswith(target_prefix):
            items_to_delete.append(item)
            continue

        # Some item names wont start with target_prefix.  This can happen if user
        # is not using a naming convention or default names are being used.
        # We need to remove these as well and we are going to use the mesh for that.

        if item.type not in ['mesh', 'map']:
            for mesh in item.association:
                if mesh.startswith(target_prefix):
                    items_to_delete.append(item)
                    continue

    for item in items_to_delete:
        builder.remove_scene_item(item)

    # perform the mirror internally.  That is replace source_prefix with target_prefix in the internal scene items.
    builder.string_replace(source_prefix, target_prefix)

    # after the string replace we need to do another pass on attachment and map names.  A basic naming convention of
    # attachments, through the use of rename_ziva_nodes, is to name them with source and target mesh.  As a result
    # you get names like so:
    # c_sourceMesh__l_targetMesh_zAttachment1
    # we need to split that name and perform a re.sub on second element
    for attachment in builder.get_scene_items(type_filter='zAttachment'):
        maps = attachment.parameters['map']
        for obj in [attachment, maps[0], maps[1]]:
            split = obj.name.split('__')
            if len(split) == 2:
                obj.name = (split[0]+'__'+re.sub(source_prefix, target_prefix, split[1]))


    # We need to mirror the internally stored mesh on the mirror axis.
    for mesh_node in builder.get_scene_items(type_filter='mesh'):
        if mesh_node.name.startswith(center_prefix):
            mesh_node.mirror(mirror_axis=mirror_axis)

    # Once mirrored we can interpolate the maps.
    # This accomplishes flipping the map on the opposite side of the mesh once applied.
    for map_node in builder.get_scene_items(type_filter='map'):
        if map_node.get_mesh().startswith(center_prefix):
            for item in map_node.name.split('__'):
                if item.startswith(target_prefix):
                    map_node.interpolate()
                    break

    # before we build we need to clean the maya scene of any target nodes.
    # So lets look for any meshes of a zTissue, zCloth or zBone.  From there
    # we can delete nodes in the maya scene.
    for item in builder.get_scene_items(type_filter=['zTissue', 'zCloth', 'zBone']):
        if item.association[0].startswith(target_prefix):
            cmds.select(item.association[0])
            to_delete = none_to_empty(cmds.zQuery(type='zAttachment'))
            to_delete.extend(none_to_empty(cmds.zQuery(type='zFiber')))
            to_delete.extend(none_to_empty(cmds.zQuery(type='zRestShape')))
            materials = none_to_empty(cmds.zQuery(type='zMaterial'))
            # We are removing extra nodes from scene to create a place to build our setup.
            # we are leaving a single zMaterial node as by default thats what happens when
            # you create a zTissue.
            to_delete.extend(materials[1:])

            if to_delete:
                cmds.delete(to_delete)

        # To mirror collision sets we want them to be in a different group so
        # we use the multiplier.  I set the default to this as 100 thinking it
        # is a large enough number where there should be a big enough gap.
        # If the user has goups like so
        # 1 100 200
        # and use default mult they would get groups
        # 100 10000 20000
        # so the 100's here overlap and are now in same group.  I think this would be a rare
        # occurance.
        collision_set_mult = 100
        collision_sets = item.attrs['collisionSets']['value']
        new_collision_set = re.split(r',| ', collision_sets)
        new_collision_set = filter(lambda s: s.isdigit(), new_collision_set)
        new_collision_set = [str(int(x) * collision_set_mult) for x in new_collision_set]
        item.attrs['collisionSets']['value'] = ' '.join(new_collision_set)

    # now we build, though we need to turn OFF interpolation so we dont accidently
    # interpolate twice
    builder.build(interp_maps=False, target_prefix=target_prefix, center_prefix=center_prefix)
