import maya.cmds as mc
import maya.mel as mm
from zBuilder.utils import merge_solvers
from vfx_test_case import VfxTestCase


class MergeSolversTestCase(VfxTestCase):
    @classmethod
    def setUpClass(cls):
        pass

    def setUp(self):
        pass

    def test_merge_solvers_will_not_merge_gibberish_arguments(self):
        # Act & Verify
        with self.assertRaises(Exception):
            merge_solvers([1,2,3], 7)

    def test_merge_solvers_will_not_merge_solver_with_itself(self):
        # Setup
        mm.eval('ziva -solver')

        # Act & Verify
        with self.assertRaises(Exception):
            merge_solvers('zSolver1', 'zSolver1')
            
    def test_merge_solvers_will_not_merge_solver_shapes(self):
        # Setup
        mm.eval('ziva -solver')
        mm.eval('ziva -solver')

        # Act & Verify
        with self.assertRaises(Exception):
            merge_solvers('zSolver1Shape', 'zSolver2Shape')

    def test_merge_solvers_can_merge_two_empty_solvers(self):
        # Setup
        mm.eval('ziva -solver')
        solver1 = mc.rename('zSolver1', 'foo_solver')
        mm.eval('ziva -solver')
        solver2 = mc.rename('zSolver1', 'bar_solver')

        # Act
        merge_solvers(solver1, solver2)

        # Verify
        nodes = set(mc.ls())
        self.assertIn(solver1, nodes)
        self.assertNotIn(solver2, nodes)
