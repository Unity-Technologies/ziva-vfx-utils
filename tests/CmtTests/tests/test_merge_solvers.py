import maya.cmds as mc
import maya.mel as mm
from zBuilder.utils import merge_solvers
import vfx_test_case


def make_a_simple_test_scene():
    """ return [solver_transform, a_tissue_mesh]"""
    solver = mm.eval('ziva -solver')[1]
    solver = mc.rename(solver, 'bob_solver')  # to make sure we're not depending on names
    bone1 = mc.polySphere(name='bone1_1', sx=4, sy=4)[0]
    bone2 = mc.polySphere(name='bone2_1', sx=4, sy=4)[0]
    tissue2 = mc.polySphere(name='tissue1_1', sx=4, sy=4)[0]
    tissue1 = mc.polySphere(name='tissue2_1', sx=4, sy=3)[0]
    embedd1 = mc.polySphere(name='embedded1_1', sx=3, sy=2)[0]
    mm.eval('ziva -b {} {} {}'.format(solver, bone1, bone2))
    mm.eval('ziva -t {} {} {}'.format(solver, tissue1, tissue2))
    mm.eval('ziva -e {} {} {}'.format(solver, tissue1, embedd1))
    mm.eval('ziva -a {} {} {}'.format(solver, tissue1, bone1))
    fiber = mm.eval('ziva -f {} {}'.format(solver, tissue1))[0]
    mc.setAttr('{}.excitation'.format(fiber), 0.7)
    return [solver, tissue1]


def get_simulated_positions():
    """ Simulate a few frames, then return the position of all vertices """
    solvers = mc.ls(type='zSolver')
    end_frame = 3
    for i in range(1, end_frame + 1):
        mc.currentTime(i)
        for s in solvers:
            # Pull on the solver each frame, to make sure it computes.
            mc.getAttr(s + '.oSolved', silent=True)
    return vfx_test_case.get_all_mesh_vertex_positions()


class MergeSolversTestCase(vfx_test_case.VfxTestCase):
    @classmethod
    def setUpClass(cls):
        pass

    def setUp(self):
        pass

    def test_merge_solvers_will_not_merge_gibberish_arguments(self):
        # Act & Verify
        with self.assertRaises(Exception):
            merge_solvers([1, 2, 3], 7)

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
        solver1 = mc.rename(mm.eval('ziva -solver')[1], 'foo_solver')
        solver2 = mc.rename(mm.eval('ziva -solver')[1], 'bar_solver')

        # Act
        merge_solvers(solver1, solver2)

        # Verify
        nodes = set(mc.ls())
        self.assertIn(solver1, nodes)
        self.assertNotIn(solver2, nodes)

    def test_merge_solvers_can_merge_two_simple_solvers(self):
        # Setup
        solver1, _ = make_a_simple_test_scene()
        solver2, _ = make_a_simple_test_scene()

        # Act
        merge_solvers(solver1, solver2)

        # Verify
        nodes = set(mc.ls())
        self.assertIn(solver1, nodes)
        self.assertNotIn(solver2, nodes)
        self.assertEqual(1, len(mc.ls(type='zEmbedder')))
        self.assertEqual(1, len(mc.ls(type='zSolver')))
        self.assertEqual(1, len(mc.ls(type='zSolverTransform')))

    def test_tissues_in_merged_solvers_can_be_attached_together(self):
        # Setup
        solver1, tissue1 = make_a_simple_test_scene()
        solver2, tissue2 = make_a_simple_test_scene()
        attachments_orig = set(mc.ls(type='zAttachment'))

        # Act
        merge_solvers(solver1, solver2)
        attachment_new = mm.eval('ziva -a {} {} {}'.format(solver1, tissue1, tissue2))[0]

        # Verify
        attachments_expected = attachments_orig.union({attachment_new})
        attachments_new = set(mc.ls(type='zAttachment'))
        self.assertEqual(attachments_expected, attachments_new)

    def test_merged_solvers_sim_result_matches_original_result(self):
        # Setup
        solver1, _ = make_a_simple_test_scene()
        solver2, _ = make_a_simple_test_scene()
        old_positions = get_simulated_positions()

        # Act
        merge_solvers(solver1, solver2)
        new_positions = get_simulated_positions()

        # Verify
        self.assertAllApproxEqual(old_positions, new_positions)
