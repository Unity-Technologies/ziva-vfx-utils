from maya import cmds
from vfx_test_case import VfxTestCase, get_all_mesh_vertex_positions
from zBuilder.commands import merge_two_solvers, merge_solvers


def make_a_simple_test_scene():
    """ return [solver_transform, a_tissue_mesh]"""
    solver = cmds.ziva(solver=True)[1]
    solver = cmds.rename(solver, 'bob_solver')  # to make sure we're not depending on names
    bone1 = cmds.polyCube(name='bone1_1', sx=1, sy=2, sz=1)[0]
    tissue1 = cmds.polyCube(name='tissue1_1', sx=1, sy=3, sz=1)[0]
    cmds.ziva(solver, bone1, b=True)
    cmds.ziva(solver, tissue1, t=True)
    cmds.ziva(solver, tissue1, bone1, a=True)
    fiber = cmds.ziva(solver, tissue1, f=True)[0]
    cmds.setAttr('{}.excitation'.format(fiber), 0.7)
    return [solver, tissue1]


def make_another_simple_test_scene():
    """ return [solver_transform, a_tissue_mesh]"""
    solver = cmds.ziva(solver=True)[1]
    solver = cmds.rename(solver, 'bob_solver')  # to make sure we're not depending on names
    bone1 = cmds.polySphere(name='bone1_1', sx=4, sy=4)[0]
    bone2 = cmds.polySphere(name='bone2_1', sx=4, sy=4)[0]
    tissue1 = cmds.polySphere(name='tissue1_1', sx=4, sy=4)[0]
    tissue2 = cmds.polySphere(name='tissue2_1', sx=4, sy=3)[0]
    embedd1 = cmds.polySphere(name='embedded1_1', sx=3, sy=2)[0]
    cmds.ziva(solver, bone1, bone2, b=True)
    cmds.ziva(solver, tissue1, tissue2, t=True)
    cmds.ziva(solver, tissue1, embedd1, e=True)
    cmds.ziva(solver, tissue1, bone1, a=True)
    fiber = cmds.ziva(solver, tissue1, f=True)[0]
    cmds.setAttr('{}.excitation'.format(fiber), 0.7)
    return [solver, tissue1]


def make_scene_with_referenced_and_typical_solver():
    make_another_simple_test_scene()  # Make a simple scene and save it to a file.
    cmds.file(rename='tempfile')
    filepath = cmds.file(force=True, save=True)

    cmds.file(force=True, new=True)  # Into a new file, make a new solver and reference one in.
    make_a_simple_test_scene()
    cmds.file(filepath, r=True, namespace='ns1')


def get_simulated_positions():
    """ Simulate a few frames, then return the position of all vertices """
    solvers = cmds.ls(type='zSolver')
    end_frame = 3
    for i in range(1, end_frame + 1):
        cmds.currentTime(i)
        for s in solvers:
            # Pull on the solver each frame, to make sure it computes.
            cmds.getAttr(s + '.oSolved', silent=True)
    return get_all_mesh_vertex_positions()


class MergeSolversTestCase(VfxTestCase):

    def test_merge_solvers_will_not_merge_gibberish_arguments(self):
        # Act & Verify
        with self.assertRaises(Exception):
            merge_two_solvers([1, 2, 3], 7)

    def test_merge_solvers_will_not_merge_solver_with_itself(self):
        # Setup
        cmds.ziva(solver=True)

        # Act & Verify
        with self.assertRaises(Exception):
            merge_two_solvers('zSolver1', 'zSolver1')

    def test_merge_solvers_will_not_merge_solver_shapes(self):
        # Setup
        cmds.ziva(solver=True)
        cmds.ziva(solver=True)

        # Act & Verify
        with self.assertRaises(Exception):
            merge_two_solvers('zSolver1Shape', 'zSolver2Shape')

    def test_merge_solvers_can_merge_two_empty_solvers(self):
        # Setup
        solver1 = cmds.rename(cmds.ziva(solver=True)[1], 'foo_solver')
        solver2 = cmds.rename(cmds.ziva(solver=True)[1], 'bar_solver')

        # Act
        merge_two_solvers(solver1, solver2)

        # Verify
        nodes = set(cmds.ls())
        self.assertIn(solver1, nodes)
        self.assertNotIn(solver2, nodes)

    def test_merge_solvers_can_merge_two_simple_solvers(self):
        # Setup
        solver1, _ = make_a_simple_test_scene()
        solver2, _ = make_another_simple_test_scene()

        # Act
        merge_two_solvers(solver1, solver2)

        # Verify
        nodes = set(cmds.ls())
        self.assertIn(solver1, nodes)
        self.assertNotIn(solver2, nodes)
        self.assertEqual(1, len(cmds.ls(type='zEmbedder')))
        self.assertEqual(1, len(cmds.ls(type='zSolver')))
        self.assertEqual(1, len(cmds.ls(type='zSolverTransform')))

    def test_tissues_in_merged_solvers_can_be_attached_together(self):
        # Setup
        solver1, tissue1 = make_a_simple_test_scene()
        solver2, tissue2 = make_another_simple_test_scene()
        attachments_orig = set(cmds.ls(type='zAttachment'))

        # Act
        merge_two_solvers(solver1, solver2)
        attachment_new = cmds.ziva(solver1, tissue1, tissue2, a=True)[0]

        # Verify
        attachments_expected = attachments_orig.union({attachment_new})
        attachments_new = set(cmds.ls(type='zAttachment'))
        self.assertEqual(attachments_expected, attachments_new)

    def test_merged_solvers_sim_result_matches_original_result(self):
        # Setup
        solver1, _ = make_a_simple_test_scene()
        solver2, _ = make_another_simple_test_scene()
        old_positions = get_simulated_positions()

        # Act
        merge_two_solvers(solver1, solver2)
        new_positions = get_simulated_positions()

        # Verify
        self.assertAllApproxEqual(old_positions, new_positions, 1e-4)

    def test_merge_referenced_solvers(self):
        # Setup
        make_another_simple_test_scene()  # Make a simple scene and save it to a file.
        cmds.file(rename='tempfile')
        filepath = cmds.file(force=True, save=True)
        cmds.file(force=True, new=True)
        cmds.file(filepath, r=True, namespace='ns1')  # Into a new file, reference it twice,
        cmds.file(filepath, r=True, namespace='ns2')  # so there are two solvers.
        solvers = cmds.ls(type='zSolverTransform')
        old_meshes = cmds.ls(dag=True, type='mesh', noIntermediate=True)

        # Act
        merge_two_solvers(solvers[0], solvers[1])

        # Verify
        self.assertIn(solvers[0], cmds.ls(type='zSolverTransform'))
        new_meshes = cmds.ls(dag=True, type='mesh', noIntermediate=True)
        self.assertCountsEqual(old_meshes, new_meshes)
        # Referenced nodes cannot be renamed or deleted, so we should not check for their deletion.

    def test_merge_referenced_and_typical_solver(self):
        # merge the referenced solver into the typical one, and the other way around.
        for i in range(2):
            # Setup
            cmds.file(force=True, new=True)
            make_scene_with_referenced_and_typical_solver()
            old_meshes = cmds.ls(dag=True, type='mesh', noIntermediate=True)
            solvers = cmds.ls(type='zSolverTransform')
            solver_to_keep = solvers[i]
            solver_to_lose = solvers[(i + 1) % 2]
            print((solver_to_keep, solver_to_lose))  # so we know which test failed

            # Act
            merge_two_solvers(solver_to_keep, solver_to_lose)

            # Verify
            self.assertIn(solver_to_keep, cmds.ls(type='zSolverTransform'))
            new_meshes = cmds.ls(dag=True, type='mesh', noIntermediate=True)
            self.assertCountsEqual(old_meshes, new_meshes)
            # Referenced nodes cannot be renamed or deleted, so we should not check for their deletion.

    def test_merge_solvers_can_handle_connection_to_enabled(self):
        # Setup
        solver1, _ = make_a_simple_test_scene()
        locator1 = cmds.spaceLocator()[0]
        cmds.connectAttr(locator1 + '.visibility', solver1 + '.enable')
        solver2, _ = make_a_simple_test_scene()
        locator2 = cmds.spaceLocator()[0]
        cmds.connectAttr(locator2 + '.visibility', solver2 + '.enable')

        # Act
        merge_two_solvers(solver1, solver2)

        # Verify
        input_to_enable = cmds.listConnections(solver1 + '.enable', d=False, s=True, p=True)
        self.assertEqual(input_to_enable, [locator1 + '.visibility'])

    def test_can_merge_many_solvers(self):
        # Setup
        solvers = []
        solvers.append(make_a_simple_test_scene()[0])
        solvers.append(make_a_simple_test_scene()[0])
        solvers.append(make_a_simple_test_scene()[0])
        solvers.append(make_a_simple_test_scene()[0])
        old_meshes = cmds.ls(dag=True, type='mesh', noIntermediate=True)

        # Act
        merge_solvers(solvers)

        # Verify
        new_meshes = cmds.ls(dag=True, type='mesh', noIntermediate=True)
        self.assertCountsEqual(old_meshes, new_meshes)
        self.assertIn(solvers[0], cmds.ls(type='zSolverTransform'))
        self.assertEqual(1, len(cmds.ls(type='zSolverTransform')))
        self.assertEqual(1, len(cmds.ls(type='zEmbedder')))
        self.assertEqual(1, len(cmds.ls(type='zSolver')))
