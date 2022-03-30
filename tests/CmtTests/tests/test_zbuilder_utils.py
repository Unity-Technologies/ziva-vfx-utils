import os
import tests.utils as test_utils
import zBuilder.utils as utils
import zBuilder.builders.ziva as zva
import zBuilder.zMaya as mz

from maya import cmds
from vfx_test_case import VfxTestCase, ZivaUpdateTestCase, get_mesh_vertex_positions
from zBuilder.commonUtils import parse_version_info
from zBuilder.mayaUtils import replace_long_name


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
            results.append(replace_long_name('^r_', 'l_', case))

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
            results.append(replace_long_name('_r_', '_l_', case))

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
        observed = {k: replace_long_name('^', 'prefix_', k) for k in expected.keys()}

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
        observed = {k: replace_long_name('$', '_postfix', k) for k in expected.keys()}

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
        observed = {k: replace_long_name('(^|_)r($|_)', 'l', k) for k in expected.keys()}

        self.assertDictEqual(expected, observed)

    def test_get_zbones_case1(self):
        test_utils.build_anatomical_arm_with_no_popup()

        # For this test lets add a bone without an attachment.  Previously
        # it was not able to pick this case up.
        cmds.select('hand_bone')
        cmds.ziva(b=True)

        # testing command
        cmds.select('bone_grp', hi=True)
        bones = mz.get_zBones(cmds.ls(sl=True))

        self.assertEqual(len(bones), 5)

    def test_get_zbones_case2(self):
        test_utils.build_anatomical_arm_with_no_popup()

        # testing command
        cmds.select('r_humerus_bone', 'r_radius_bone', 'hand_bone')
        bones = mz.get_zBones(cmds.ls(sl=True))

        # we should have 2 as the hand bone is not a zBone in this case
        self.assertEqual(len(bones), 2)


class BuilderUtilsTestCaseArm(VfxTestCase):

    def setUp(self):
        super(BuilderUtilsTestCaseArm, self).setUp()
        test_utils.build_anatomical_arm_with_no_popup()

    def test_copy_paste(self):
        cmds.select(cl=True)

        cmds.duplicate('r_bicep_muscle', name='dupe')
        cmds.polySmooth('dupe')
        cmds.select('r_bicep_muscle', 'dupe')

        utils.copy_paste()
        self.assertSceneHasNodes(['dupe_r_radius_bone'])

    def test_utils_rig_copy_paste_clean(self):
        # testing menu command to copy and paste on ziva that has been cleaned
        cmds.select('zSolver1')
        utils.rig_copy()

        utils.clean_scene()

        utils.rig_paste()
        self.assertSceneHasNodes(['zSolver1'])

    def test_utils_rig_cut(self):
        # testing the cut feature, removing ziva setup after copy
        cmds.select('zSolver1')
        utils.rig_cut()

        # there should be no attachments in scene
        self.assertTrue(len(cmds.ls(type='zAttachment')) is 0)

    def test_remove_single_items(self):

        types = ['zAttachment', 'zFiber']
        result = []

        all_items = cmds.ls(type=types)
        utils.remove(all_items)

        result.extend(cmds.ls(type=types))

        self.assertTrue(result == [])

    def test_remove_all_of_type(self):
        types = ['zAttachment', 'zFiber']
        result = []
        # testing removing all attachments

        for type_ in types:
            all_items = cmds.ls(type=type_)

            # delete all attachments
            utils.remove(all_items)
            result.append(cmds.ls(type=type_))

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
            utils.remove(cmds.ls(sl=True))
        cmds.select(cl=True)
        self.assertIsNone(cmds.zQuery(bt=True))

    def test_rig_copy_without_selection_should_raise(self):
        cmds.select(cl=True)
        with self.assertRaises(Exception):
            utils.rig_copy()

    def test_save_rig(self):
        # Setup
        file_name = test_utils.get_tmp_file_location('.zBuilder')
        cmds.select('zSolver1')

        # Action
        utils.save_rig(file_name)

        # Verify
        # simply check if file exists
        self.assertTrue(os.path.exists(file_name))
        self.assertGreater(os.path.getsize(file_name), 1000)

        os.remove(file_name)

    def test_load_rig(self):
        # Setup
        file_name = test_utils.get_tmp_file_location('.zBuilder')
        cmds.select('zSolver1')
        utils.save_rig(file_name)
        # clean scene so we just have geo
        utils.clean_scene()

        # Action
        utils.load_rig(file_name)

        # Verify
        self.assertSceneHasNodes(['zSolver1'])

        os.remove(file_name)

    def test_update_1_solver_nothing_selected(self):
        ## SETUP
        # create a cluster on a vert on arm to move it on live ziva rig
        vert = 'r_bicep_muscle.vtx[961]'
        cmds.select(vert)
        cmds.cluster()
        cmds.setAttr('cluster1Handle.translateZ', 5)
        expected_pos = get_mesh_vertex_positions('r_bicep_muscle')

        ## ACT
        cmds.select(cl=True)
        utils.rig_update()

        ## VERIFY
        geoNode = cmds.zQuery('r_bicep_muscle', t='zGeo')[0]
        cmds.polySphere(n='mesh')
        cmds.connectAttr('{}.iNeutralMesh'.format(geoNode), 'mesh.inMesh', force=True)
        observed_pos = get_mesh_vertex_positions('mesh')
        self.assertAllApproxEqual(expected_pos, observed_pos, 1e-3)

    def test_update_1_solver_solver_selected(self):
        ## SETUP
        # create a cluster on a vert on arm to move it on live ziva rig
        vert = 'r_bicep_muscle.vtx[961]'
        cmds.select(vert)
        cmds.cluster()
        cmds.setAttr('cluster1Handle.translateZ', 5)
        expected_pos = get_mesh_vertex_positions('r_bicep_muscle')

        ## ACT
        cmds.select('zSolver1')
        utils.rig_update()

        ## VERIFY
        geoNode = cmds.zQuery('r_bicep_muscle', t='zGeo')[0]
        cmds.polySphere(n='mesh')
        cmds.connectAttr('{}.iNeutralMesh'.format(geoNode), 'mesh.inMesh', force=True)
        observed_pos = get_mesh_vertex_positions('mesh')
        self.assertAllApproxEqual(expected_pos, observed_pos, 1e-3)


class BuilderUtilsTestCase(VfxTestCase):

    def test_version_parse_function(self):
        # Valid cases
        # major.minor.patch-tag
        major, minor, patch, tag = parse_version_info("1.2.30-alpha")
        self.assertEqual(major, 1)
        self.assertEqual(minor, 2)
        self.assertEqual(patch, 30)
        self.assertEqual(tag, "alpha")

        # major.minor.patch
        major, minor, patch, tag = parse_version_info("1.20.3")
        self.assertEqual(major, 1)
        self.assertEqual(minor, 20)
        self.assertEqual(patch, 3)
        self.assertEqual(tag, "")

        # major.minor-tag
        major, minor, patch, tag = parse_version_info("1.33-beta")
        self.assertEqual(major, 1)
        self.assertEqual(minor, 33)
        self.assertEqual(patch, 0)
        self.assertEqual(tag, "beta")

        # major.minor
        major, minor, patch, tag = parse_version_info("10.2")
        self.assertEqual(major, 10)
        self.assertEqual(minor, 2)
        self.assertEqual(patch, 0)
        self.assertEqual(tag, "")

        # Invalid cases
        # major-tag
        with self.assertRaises(AssertionError):
            parse_version_info("1-gammar")

        # major only
        with self.assertRaises(AssertionError):
            parse_version_info("1")

        # non-integer version number
        with self.assertRaises(AssertionError):
            parse_version_info("1.0c")

        # missing major version
        with self.assertRaises(AssertionError):
            parse_version_info(".1.2")

        # negative version number
        with self.assertRaises(AssertionError):
            parse_version_info("1.-2")

    def test_remove_all_solvers(self):
        cmds.ziva(s=True)
        cmds.ziva(s=True)

        utils.remove_all_solvers()

        self.assertEqual(cmds.ls(type='zSolver'), [])

    def test_remove_referenced_solver(self):
        cmds.ziva(s=True)
        cmds.file(rename='tempfile')
        filepath = cmds.file(force=True, save=True)
        cmds.file(force=True, new=True)
        cmds.file(filepath, r=True, namespace='ns')

        with self.assertRaisesRegexp(Exception, 'reference'):
            utils.remove_solver(solvers=['ns:zSolver1'])

        self.assertEqual(cmds.ls(type='zSolverTransform'), ['ns:zSolver1'])

    def test_remove_single_solver(self):
        cmds.ziva(s=True)
        cmds.ziva(s=True)

        utils.remove_solver(solvers=['zSolver1'])
        self.assertListEqual(cmds.ls(type='zSolver'), ['zSolver2Shape'])

    def test_update_no_solvers(self):
        # scene is empty with no solvers, this should raise an error with update
        with self.assertRaises(Exception):
            utils.rig_update()

    def test_rig_transfer_warped_prefix(self):
        # get demo arm geo to add prefix
        test_utils.build_anatomical_arm_with_no_popup(ziva_setup=False)

        # prefix all geometry transforms with warped_
        to_change = ['muscle_grp', 'bone_grp', 'rig_grp']
        transforms = cmds.listRelatives(to_change,
                                        children=True,
                                        allDescendents=True,
                                        type='transform')

        for item in transforms + to_change:
            cmds.rename(item, 'warped_{}'.format(item))

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

        cmds.select('r_muscle')
        utils.copy_paste_with_substitution('^r', 'l')

        self.assertSceneHasNodes(['l_zMaterial1', 'l_zTissue'])


class BuilderUtilsMirrorTestCase_part2(ZivaUpdateTestCase):
    """This Class tests a specific type of "mirroring" so there are some assumptions made

    - geometry has an identifiable qualifier, in this case it is l_ and r_
    - Both sides geometry are in the scene
    - Both sides have Ziva nodes

    """

    def setUp(self):
        super(BuilderUtilsMirrorTestCase_part2, self).setUp()
        test_utils.load_scene(scene_name='copy_paste_bug2.ma')

        self.builder = zva.Ziva()
        self.builder.retrieve_from_scene()

        cmds.select('pSphere2')
        utils.rig_cut()

        self.stored_buffer = utils.return_copy_buffer()

        cmds.select('pSphere1')
        utils.rig_paste()

    def test_menu_paste(self):

        att_map = self.builder.get_scene_items(type_filter='map',
                                               name_filter='zAttachment1.weightList[0].weights')[0]

        self.builder_new = zva.Ziva()
        self.builder_new.retrieve_from_scene()

        new_att_map = self.builder_new.get_scene_items(
            type_filter='map', name_filter='zAttachment1.weightList[0].weights')[0]

        # the New map has been interpolated on a larger mesh so size of map should
        # be different
        self.assertNotEqual(len(att_map.values), len(new_att_map.values))

        # it has been interpolated and source map just has 1's and 0's.  Being
        # interpolated lets check for values that are not 1 or 0
        non_binary_values = [x for x in new_att_map.values if x != 0.0 and x != 1.0]
        self.assertTrue(non_binary_values)

        # test post paste
        # stiffness on attachment should equal 20
        self.assertEquals(cmds.getAttr("zAttachment1.stiffness"), 20)

        # the map is on a new node now lets check what happens when we change a value
        # on pasted item the paste again.
        cmds.setAttr("zAttachment1.stiffness", 10)

        cmds.select('pSphere3')

        utils.rig_paste()
        # New attachment gets named zAttachment2, this stiffness should equal 20
        self.assertEquals(cmds.getAttr("zAttachment2.stiffness"), 20)
        # make sure att1 is still 20 as well.
        self.assertEquals(cmds.getAttr("zAttachment1.stiffness"), 10)

    def test_copy_buffer(self):
        # it has been pasted in setup.  Now the buffer should remain unchanged
        # get buffer again and compare

        build = zva.Ziva()
        build.retrieve_from_scene()

        # this gets interpolate so scene builder should be different then buffer
        self.assertNotEquals(self.stored_buffer, build)

        current_buffer = utils.return_copy_buffer()

        # these should be same
        self.assertEquals(self.stored_buffer, current_buffer)


class ZivaCopyBuffer(ZivaUpdateTestCase):
    """
    This Class tests a specific type of "mirroring" so there are some assumptions made
    """

    def setUp(self):
        super(ZivaCopyBuffer, self).setUp()
        test_utils.load_scene(scene_name='copy_paste_bug2.ma')

        self.builder = zva.Ziva()
        self.builder.retrieve_from_scene()

        cmds.select('pSphere2')
        utils.rig_cut()

        self.stored_buffer = utils.return_copy_buffer()

        cmds.select('pSphere3')
        utils.rig_paste()

    def test_copy_buffer(self):
        # it has been pasted in setup.  Now the buffer should remain unchanged
        # get buffer again and compare

        current_buffer = utils.return_copy_buffer()

        # these should be same
        self.assertEquals(self.stored_buffer, current_buffer)

        # lets make some changes to scene to make sure it is a deep copy(buffer should not change)
        cmds.setAttr('zAttachment1.weightList[0].weights[0]', 22)
        cmds.setAttr('zAttachment1.stiffness', 10)

        builder = zva.Ziva()
        builder.retrieve_from_scene()

        # not equal to scene
        self.assertNotEquals(self.stored_buffer, builder)
        # equal to existing buffer
        self.assertEquals(self.stored_buffer, utils.return_copy_buffer())
