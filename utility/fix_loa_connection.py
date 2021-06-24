from maya.api.OpenMaya import MTypeId, MFn, MItDependencyNodes, MFnDependencyNode
import maya.mel as mel

LINE_OF_ACTION_TYPEID = MTypeId(0x123ba7)


def run():
    '''
    This function search all zLineOfAction node(s) in the scene.
    It checks their iSolverParams plug is connected.
    If not, fix the connection by search for their corresponding zSolverTransform node's oSolverParams plug.
    The fix always works as each zLineOfAction node should have only one corresponding zSolverTransform node.
    '''
    # Collect zLineOfAction node(s)
    loa_nodes = []
    it = MItDependencyNodes(MFn.kPluginDependNode)
    while not it.isDone():
        obj = it.thisNode()
        if obj.isNull():
            continue
        dep_node = MFnDependencyNode(obj)
        if dep_node.typeId == LINE_OF_ACTION_TYPEID:
            loa_nodes.append(dep_node)
        it.next()
    print('Found {} Line of Action node{}.'.format(len(loa_nodes),
                                                   's' if len(loa_nodes) > 1 else ''))

    patched_loa_node_num = 0
    for loa in loa_nodes:
        try:
            # Check if zLineOfAction.iSolverParams is connected
            loa_isolver_param_plug = loa.findPlug('iSolverParams', False)
            solvertm_osolver_param_plug = loa_isolver_param_plug.connectedTo(True, False)
            # Fix the zLineOfAction node(s) connection
            if len(solvertm_osolver_param_plug) == 0:
                # Get zFiber node
                loa_oloadata_plug = loa.findPlug('oLineOfActionData', False)
                fiber_iloadata_plug = loa_oloadata_plug.connectedTo(False, True)
                if len(fiber_iloadata_plug) == 0:
                    raise RuntimeError(
                        'Failure getting zFiber node connected to zLineOfAction node oLineOfActionData plug.'
                    )
                fiber = MFnDependencyNode(fiber_iloadata_plug[0].node())
                # Get zSolver node
                fiber_omuscle_plug = fiber.findPlug('oMuscle', False)
                solver_isolver_param_plug = fiber_omuscle_plug.connectedTo(False, True)
                if len(solver_isolver_param_plug) == 0:
                    raise RuntimeError(
                        'Failure getting zSolver node connected to zFiber node oMuscle plug.')
                solver_node = MFnDependencyNode(solver_isolver_param_plug[0].node())
                # Get zSolver Transform node
                solver_isolver_param_plug = solver_node.findPlug('iSolverParams', False)
                solvertm_osolver_param_plug = solver_isolver_param_plug.connectedTo(True, False)
                if len(solvertm_osolver_param_plug) == 0:
                    raise RuntimeError(
                        'Failure getting zSolverTransform node connected to zSolver node iSolverParams plug.'
                    )
                solvertm = MFnDependencyNode(solvertm_osolver_param_plug[0].node())
                command = "connectAttr {}.oSolverParams {}.iSolverParams;".format(
                    solvertm.name(), loa.name())
                mel.eval(command)
                patched_loa_node_num += 1
        except RuntimeError as e:
            print("{} node fail to patch connection to zSolverTransform.oSolverParams plug.".format(
                loa.name()))
            print("Error message: {}".format(e))
            continue
    print("{} Line of Action node{} fixed.".format(patched_loa_node_num,
                                                   's' if patched_loa_node_num > 1 else ''))
