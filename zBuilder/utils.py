import logging
import copy as copy

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


# Safely remove the given Ziva nodes without worrying about breaking the scene.
# A solver node can be specified either by its transform node or shape node (or both);
# in any case, both are removed.
def zRemove(nodes):
    # The following node types are safe to remove directly.
    safe_to_delete = ['zFiber', 'zAttachment']

    for node in nodes:
        # Check if node still exists.
        if not mc.objExists(node):
            continue

        # Check if node is a solver, and if so, remove it first.
        if mz.isSolver([node]):
            zRemoveSolver(solvers=[node])

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


# Removes the entire Ziva rig from the solver(s).
# If no solver is provided, it infers them from selection.
# If no solver is provided, and nothing is selected, it returns an error.
# Otherwise, the provided solvers are removed. Solvers can be provided either
# as a solver transform node, or solver shape node.
# The command also deletes the solver nodes themselves.
def zRemoveSolver(solvers=None, askForConfirmation=False):

    if solvers == None:
        # If selection is empty, do not select any solvers. Therefore, an error message is printed.
        numSelectedObjects = len(mc.ls(selection=True))
        if numSelectedObjects > 0:
            solvers = mm.eval('zQuery -t "zSolver" -l')
        else:
            mm.eval('error -n "Nothing is selected"')
            return
    if solvers == None:
        mm.eval('error -n "No solver selected"')
        return

    # Convert any solver transform nodes to solver shape nodes.
    solvers = mm.eval('zQuery -t "zSolver" -l ' + ' '.join(solvers))

    message = 'This command will remove the solver(s): '
    for solver in solvers:
        shortSolverName = mc.ls(solver)[0][:-5]  # remove 'Shape' at the end
        message += shortSolverName + ', '
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
            solverOfThisItem = mz.get_zSolver(item)[0]
            if solverOfThisItem in solvers:
                to_erase.append(item)
            # unlock the transform attributes
            if (node == 'zTissue') or (node == 'zCloth'):
                mayaMesh = mm.eval('zQuery -m ' + item)[0]
                attrs = ['tx', 'ty', 'tz', 'rx', 'ry', 'rz', 'sx', 'sy', 'sz']
                for attr in attrs:
                    mm.eval('setAttr -lock 0 ' + mayaMesh + '.' + attr)

    mm.eval('select -cl;')  # needed to avoid Maya error messages
    if len(to_erase) > 0:
        mc.delete(to_erase)


# Removes all Ziva solvers from the scene, including all Ziva rigs.
# All Ziva nodes are removed from the Maya scene.
# The command also deletes the solvers themselves.
def zRemoveAllSolvers(askForConfirmation=False):

    if askForConfirmation:
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


# Cut or copy the Ziva rig available on currently selected objects into the Ziva clipboard.
# Selection cannot be empty; otherwise an error is reported.
# Selection can contain zero or one solver node; otherwise an error is reported
# (it does not matter if the solver node is a solver transform node, or solver shape node).
# The selected objects must all come from exactly one solver; otherwise an error is reported.
# If cut is True, the Ziva rig is removed from the selection after being copied (i.e., perform a cut).
def zRigCutCopy(cut=False):
    global ZIVA_CLIPBOARD_ZBUILDER
    global ZIVA_CLIPBOARD_SELECTION
    global ZIVA_CLIPBOARD_CONTAINS_SOLVER_NODE
    selection = mc.ls(sl=True)
    if len(selection) == 0:
        mm.eval('error -n "Selection is empty. Cut/copy needs a selection to operate on."')
        return

    # Enforce that the selected objects come from exactly one solver.
    selectedSolvers = mm.eval('zQuery -t "zSolver" -l')
    if selectedSolvers == None:
        mm.eval('error -n "Selected objects are not connected to a solver."')
        return
    if len(selectedSolvers) >= 2:
        mm.eval(
            'error -n "Selected objects come from two or more solvers. Inputs to cut/copy must come from only one solver."'
        )
        return

    # Record if selection contains a solver node.
    # We'll need this information when pasting.
    # Also check if selection contains two or more solver nodes. This is an error.
    numSolverNodes = 0
    for item in selection:
        if mz.isSolver([item]):
            numSolverNodes = numSolverNodes + 1
    if numSolverNodes == 0:
        ZIVA_CLIPBOARD_CONTAINS_SOLVER_NODE = False
    elif numSolverNodes == 1:
        ZIVA_CLIPBOARD_CONTAINS_SOLVER_NODE = True
    else:
        mm.eval('error -n "Selection contains more than one solver node. "')
        return

    ZIVA_CLIPBOARD_ZBUILDER = zva.Ziva()
    ZIVA_CLIPBOARD_ZBUILDER.retrieve_from_scene_selection()
    ZIVA_CLIPBOARD_SELECTION = selection

    if cut:
        zRemove(selection)


# Cut Ziva rig. See zRigCutCopy for instructions.
def zRigCut():
    zRigCutCopy(cut=True)


# Copy Ziva rig. See zRigCutCopy for instructions.
def zRigCopy():
    zRigCutCopy(cut=False)


# Paste the Ziva rig from the Ziva clipboard onto scene geometry.
# If nothing is selected, or the Ziva clipboard contains an explicit solver node,
# the Ziva rig is applied to scene geometry that is named inside the Ziva clipboard.
# If something is selected, then:
#   source selection 1 is pasted onto target selection 1;
#   source selection 2 is pasted onto target selection 2; and so on.
# The pasted Ziva rig is added to the solver that was used for the last cut/copy operation.
# If such a solver does not exist any more in the Maya scene (because, say, it has been cut),
# it is created.
def zRigPaste():
    global ZIVA_CLIPBOARD_ZBUILDER
    global ZIVA_CLIPBOARD_SELECTION
    if ZIVA_CLIPBOARD_ZBUILDER == None:
        mm.eval('error -n "Ziva clipboard is empty. Need to cut/copy into it."')
        return

    # We need to do a deepcopy of ziva_clipboard_zbuilder because we want to manipulate
    # it (using string_replace), and not change the original ziva_clipboard_zbuilder object.
    # In this way, we can paste the same clipboard multiple times.
    # In order to deepcopy, we need to first remove all mobject references, using mobject_reset.
    for item in ZIVA_CLIPBOARD_ZBUILDER.get_scene_items():
        if hasattr(item, 'mobject_reset'):
            item.mobject_reset()
    # Make the deepcopy.
    builder = copy.deepcopy(ZIVA_CLIPBOARD_ZBUILDER)

    source_selection = ZIVA_CLIPBOARD_SELECTION
    target_selection = mc.ls(sl=True, l=True)
    numObjectToPaste = min([len(source_selection), len(target_selection)])

    # If nothing is selected when we paste, or the clipboard contains a solver node,
    # we paste without any name substitution.
    # Otherwise, perform name substitution:
    #     source selection 1 is pasted onto target selection 1;
    #     source selection 2 is pasted onto target selection 2; and so on.
    if not (target_selection == [] or ZIVA_CLIPBOARD_CONTAINS_SOLVER_NODE):
        for i in range(0, numObjectToPaste):
            builder.string_replace(source_selection[i].split('|')[-1],
                                   target_selection[i].split('|')[-1])

    # In case there are other solvers in the scene, we need to make sure that all the zBuilder commands
    # go to the solver stored in the clipboard. Otherwise, errors could occur due to solver ambiguity.
    # We resolve this as follows: If such a solver does not exist in the scene (because, say,
    # it has been cut), we first create a solver and name it the same as the solver on the clipboard.
    # Then, we make the solver stored on the clipboard be the default solver. So, all zBuilder commands go to it.
    solverInClipboard = ZIVA_CLIPBOARD_ZBUILDER.get_scene_items(
        type_filter='zSolver')[0].solver[:-5]  # remove 'Shape' at the end
    if not mc.objExists(solverInClipboard):
        generatedSolver = mm.eval('ziva -s;')[1]  # make a new solver
        mc.rename(
            generatedSolver,
            solverInClipboard)  # rename the solver (this also auto-renames the solver shape node)
    mm.eval('ziva -def ' + solverInClipboard + ';')  # make the clipboard solver default

    builder.reset_solvers()
    builder.build()


# Updates the Ziva rig in the solver(s).
# This command can be used if you made geometry modifications and you'd like to re-use a previously
# built Ziva rig on the modified geometry.
# If no "solvers" are provided, they are inferred from selection.
def zRigUpdate(solvers=None):
    if solvers == None:
        solvers = mm.eval('zQuery -t "zSolver" -l')
    if solvers == None:
        mm.eval('error -n "No solver selected"')
        return

    for solver in solvers:
        solverTransform = mc.listRelatives(solver, p=True, f=True)[0][1:]
        # select the solver, and read the ziva setup from solver into the zBuilder object
        mc.select(solver)
        builder = zva.Ziva()
        builder.retrieve_from_scene()

        # remove existing solver
        zRemoveSolver(solvers=[solver])

        # create an empty solver
        generatedSolver = mm.eval('ziva -s;')[1]  # make the output solver
        mc.rename(
            generatedSolver,
            solverTransform)  # rename the solver (this also auto-renames the solver shape node)
        mm.eval('ziva -def ' + solver + ';')  # make this solver be default

        # re-build the solver
        builder.reset_solvers()
        builder.build()


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
def zRigTransfer(sourceSolver, prefix, targetSolver=""):
    if (targetSolver == ""):
        targetSolver = prefix + sourceSolver  # default target solver

    if (not mc.objExists(targetSolver)):
        generatedSolver = mm.eval('ziva -s;')[1]  # make the output solver
        mc.rename(generatedSolver,
                  targetSolver)  # rename the solver (this also auto-renames the transform node)

    # select the sourceSolver, and read the ziva setup from sourceSolver into the zBuilder object
    mc.select(sourceSolver)
    builder = zva.Ziva()
    builder.retrieve_from_scene()

    # rename to prefix
    builder.string_replace('^', prefix)
    builder.string_replace('^' + prefix + sourceSolver,
                           targetSolver)  # rename the solver stored in the zBuilder to targetSolver

    # build the transferred solver
    mm.eval('ziva -def ' + targetSolver + ';')  # make the target solver be default
    builder.reset_solvers()
    builder.build()


# Transfer the skin clusters for the selected mesh(es) onto their warped counterpart(s),
# and connect the warped mesh(es) to the warped joint hierarchy.
# Both geometries must have the same topology. The names of the warped meshes must be prefixed with prefix.
# This command assumes that both the source mesh(es) and the joint hierarchy driving it via the
# skin cluster(s), have already been warped, and are prefixed with "prefix" (without the quotes).
def zSkinClusterTransfer(prefix=""):
    selectedNodes = mc.ls(sl=True)
    if len(selectedNodes) == 0:
        mc.error("Must select at least one mesh.\n")

    if prefix == "":
        mc.error('Must specify a prefix.')

    builder = skn.SkinCluster()
    builder.retrieve_from_scene()
    builder.string_replace('^', prefix)
    builder.build()


# Load a Ziva rig from a file. Geometry must already be in the scene.
# If solverName is not provided, the rig is applied to the solver stored in the zBuilder file.
# If solverName is provided, replace the name of the solver stored in the zBuilder file
# with a given solverName, and apply the rig to that solver.
def zLoadRig(zBuilderFilename, solverName=None):
    builder = zva.Ziva()
    builder.retrieve_from_file(zBuilderFilename)
    if solverName != None:
        # replace the solver name stored in the .zBuilder file with solverName
        solverNameInFile = builder.get_scene_items(
            type_filter='zSolver')[0].solver[:-5]  # remove 'Shape' at the end
        builder.string_replace(solverNameInFile, solverName)
    builder.build()


# Save a Ziva rig to a file.
# If there is only one solver in the scene, it is saved.
# If there is multiple solvers, save the first solver in the union
# of selected solvers and the default solver.
def zSaveRig(zBuilderFilename):
    builder = zva.Ziva()
    builder.retrieve_from_scene()
    builder.write(zBuilderFilename)


# Copy/Pastes the Ziva rig of the selected objects, onto non-Ziva-rigged objects
# whose names are defined using regular expressions.
# This is useful, for example, for mirroring a Ziva rig: rig one side of the character first,
# then use this command to automatically "copy" the rig to the other side.
# Of course, objects must follow a proper naming convention, such as l_humerus, r_humerus, or similar.
# The specific naming convention is defined via a regular expression (regularExpression),
# and a string with which to replace any regular expression matches (stringToSubstituteMatchesWith).
# For example, if regularExpression is "^l_" and stringToSubstituteMatchesWith is "r_", then all
# instances of geometry that begin with "r_" will be rigged in the same way as the corresponding
# geometry that begins with "l_".
# The selected objects should come from exactly one solver.
# Upon exiting, the command selects a few common Ziva node types (zTissue, zBone, zCloth),
# for better visual feedback to the user.
def zRigCopyPasteWithNameSubstitution(regularExpression, stringToSubstituteMatchesWith):
    builder = zva.Ziva()
    builder.retrieve_from_scene_selection()
    builder.string_replace(regularExpression, stringToSubstituteMatchesWith)
    builder.build()

    # Select the new items that have been pasted, for better visual feedback to the user.
    # Look into the zBuilder object and find the meshes associated with a few common Ziva node types:
    displayedNodeTypes = ['zTissue', 'zBone', 'zCloth']
    # clear selection
    mc.select(cl=True)
    for displayedNodeType in displayedNodeTypes:
        for item in builder.get_scene_items(type_filter=displayedNodeType):
            # Add each mesh of this type to selection.
            mc.select(item.long_association, add=True)
