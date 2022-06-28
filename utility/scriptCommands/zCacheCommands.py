from maya import cmds


def clear_zcache():
    """ Clear zCache on all selected zSolver nodes.
    If no zSolver node is selected, clear all zSolver nodes in the scene.
    """
    # The zQuery command gets selected zSolver nodes,
    # or all zSolver nodes if selection list is empty.
    zsolver_nodes = cmds.zQuery(type="zSolver")
    if not zsolver_nodes:
        return

    for solver_node in zsolver_nodes:
        zcache_node = cmds.zQuery(solver_node, type="zCache")
        if zcache_node:
            cmds.zCache(solver_node, c=True)
