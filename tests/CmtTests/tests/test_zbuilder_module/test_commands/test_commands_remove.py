from maya import cmds
from vfx_test_case import VfxTestCase, get_mesh_vertex_positions
from tests.utils import build_anatomical_arm_with_no_popup
from zBuilder.commands import remove, remove_solver, remove_all_solvers, rig_update, rig_transfer


class RemoveCommandsWithArmAsset(VfxTestCase):

    def setUp(self):
        super(RemoveCommandsWithArmAsset, self).setUp()
        build_anatomical_arm_with_no_popup()

    def test_remove_single_items(self):
        # Action
        types = ('zAttachment', 'zFiber')
        all_items = cmds.ls(type=types)
        remove(all_items)
        result = []
        result.extend(cmds.ls(type=types))

        # Verify
        self.assertTrue(result == [])

    def test_remove_all_of_type(self):
        # Action: removing all attachments
        types = ('zAttachment', 'zFiber')
        result = []
        for type_ in types:
            all_items = cmds.ls(type=type_)
            remove(all_items)
            result.append(cmds.ls(type=type_))

        # Verify
        self.assertTrue(all(x == [] for x in result))

    def test_remove_all_of_bodies(self):
        types = ['zTissue', 'zBone', 'zCloth']
        # testing removing all bodies

        sph = cmds.polySphere()
        cmds.select(sph[0])
        cmds.ziva(c=True)

        for type_ in types:
            cmds.select(cmds.ls(type=type_))

            # select the body geo
            cmds.select(cmds.zQuery(m=True))

            # delete all
            remove(cmds.ls(sl=True))
        cmds.select(cl=True)
        self.assertIsNone(cmds.zQuery(bt=True))

    def test_update_1_solver_nothing_selected(self):
        # Setup: create a cluster on a vert on arm to move it on live ziva rig
        vert = 'r_bicep_muscle.vtx[961]'
        cmds.select(vert)
        cmds.cluster()
        cmds.setAttr('cluster1Handle.translateZ', 5)
        expected_pos = get_mesh_vertex_positions('r_bicep_muscle')

        # Act
        cmds.select(cl=True)
        rig_update()

        # Verify
        geoNode = cmds.zQuery('r_bicep_muscle', t='zGeo')[0]
        cmds.polySphere(n='mesh')
        cmds.connectAttr('{}.iNeutralMesh'.format(geoNode), 'mesh.inMesh', force=True)
        observed_pos = get_mesh_vertex_positions('mesh')
        self.assertAllApproxEqual(expected_pos, observed_pos, 1e-3)

    def test_update_1_solver_solver_selected(self):
        # Setup: create a cluster on a vert on arm to move it on live ziva rig
        vert = 'r_bicep_muscle.vtx[961]'
        cmds.select(vert)
        cmds.cluster()
        cmds.setAttr('cluster1Handle.translateZ', 5)
        expected_pos = get_mesh_vertex_positions('r_bicep_muscle')

        # Action
        cmds.select('zSolver1')
        rig_update()

        # Verify
        geoNode = cmds.zQuery('r_bicep_muscle', t='zGeo')[0]
        cmds.polySphere(n='mesh')
        cmds.connectAttr('{}.iNeutralMesh'.format(geoNode), 'mesh.inMesh', force=True)
        observed_pos = get_mesh_vertex_positions('mesh')
        self.assertAllApproxEqual(expected_pos, observed_pos, 1e-3)


class RemoveCommandTestCase(VfxTestCase):

    def test_remove_all_solvers(self):
        cmds.ziva(s=True)
        cmds.ziva(s=True)

        remove_all_solvers()

        self.assertEqual(cmds.ls(type='zSolver'), [])

    def test_remove_referenced_solver(self):
        cmds.ziva(s=True)
        cmds.file(rename='tempfile')
        filepath = cmds.file(force=True, save=True)
        cmds.file(force=True, new=True)
        cmds.file(filepath, r=True, namespace='ns')

        with self.assertRaisesRegexp(Exception, 'reference'):
            remove_solver(solvers=['ns:zSolver1'])

        self.assertEqual(cmds.ls(type='zSolverTransform'), ['ns:zSolver1'])

    def test_remove_single_solver(self):
        cmds.ziva(s=True)
        cmds.ziva(s=True)

        remove_solver(solvers=['zSolver1'])
        self.assertListEqual(cmds.ls(type='zSolver'), ['zSolver2Shape'])

    def test_update_no_solvers(self):
        # scene is empty with no solvers, this should raise an error with update
        with self.assertRaises(Exception):
            rig_update()

    def test_rig_transfer_warped_prefix(self):
        # get demo arm geo to add prefix
        build_anatomical_arm_with_no_popup(ziva_setup=False)

        # prefix all geometry transforms with warped_
        to_change = ['muscle_grp', 'bone_grp', 'rig_grp']
        transforms = cmds.listRelatives(to_change,
                                        children=True,
                                        allDescendents=True,
                                        type='transform')

        for item in transforms + to_change:
            cmds.rename(item, 'warped_{}'.format(item))

        # get full setup demo arm
        build_anatomical_arm_with_no_popup(ziva_setup=True, new_scene=False)

        # now do the trasnfer
        rig_transfer('zSolver1', 'warped_', '')

        # when done we should have some ziva nodes with a 'warped_' prefix
        nodes_in_scene = [
            'warped_zSolver1', 'warped_r_bicep_muscle_zTissue', 'warped_r_bicep_muscle_zFiber',
            'warped_r_tricepsTendon_muscle_zTet'
        ]
        self.assertSceneHasNodes(nodes_in_scene)
