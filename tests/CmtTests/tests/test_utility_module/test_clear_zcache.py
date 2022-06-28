from maya import cmds
from vfx_test_case import VfxTestCase
from utility.scriptCommands.zCacheCommands import clear_zcache


def setup_cache_env(N=1, add_cache=True):
    """ Create N node pair, with zSolver, zCache, cube tissue.
    Return the zSolver, zCache node list respectively.
    """
    solver_nodes = []
    cache_nodes = []
    for i in range(N):
        solver_node, _, _ = cmds.ziva(s=True)
        solver_nodes.append(solver_node)
        if add_cache:
            _, cache_node = cmds.ziva(solver_node, acn=True)
            cache_nodes.append(cache_node)
        # Create a tissue to make simulation run, so as to fill the cache
        tissue_name = "Tissue{}".format(i + 1)
        cmds.polyCube(name=tissue_name)
        cmds.ziva(tissue_name, t=True)

    return solver_nodes, cache_nodes


def run_sim(solver_nodes):
    for i in range(3):
        cmds.currentTime(i + 1)
        for solver in solver_nodes:
            # Pull on the solver to make sure it computes the frame
            cmds.getAttr("{}.oSolved".format(solver), silent=True)


def get_cache_range(cache_node):
    return cmds.getAttr("{}.startFrame".format(cache_node)), cmds.getAttr(
        "{}.endFrame".format(cache_node))


class ClearZCacheTestCase(VfxTestCase):

    FILLED_CACHE_RANGE = (2.0, 3.0)  # We only sim [1, 3] range, so only 2 frames are cached
    EMPTY_CACHE_RANGE = (0.0, -1.0)

    def test_clear_zcache_with_no_cache_scene(self):
        """ Clear zCache command with no cache in the scene should do nothing,
        and cause no issue.
        """
        # Setup
        solver_nodes, _ = setup_cache_env(1, False)
        run_sim(solver_nodes)

        # Action
        clear_zcache()

    # one cache tests
    def test_clear_one_zcache_with_no_selection(self):
        # Setup
        solver_nodes, cache_nodes = setup_cache_env()
        run_sim(solver_nodes)
        # Verify: cache is filled
        self.assertEqual(len(cache_nodes), 1)
        self.assertEqual(get_cache_range(cache_nodes[0]), ClearZCacheTestCase.FILLED_CACHE_RANGE)

        # Action
        cmds.select(clear=True)
        clear_zcache()

        # Verify: cache is cleared
        self.assertEqual(get_cache_range(cache_nodes[0]), ClearZCacheTestCase.EMPTY_CACHE_RANGE)

    def test_clear_one_zcache_with_solver_selected(self):
        # Setup
        solver_nodes, cache_nodes = setup_cache_env()
        run_sim(solver_nodes)
        # Verify: cache is filled
        self.assertEqual(len(cache_nodes), 1)
        self.assertEqual(get_cache_range(cache_nodes[0]), ClearZCacheTestCase.FILLED_CACHE_RANGE)

        # Action
        cmds.select(clear=True)
        cmds.select(solver_nodes[0])
        clear_zcache()

        # Verify: cache is cleared
        self.assertEqual(get_cache_range(cache_nodes[0]), ClearZCacheTestCase.EMPTY_CACHE_RANGE)

    def test_clear_one_zcache_with_solverTM_selected(self):
        """ Select solverTM is same as select the solver node
        """
        # Setup
        solver_nodes, cache_nodes = setup_cache_env()
        run_sim(solver_nodes)
        # Verify: cache is filled
        self.assertEqual(len(cache_nodes), 1)
        self.assertEqual(get_cache_range(cache_nodes[0]), ClearZCacheTestCase.FILLED_CACHE_RANGE)

        # Action
        solverTM = cmds.listRelatives(solver_nodes[0], parent=True)
        cmds.select(clear=True)
        cmds.select(solverTM)
        clear_zcache()

        # Verify: cache is cleared
        self.assertEqual(get_cache_range(cache_nodes[0]), ClearZCacheTestCase.EMPTY_CACHE_RANGE)

    def test_clear_one_zcache_with_cache_selected(self):
        # Setup
        solver_nodes, cache_nodes = setup_cache_env()
        run_sim(solver_nodes)
        # Verify: cache is filled
        self.assertEqual(len(cache_nodes), 1)
        self.assertEqual(get_cache_range(cache_nodes[0]), ClearZCacheTestCase.FILLED_CACHE_RANGE)

        # Action
        cmds.select(clear=True)
        cmds.select(cache_nodes[0])
        clear_zcache()

        # Verify: cache is cleared
        self.assertEqual(get_cache_range(cache_nodes[0]), ClearZCacheTestCase.EMPTY_CACHE_RANGE)

    # two cache tests
    def test_clear_two_zcache_with_no_selection(self):
        # Setup
        solver_nodes, cache_nodes = setup_cache_env(2)
        run_sim(solver_nodes)
        # Verify: cache is filled
        self.assertEqual(len(cache_nodes), 2)
        for cache in cache_nodes:
            self.assertEqual(get_cache_range(cache), ClearZCacheTestCase.FILLED_CACHE_RANGE)

        # Action
        cmds.select(clear=True)
        clear_zcache()

        # Verify: caches are cleared
        for cache in cache_nodes:
            self.assertEqual(get_cache_range(cache), ClearZCacheTestCase.EMPTY_CACHE_RANGE)

    def test_clear_two_zcache_with_both_solver_selected(self):
        # Setup
        solver_nodes, cache_nodes = setup_cache_env(2)
        run_sim(solver_nodes)
        # Verify: cache is filled
        self.assertEqual(len(cache_nodes), 2)
        for cache in cache_nodes:
            self.assertEqual(get_cache_range(cache), ClearZCacheTestCase.FILLED_CACHE_RANGE)

        # Action
        cmds.select(clear=True)
        cmds.select(solver_nodes)
        clear_zcache()

        # Verify: caches are cleared
        for cache in cache_nodes:
            self.assertEqual(get_cache_range(cache), ClearZCacheTestCase.EMPTY_CACHE_RANGE)

    def test_clear_two_zcache_with_one_solver_selected(self):
        # Setup
        solver_nodes, cache_nodes = setup_cache_env(2)
        run_sim(solver_nodes)
        # Verify: cache is filled
        self.assertEqual(len(cache_nodes), 2)
        for cache in cache_nodes:
            self.assertEqual(get_cache_range(cache), ClearZCacheTestCase.FILLED_CACHE_RANGE)

        # Action
        cmds.select(clear=True)
        cmds.select(solver_nodes[0])
        clear_zcache()

        # Verify: selected cache is cleared
        self.assertEqual(get_cache_range(cache_nodes[0]), ClearZCacheTestCase.EMPTY_CACHE_RANGE)
        self.assertEqual(get_cache_range(cache_nodes[1]), ClearZCacheTestCase.FILLED_CACHE_RANGE)

    def test_clear_two_zcache_with_one_tissue_selected(self):
        """ Test the less frequent case: select a zTissue node and try clearing the cache
        """
        # Setup
        solver_nodes, cache_nodes = setup_cache_env(2)
        run_sim(solver_nodes)
        # Verify: cache is filled
        self.assertEqual(len(cache_nodes), 2)
        for cache in cache_nodes:
            self.assertEqual(get_cache_range(cache), ClearZCacheTestCase.FILLED_CACHE_RANGE)

        # Action
        cmds.select(clear=True)
        cmds.select("zTissue1")  # The zTissue1 correspond to cache_nodes[0]
        clear_zcache()

        # Verify: selected tissue node's cache is cleared
        self.assertEqual(get_cache_range(cache_nodes[0]), ClearZCacheTestCase.EMPTY_CACHE_RANGE)
        self.assertEqual(get_cache_range(cache_nodes[1]), ClearZCacheTestCase.FILLED_CACHE_RANGE)
