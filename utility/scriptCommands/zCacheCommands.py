import logging

from maya import cmds

logger = logging.getLogger(__name__)

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

def save_zcache():
    """ Save zCache on the selected zSolver node.
    """
    transform_nodes = cmds.zQuery(type="zCacheTransform")

    if not transform_nodes:
        logger.error("No cache node found. Does one exist on the solver?")
        return

    if len(transform_nodes) > 1:
        logger.error("Multiple cache nodes found. Please select the solver you want to save a cache for.")
        return

    multipleFilters = "zCache (*.zCache);;All Files (*.*)"
    result = cmds.fileDialog2(fileFilter=multipleFilters,selectFileFilter="zCache", dialogStyle=2, cap="Save Cache", fm=0)
    if not result:
        logger.error("No cache file found.")
        return
    cmds.zCache(save=result[0])

def load_zcache():
    zcache_nodes = cmds.zQuery(type="zCacheTransform")
    if not zcache_nodes:
        # Create the cache node.
        cmds.ziva(acn=True)
        zcache_nodes = cmds.zQuery(type="zCacheTransform")

        if not zcache_nodes:
            logger.error("There is no cache node in the file and trying to create one also failed. Create a cache node manually.")
            return
        logger.info("Created a cache node to support loading the cache, as one did not exist in the scene.\n")

    if len(zcache_nodes) > 1:
        logger.error("Multiple cache nodes found. Please select the solver you want to load a cache for.")
        return

    multipleFilters = "zCache (*.zCache);;All Files (*.*)"
    result = cmds.fileDialog2(fileFilter=multipleFilters,selectFileFilter="zCache", dialogStyle=2, cap="Load Cache", fm=1)
    if not result:
        logger.error("No cache file selected!")
        return
    cmds.zCache(load=result[0])
