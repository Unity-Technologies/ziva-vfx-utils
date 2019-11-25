import tempfile
import os

import maya.cmds as mc
import maya.mel as mm

import zBuilder.zMaya as mz
import tests.utils as test_utils
import zBuilder.utils as utils
import zBuilder.builder as bld
from vfx_test_case import get_mesh_vertex_positions
from vfx_test_case import VfxTestCase


class BuilderMayaTestCase(VfxTestCase):
    def test_replace_long_name_usecase1(self):
        # searching and replacing r_ at begining of string
        # check long name use case
        strings = [
            'r_bicep', 'r_bicep__r_tricep', '|muscle_geo|r_bicep', 'rr_bicep', '|r_bicep',
            'r_bicep_r'
        ]

        outputs = [
            'l_bicep', 'l_bicep__r_tricep', '|muscle_geo|l_bicep', 'rr_bicep', '|l_bicep',
            'l_bicep_r'
        ]

        results = list()

        for case in strings:
            results.append(mz.replace_long_name('^r_', 'l_', case))

        self.assertEqual(results, outputs)

    def test_replace_long_name_usecase2(self):
        strings = [
            'r_bicep', 'r_bicep__r_tricep', '|muscle_geo|r_bicep', 'rr_bicep', '|r_bicep',
            'r_bicep_r'
        ]

        outputs = [
            'r_bicep', 'r_bicep__l_tricep', '|muscle_geo|r_bicep', 'rr_bicep', '|r_bicep',
            'r_bicep_r'
        ]

        results = list()

        for case in strings:
            results.append(mz.replace_long_name('_r_', '_l_', case))

        self.assertEqual(results, outputs)

    def test_replace_long_name_prefix(self):
        # yapf: disable
        expected = {

            'r_bicep'           : 'prefix_r_bicep',
            'r_bicep__r_tricep' : 'prefix_r_bicep__r_tricep',
            '|r_bicep'          : '|prefix_r_bicep',
            '|foo|r_bicep'      : '|prefix_foo|prefix_r_bicep',
            '|foo|bar|r_bicep'  : '|prefix_foo|prefix_bar|prefix_r_bicep',
            None                :  None,
            ''                  : '',
            ' '                 : ' ',
        }
        # yapf: enable
        observed = {k: mz.replace_long_name('^', 'prefix_', k) for k in expected.keys()}

        self.assertDictEqual(expected, observed)

    def test_replace_long_name_postfix(self):
        # yapf: disable
        expected = {

            'r_bicep'           : 'r_bicep_postfix',
            'r_bicep__r_tricep' : 'r_bicep__r_tricep_postfix',
            '|r_bicep'          : '|r_bicep_postfix',
            '|foo|r_bicep'      : '|foo_postfix|r_bicep_postfix',
            '|foo|bar|r_bicep'  : '|foo_postfix|bar_postfix|r_bicep_postfix',
            None                :  None,
            ''                  : '',
            ' '                 : ' ',
        }
        # yapf: enable
        observed = {k: mz.replace_long_name('$', '_postfix', k) for k in expected.keys()}

        self.assertDictEqual(expected, observed)

    def test_replace_long_name_groups(self):
        # yapf: disable
        expected = {
            '|muscles_geo|bicep_r|muscle_r' : '|muscles_geo|bicep_l|muscle_l',
            'rr_bicep'                      : 'rr_bicep',
            'r_bicep'                       : 'l_bicep',
            'r_bicep__r_tricep'             : 'l_bicep__l_tricep',
            '|r_bicep'                      : '|l_bicep',
            '|foo|r_bicep'                  : '|foo|l_bicep',
            '|foo|bar|r_bicep'              : '|foo|bar|l_bicep',
            None                            :  None,
            ''                              : '',
            ' '                             : ' ',
        }
        # yapf: enable
        observed = {k: mz.replace_long_name('(^|_)r($|_)', 'l', k) for k in expected.keys()}

        self.assertDictEqual(expected, observed)

    def test_get_zbones_case1(self):
        test_utils.build_anatomical_arm_with_no_popup()

        # For this test lets add a bone without an attachment.  Previously
        # it was not able to pick this case up.
        mc.select('hand_bone')
        mm.eval('ziva -b')

        # testing command
        mc.select('bone_grp', hi=True)
        import zBuilder.zMaya as mz
        bones = mz.get_zBones(mc.ls(sl=True))

        self.assertEqual(len(bones), 5)

    def test_get_zbones_case2(self):
        test_utils.build_anatomical_arm_with_no_popup()

        # testing command
        mc.select('r_humerus_bone', 'r_radius_bone', 'hand_bone')
        import zBuilder.zMaya as mz
        bones = mz.get_zBones(mc.ls(sl=True))

        # we should have 2 as the hand bone is not a zBone in this case
        self.assertEqual(len(bones), 2)


class BuilderUtilsTestCaseArm(VfxTestCase):
    def setUp(self):
        super(BuilderUtilsTestCaseArm, self).setUp()

        test_utils.build_anatomical_arm_with_no_popup()

    def tearDown(self):
        super(BuilderUtilsTestCaseArm, self).tearDown()

    def test_copy_paste(self):
        mc.select(cl=True)

        mc.duplicate('r_bicep_muscle', name='dupe')
        mc.polySmooth('dupe')
        mc.select('r_bicep_muscle', 'dupe')

        utils.copy_paste()
        self.assertSceneHasNodes(['dupe_r_radius_bone'])

    def test_utils_rig_copy_paste_clean(self):
        # testing menu command to copy and paste on ziva that has been cleaned
        mc.select('zSolver1')
        utils.rig_copy()

        mz.clean_scene()

        utils.rig_paste()
        self.assertSceneHasNodes(['zSolver1'])

    def test_utils_rig_cut(self):
        # testing the cut feature, removing ziva setup after copy
        mc.select('zSolver1')
        utils.rig_cut()

        # there should be no attachments in scene
        self.assertTrue(len(mc.ls(type='zAttachment')) is 0)

    def test_remove_single_items(self):

        types = ['zAttachment', 'zFiber']
        result = []

        all_items = mc.ls(type=types)
        utils.remove(all_items)

        result.extend(mc.ls(type=types))

        self.assertTrue(result == [])

    def test_remove_all_of_type(self):
        types = ['zAttachment', 'zFiber']
        result = []
        # testing removing all attachments

        for type_ in types:
            all_items = mc.ls(type=type_)

            # delete all attachments
            utils.remove(all_items)
            result.append(mc.ls(type=type_))

        self.assertTrue(all(x == [] for x in result))

    def test_remove_all_of_bodies(self):
        types = ['zTissue', 'zBone', 'zCloth']
        # testing removing all bodies

        sph = mc.polySphere()
        mc.select(sph[0])
        mm.eval('ziva -c')

        for type_ in types:
            mc.select(mc.ls(type=type_))

            # select the body geo
            mc.select(mm.eval('zQuery -m'))

            # delete all
            utils.remove(mc.ls(sl=True))
        mc.select(cl=True)
        self.assertIsNone(mm.eval('zQuery -bt'))

    def test_rig_copy_without_selection_should_raise(self):
        mc.select(cl=True)
        with self.assertRaises(Exception):
            utils.rig_copy()

    def test_save_rig(self):
        # find a temp file location
        fd, file_name = tempfile.mkstemp(suffix='.zBuilder')

        mc.select('zSolver1')

        utils.save_rig(file_name)

        # simply check if file exists, if it does it passes
        self.assertTrue(os.path.exists(file_name))
        self.assertGreater(os.path.getsize(file_name), 1000)

        os.close(fd)
        os.remove(file_name)

    def test_load_rig(self):
        # find a temp file location
        fd, file_name = tempfile.mkstemp(suffix='.zBuilder')

        mc.select('zSolver1')

        utils.save_rig(file_name)

        # clean scene so we just have geo
        mz.clean_scene()

        utils.load_rig(file_name)
        self.assertSceneHasNodes(['zSolver1'])

        os.close(fd)
        os.remove(file_name)

    def test_update_1_solver_nothing_selected(self):
        ## SETUP
        # create a cluster on a vert on arm to move it on live ziva rig
        vert = 'r_bicep_muscle.vtx[961]'
        mc.select(vert)
        mc.cluster()
        mc.setAttr('cluster1Handle.translateZ', 5)
        expected_pos = get_mesh_vertex_positions('r_bicep_muscle')

        ## ACT
        mc.select(cl=True)
        utils.rig_update()

        ## VERIFY
        geoNode = mm.eval('zQuery -t zGeo r_bicep_muscle')[0]
        mc.polySphere(n='mesh')
        mc.connectAttr('{}.iNeutralMesh'.format(geoNode), 'mesh.inMesh', force=True)
        observed_pos = get_mesh_vertex_positions('mesh')
        self.assertAllApproxEqual(expected_pos, observed_pos, 1e-3)

    def test_update_1_solver_solver_selected(self):
        ## SETUP
        # create a cluster on a vert on arm to move it on live ziva rig
        vert = 'r_bicep_muscle.vtx[961]'
        mc.select(vert)
        mc.cluster()
        mc.setAttr('cluster1Handle.translateZ', 5)
        expected_pos = get_mesh_vertex_positions('r_bicep_muscle')

        ## ACT
        mc.select('zSolver1')
        utils.rig_update()

        ## VERIFY
        geoNode = mm.eval('zQuery -t zGeo r_bicep_muscle')[0]
        mc.polySphere(n='mesh')
        mc.connectAttr('{}.iNeutralMesh'.format(geoNode), 'mesh.inMesh', force=True)
        observed_pos = get_mesh_vertex_positions('mesh')
        self.assertAllApproxEqual(expected_pos, observed_pos, 1e-3)


class BuilderUtilsTestCase(VfxTestCase):
    def test_builder_factory_throws_when_class_is_not_found(self):
        with self.assertRaises(Exception):
            bld.builder_factory('class_not_found_error')

    def test_remove_all_solvers(self):
        mm.eval('ziva -s')
        mm.eval('ziva -s')

        utils.remove_all_solvers()

        self.assertEqual(mc.ls(type='zSolver'), [])

    def test_remove_single_solver(self):
        mm.eval('ziva -s')
        mm.eval('ziva -s')

        utils.remove_solver(solvers=['zSolver1'])
        self.assertListEqual(mc.ls(type='zSolver'), ['zSolver2Shape'])

    def test_update_no_solvers(self):
        # scene is empty with no solvers, this should raise an error with update
        with self.assertRaises(Exception):
            utils.rig_update()

    def test_rig_transfer_warped_prefix(self):
        # get demo arm geo to add prefix
        test_utils.build_anatomical_arm_with_no_popup(ziva_setup=False)

        # prefix all geometry transforms with warped_
        to_change = ['muscle_grp', 'bone_grp', 'rig_grp']
        transforms = mc.listRelatives(to_change,
                                      children=True,
                                      allDescendents=True,
                                      type='transform')

        for item in transforms + to_change:
            mc.rename(item, 'warped_{}'.format(item))

        # get full setup demo arm
        test_utils.build_anatomical_arm_with_no_popup(ziva_setup=True, new_scene=False)

        # now do the trasnfer
        utils.rig_transfer('zSolver1', 'warped_', '')

        # when done we should have some ziva nodes with a 'warped_' prefix
        nodes_in_scene = [
            'warped_zSolver1', 'warped_r_bicep_muscle_zTissue', 'warped_r_bicep_muscle_zFiber',
            'warped_r_tricepsTendon_muscle_zTet'
        ]
        self.assertSceneHasNodes(nodes_in_scene)


class BuilderUtilsMirrorTestCase(VfxTestCase):
    def test_copy_paste_with_substitution(self):
        test_utils.build_mirror_sample_geo()
        test_utils.ziva_mirror_sample_geo()
        mz.rename_ziva_nodes()

        mc.select('r_muscle')
        utils.copy_paste_with_substitution('^r', 'l')

        self.assertSceneHasNodes(['l_zMaterial', 'l_zTissue'])
