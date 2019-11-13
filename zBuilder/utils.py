import logging
import re
import copy

import maya.cmds as mc
import maya.mel as mm

import zBuilder.zMaya as mz
import zBuilder.builders.ziva as zva
import zBuilder.builders.skinClusters as skn

ZIVA_CLIPBOARD_ZBUILDER = None
ZIVA_CLIPBOARD_SELECTION = None
ZIVA_CLIPBOARD_CONTAINS_SOLVER_NODE = False

logger = logging.getLogger(__name__)


def copy_paste(*args, **kwargs):
    '''
    A utility wrapper for copying and pasting a tissue
    '''
    sel = mc.ls(sl=True)

    selection = None
    if args:
        selection = mc.ls(args[0], l=True)
    else:
        selection = mc.ls(sl=True, l=True)

    builder = zva.Ziva()
    builder.retrieve_from_scene_selection(selection[0])
    builder.string_replace(selection[0].split('|')[-1], selection[1].split('|')[-1])
    builder.stats()
    builder.build(**kwargs)

    mc.select(sel)


def check_map_validity():
    """
    This checks the map validity for zAttachments and zFibers.  For zAttachments
    it checks if all the values are zero.  If so it failed and turns off the
    associated zTissue node.  For zFibers it checks to make sure there are at least
    1 value of 0 and 1 value of .5 within a .1 threshold.  If not that fails and
    turns off the zTissue

    Returns:
        list of offending maps
    """
    sel = mc.ls(sl=True)

    # we are going to check fibers and attachments
    mc.select(mc.ls(type=['zAttachment', 'zFiber']), r=True)

    builder = zva.Ziva()
    builder.retrieve_from_scene_selection(connections=False)

    mz.check_map_validity(builder.get_scene_items(type_filter='map'))

    mc.select(sel, r=True)


def remove(nodes):
    # Safely remove the given Ziva nodes without worrying about breaking the scene.
    # A solver node can be specified either by its transform node or shape node (or both);
    # in any case, both are removed.
    # The following node types are safe to remove directly.
    safe_to_delete = ['zFiber', 'zAttachment']

    for node in nodes:
        # Check if node still exists.
        if not mc.objExists(node):
            continue

        # Check if node is a solver, and if so, remove it first.
        if mz.isSolver([node]):
            remove_solver(solvers=[node])

        # Check if node still exists.
        if not mc.objExists(node):
            continue

        # Check if node is a body, and if so, remove it.
        # We do this first as this will remove other items.
        if mz.check_body_type([node]):
            # If this is a zTissue of zTet, we need to select the mesh before we remove it:
            mc.select(mm.eval('zQuery -m'))
            mm.eval('ziva -rm')
        # Check again if node exists after the body has been removed.
        if mc.objExists(node):
            if mc.objectType(node) in safe_to_delete:
                mc.delete(node)


def remove_solver(solvers=None, askForConfirmation=False):
    # Removes the entire Ziva rig from the solver(s).
    # If no solver is provided, it infers them from selection.
    # If no solver is provided, and nothing is selected, it returns an error.
    # Otherwise, the provided solvers are removed. Solvers can be provided either
    # as a solver transform node, or solver shape node.
    # The command also deletes the solver nodes themselves.
    if solvers is None:
        # If selection is empty, do not select any solvers. Therefore, an error message is printed.
        num_selected_objects = len(mc.ls(selection=True))
        if num_selected_objects > 0:
            solvers = mm.eval('zQuery -t "zSolver" -l')
        else:
            mm.eval('error -n "Nothing is selected"')
            return
    if solvers is None:
        mm.eval('error -n "No solver selected"')
        return

    # Convert any solver transform nodes to solver shape nodes.
    solvers = mm.eval('zQuery -t "zSolver" -l ' + ' '.join(solvers))

    message = 'This command will remove the solver(s): '
    for solver in solvers:
        short_solver_name = mc.ls(solver)[0][:-5]  # remove 'Shape' at the end
        message += short_solver_name + ', '
    message += 'including all Ziva rigs in them. Proceed?'
    if askForConfirmation:
        response = mc.confirmDialog(title='Remove Ziva solver(s)',
                                    message=message,
                                    button=['Yes', 'Cancel'],
                                    defaultButton='Yes',
                                    cancelButton='Cancel')
        if response != 'Yes':
            return

    to_erase = []
    for node in mz.ZNODES:
        nodes_in_scene = mc.ls(type=node)
        for item in nodes_in_scene:
            solver_of_this_item = mz.get_zSolver(item)
            if solver_of_this_item:
                solver_of_this_item = solver_of_this_item[0]
            if solver_of_this_item in solvers:
                to_erase.append(item)
            # unlock the transform attributes
            if (node == 'zTissue') or (node == 'zCloth'):
                maya_mesh = mm.eval('zQuery -m ' + item)[0]
                attrs = ['tx', 'ty', 'tz', 'rx', 'ry', 'rz', 'sx', 'sy', 'sz']
                for attr in attrs:
                    mm.eval('setAttr -lock 0 ' + maya_mesh + '.' + attr)

    mz.delete_rivet_from_solver(solvers)
    mm.eval('select -cl;')  # needed to avoid Maya error messages
    if len(to_erase) > 0:
        mc.delete(to_erase)


def remove_all_solvers(confirmation=False):
    # Removes all Ziva solvers from the scene, including all Ziva rigs.
    # All Ziva nodes are removed from the Maya scene.
    # The command also deletes the solvers themselves.
    if confirmation:
        response = mc.confirmDialog(
            title='Remove all Ziva solvers',
            message=
            'This command will erase all Ziva nodes from the Maya scene. All Ziva nodes, including all solvers, will be erased. Proceed?',
            button=['Yes', 'Cancel'],
            defaultButton='Yes',
            cancelButton='Cancel')
        if response != 'Yes':
            return

    mz.clean_scene()


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

    selection = mc.ls(sl=True)
    if not selection:
        mm.eval('error -n "Selection is empty. Cut/copy needs a selection to operate on."')
        return False

    # Enforce that the selected objects come from exactly one solver.
    selected_solvers = mm.eval('zQuery -t "zSolver" -l')
    if selected_solvers is None:
        mm.eval('error -n "Selected objects are not connected to a solver."')
        return False
    if len(selected_solvers) >= 2:
        mm.eval(
            'error -n "Selected objects come from two or more solvers. Inputs to cut/copy must come from only one solver."'
        )
        return False

    # Record if selection contains a solver node.
    # We'll need this information when pasting.
    # Also check if selection contains two or more solver nodes. This is an error.
    num_solver_nodes = 0
    for item in selection:
        if mz.isSolver([item]):
            num_solver_nodes = num_solver_nodes + 1
    if num_solver_nodes == 0:
        ZIVA_CLIPBOARD_CONTAINS_SOLVER_NODE = False
    elif num_solver_nodes == 1:
        ZIVA_CLIPBOARD_CONTAINS_SOLVER_NODE = True
    else:
        mm.eval('error -n "Selection contains more than one solver node. "')
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
        mm.eval('error -n "Ziva clipboard is empty. Need to cut/copy into it."')
        return

    # We need to do a deepcopy of ziva_clipboard_zbuilder because we want to manipulate
    # it (using string_replace), and not change the original ziva_clipboard_zbuilder object.
    # In this way, we can paste the same clipboard multiple times.

    # Make the deepcopy
    builder = copy.deepcopy(ZIVA_CLIPBOARD_ZBUILDER)

    source_selection = ZIVA_CLIPBOARD_SELECTION
    target_selection = mc.ls(sl=True, l=True)
    num_object_to_paste = min([len(source_selection), len(target_selection)])

    # If nothing is selected when we paste, or the clipboard contains a solver node,
    # we paste without any name substitution.
    # Otherwise, perform name substitution:
    #     source selection 1 is pasted onto target selection 1;
    #     source selection 2 is pasted onto target selection 2; and so on.
    if not (target_selection == [] or ZIVA_CLIPBOARD_CONTAINS_SOLVER_NODE):
        for i in range(0, num_object_to_paste):
            builder.string_replace(source_selection[i].split('|')[-1],
                                   target_selection[i].split('|')[-1])

    # In case there are other solvers in the scene, we need to make sure that all the zBuilder commands
    # go to the solver stored in the clipboard. Otherwise, errors could occur due to solver ambiguity.
    # We resolve this as follows: If such a solver does not exist in the scene (because, say,
    # it has been cut), we first create a solver and name it the same as the solver on the clipboard.
    # Then, we make the solver stored on the clipboard be the default solver. So, all zBuilder commands go to it.
    solver_in_clipboard = ZIVA_CLIPBOARD_ZBUILDER.get_scene_items(
        type_filter='zSolver')[0].solver[:-5]  # remove 'Shape' at the end
    if not mc.objExists(solver_in_clipboard):
        generated_solver = mm.eval('ziva -s;')[1]  # make a new solver
        mc.rename(
            generated_solver,
            solver_in_clipboard)  # rename the solver (this also auto-renames the solver shape node)
    mm.eval('ziva -def ' + solver_in_clipboard + ';')  # make the clipboard solver default

    builder.build()


def rig_update(solvers=None):
    # Updates the Ziva rig in the solver(s).
    # This command can be used if you made geometry modifications and you'd like to re-use a previously
    # built Ziva rig on the modified geometry.
    # If no "solvers" are provided, they are inferred from selection.
    if solvers is None:
        solvers = mm.eval('zQuery -t "zSolver" -l')

    # zQuery gives an error if no solvers though it does not stop script
    # this is to stop script
    if solvers is None:
        raise StandardError("No solver in scene.")

    for solver in solvers:
        solver_transform = mc.listRelatives(solver, p=True, f=True)[0][1:]
        # select the solver, and read the ziva setup from solver into the zBuilder object
        mc.select(solver)
        builder = zva.Ziva()
        builder.retrieve_from_scene()

        # remove existing solver
        remove_solver(solvers=[solver])

        # create an empty solver
        generated_solver = mm.eval('ziva -s;')[1]  # make the output solver
        mc.rename(
            generated_solver,
            solver_transform)  # rename the solver (this also auto-renames the solver shape node)

        mm.eval('ziva -def ' + solver + ';')  # make this solver be default

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
        target_solver = prefix + source_solver  # default target solver

    if not mc.objExists(target_solver):
        generated_solver = mm.eval('ziva -s;')[1]  # make the output solver
        mc.rename(generated_solver,
                  target_solver)  # rename the solver (this also auto-renames the transform node)

    # select the sourceSolver, and read the ziva setup from sourceSolver into the zBuilder object
    mc.select(source_solver)
    builder = zva.Ziva()
    builder.retrieve_from_scene()

    # rename to prefix
    builder.string_replace('^', prefix)
    builder.string_replace(
        '^' + prefix + source_solver,
        target_solver)  # rename the solver stored in the zBuilder to targetSolver

    # we need to clear the stored mobjects.  Without doing this it keeps a pointer to original object
    # and uses that instead of creating a new object.  This makes sure it is a new setup with new nodes.
    builder.break_connection_to_scene()

    # build the transferred solver
    mm.eval('ziva -def ' + target_solver + ';')  # make the target solver be default
    builder.build()


def skincluster_transfer(prefix=""):
    # Transfer the skin clusters for the selected mesh(es) onto their warped counterpart(s),
    # and connect the warped mesh(es) to the warped joint hierarchy.
    # Both geometries must have the same topology. The names of the warped meshes must be prefixed
    # with prefix.
    # This command assumes that both the source mesh(es) and the joint hierarchy driving it via the
    # skin cluster(s), have already been warped, and are prefixed with "prefix" (without the
    # quotes).
    selected_nodes = mc.ls(sl=True)
    if len(selected_nodes) == 0:
        mc.error("Must select at least one mesh.\n")

    if prefix == "":
        mc.error('Must specify a prefix.')

    builder = skn.SkinCluster()
    builder.retrieve_from_scene()
    builder.string_replace('^', prefix)
    builder.build()


def load_rig(file_name, solver_name=None):
    # Load a Ziva rig from a file. Geometry must already be in the scene.
    # If solverName is not provided, the rig is applied to the solver stored in the zBuilder file.
    # If solverName is provided, replace the name of the solver stored in the zBuilder file
    # with a given solverName, and apply the rig to that solver.
    builder = zva.Ziva()
    builder.retrieve_from_file(file_name)
    if solver_name != None:
        # replace the solver name stored in the .zBuilder file with solverName
        solver_name_in_file = builder.get_scene_items(
            type_filter='zSolver')[0].solver[:-5]  # remove 'Shape' at the end
        builder.string_replace(solver_name_in_file, solver_name)
    builder.build()


def save_rig(file_name):
    # Save a Ziva rig to a file.
    # If there is only one solver in the scene, it is saved.
    # If there is multiple solvers, save the first solver in the union
    # of selected solvers and the default solver.
    builder = zva.Ziva()
    builder.retrieve_from_scene()
    builder.write(file_name)


def copy_paste_with_substitution(regular_expression, string_to_substitute_matches_with):
    # Copy/Pastes the Ziva rig of the selected objects, onto non-Ziva-rigged objects
    # whose names are defined using regular expressions.
    # This is useful, for example, for mirroring a Ziva rig: rig one side of the character first,
    # then use this command to automatically "copy" the rig to the other side.
    # Of course, objects must follow a proper naming convention, such as l_humerus, r_humerus, or
    # similar.
    # The specific naming convention is defined via a regular expression (regularExpression),
    # and a string with which to replace any regular expression matches
    # (stringToSubstituteMatchesWith).
    # For example, if regularExpression is "^l_" and stringToSubstituteMatchesWith is "r_", then all
    # instances of geometry that begin with "r_" will be rigged in the same way as the corresponding
    # geometry that begins with "l_".
    # The selected objects should come from exactly one solver.
    # Upon exiting, the command selects a few common Ziva node types (zTissue, zBone, zCloth),
    # for better visual feedback to the user.
    builder = zva.Ziva()
    builder.retrieve_from_scene_selection()
    builder.string_replace(regular_expression, string_to_substitute_matches_with)
    builder.build()

    # Select the new items that have been pasted, for better visual feedback to the user.
    # Look into the zBuilder object and find the meshes associated with a few common Ziva node
    # types:
    displayed_node_types = ['zTissue', 'zBone', 'zCloth']
    # clear selection
    mc.select(cl=True)
    for displayed_node_type in displayed_node_types:
        for item in builder.get_scene_items(type_filter=displayed_node_type):
            # Add each mesh of this type to selection.
            mc.select(item.long_association, add=True)


def next_free_plug_in_array(dst_plug):
    # type: (str) -> str
    """ Use this to work around the fact that zSolver.iGeo (and other attrs)
    have indexMatters=True even though the index doesn't matter. As a result,
    connectAttr(a,b,indexMatter=True) won't work on those attrs. We need to 
    find a specific array element to connect to instead.
    
    This function takes a plug name, and if it's an element of an array,
    sets the index to a free index. Else, it's the identity function.
    
    next_free_plug_in_array('foo.bar[7]') --> 'foo.bar[42]'
    next_free_plug_in_array('foo.bar') --> 'foo.bar'
    """

    array_match = re.search(r"(.*)\[\d+\]$", dst_plug)
    if array_match:
        plug = array_match.group(1)
        indices = mc.getAttr(plug, multiIndices=True)
        new_index = indices[-1] + 1 if indices else 0  # [-1] assumes indices are sorted
        new_dst = '{}[{}]'.format(plug, new_index)
        return new_dst
    return dst_plug


def listConnectionPlugs(node, destination=True, source=True):
    # type: (str, bool, bool) -> List[Tuple[basestring,basestring]]
    """ Get all of the connections with 'node' as a list of pairs of plugs.
    The first plug in each pair is a plug on 'node'. The second plug in each
    pair is a plug the first is connected to. """
    assert isinstance(node, basestring), 'Arguments #1 is not a string'
    assert isinstance(destination, bool), 'Arguments "destination" is not a bool'
    assert isinstance(source, bool), 'Arguments "source" is not a bool'
    plugs = mc.listConnections(node,
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
    Given two solvers. 
    Take everything from the second and put it into the first, then delete the second.
    e.g. merge_two_solvers('zSolver1', 'zSolver2')
    """
    ####################################################################
    # Checking inputs
    assert isinstance(solver_transform1, basestring), 'Arguments #1 is not a string'
    assert isinstance(solver_transform2, basestring), 'Arguments #2 is not a string'
    assert mc.nodeType(
        solver_transform1) == 'zSolverTransform', 'Argument #1 is not a zSolverTransform'
    assert mc.nodeType(
        solver_transform2) == 'zSolverTransform', 'Argument #2 is not a zSolverTransform'
    assert solver_transform1 != solver_transform2, 'The two solvers are not different'

    solver1 = mm.eval('zQuery -t zSolver {}'.format(solver_transform1))[0]
    solver2 = mm.eval('zQuery -t zSolver {}'.format(solver_transform2))[0]
    embedder1 = mm.eval('zQuery -t zEmbedder {}'.format(solver_transform1))[0]
    embedder2 = mm.eval('zQuery -t zEmbedder {}'.format(solver_transform2))[0]

    ####################################################################
    # For speed and to reduce noise, try to disable the solvers
    # TODO: use SolverDisabler to do this 'right'
    try:
        mc.setAttr('{}.enable'.format(solver_transform1), False)
        mc.setAttr('{}.enable'.format(solver_transform2), False)
    except:
        pass

    ####################################################################
    # logger.info('Re-wiring outputs of {} to come from {}'.format(solver2, solver1))
    for src, dst in listConnectionPlugs(solver2, source=False):
        mc.disconnectAttr(src, dst)
        new_src = src.replace(solver2, solver1, 1)
        try:
            mc.connectAttr(new_src, dst)
        except:
            logger.info('Skipped new connection {} {}'.format(src, dst))

    ####################################################################
    # logger.info('Re-wiring inputs of {} to go to {}'.format(solver2, solver1))
    for dst, src in listConnectionPlugs(solver2, destination=False):
        mc.disconnectAttr(src, dst)
        new_dst = dst.replace(solver2, solver1, 1)
        new_dst = next_free_plug_in_array(new_dst)
        try:
            mc.connectAttr(src, new_dst)
        except:
            if not new_dst.endswith('iSolverParams'):  # We _expect_ this plug to fail.
                logger.info('Skipped new connection {} {}'.format(src, new_dst))

    ####################################################################
    # logger.info('Re-wiring outputs of {} to come from {}'.format(solver_transform2, solver_transform1))
    for src, dst in listConnectionPlugs(solver_transform2, source=False):
        mc.disconnectAttr(src, dst)
        new_src = src.replace(solver_transform2, solver_transform1, 1)
        try:
            mc.connectAttr(new_src, dst)
        except:
            logger.info('Skipped new connection {} {}'.format(src, dst))

    ####################################################################
    # logger.info('Adding shapes from {} to {}'.format(embedder2, embedder1))

    # From embedder2, find all of the embedded meshes and which zGeoNode they're deformed by.
    tissue_geo_plugs = mz.none_to_empty(
        mc.listConnections('{}.iGeo'.format(embedder2), plugs=True, source=True, destination=False))
    meshes = mz.none_to_empty(mc.deformer(embedder2, query=True, geometry=True))
    indices = set(mz.none_to_empty(mc.deformer(embedder1, query=True, geometryIndices=True)))

    # Add all of the meshes from embedder2 onto embedder1, and connect up the iGeo to go with it.
    for mesh, geo_plug in zip(meshes, tissue_geo_plugs):
        mc.deformer(embedder2, edit=True, remove=True, geometry=mesh)
        mc.deformer(embedder1, edit=True, before=True, geometry=mesh)  # "-before" for referencing
        # TODO: how do I get the index of a mesh without this mess?
        new_indices = set(mc.deformer(embedder1, query=True, geometryIndices=True))
        new_index = list(new_indices - indices)[0]
        indices = new_indices
        mc.connectAttr(geo_plug, '{}.iGeo[{}]'.format(embedder1, new_index))

    ####################################################################
    # logger.info('Trying to delete stale solver {}'.format(solver_transform2))

    for node in [solver2, solver_transform2, embedder2]:
        # Referened nodes are 'readOnly; and cannot be deleted or renamed - leave them alone.
        if not mc.ls(node, readOnly=True):
            mc.delete(node)

    # TODO: use SolverDisbler to do this 'right'
    try:
        mc.setAttr('{}.enable'.format(solver_transform1), True)
    except:
        pass


def merge_solvers(solver_transforms):
    # type: (List[str]) -> None
    """ 
    Given a list of zSolverTransform nodes, merge them all into the first node.
    e.g. merge_solvers(['zSolver1', 'zSolver2', 'zSolver2'])
    """
    assert isinstance(solver_transforms, list), 'Arguments #1 is not a list'

    if len(solver_transforms) < 2:
        return
    solver1 = solver_transforms[0]
    for solver2 in solver_transforms[1:]:
        merge_two_solvers(solver1, solver2)