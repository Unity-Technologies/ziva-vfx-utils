import tempfile
import os

import maya.cmds as mc
import maya.mel as mm

import zBuilder.zMaya as mz
import zBuilder.tests.utils as utl
import zBuilder.utils as utility
import zBuilder.builder as bld
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

    def test_replace_long_name_usecase3(self):
        strings = [
            'r_bicep', 'r_bicep__r_tricep', '|muscle_geo|r_bicep', 'rr_bicep', '|r_bicep',
            'r_bicep_r', '|muscles_geo|bicep_r|muscle_r'
        ]

        outputs = [
            'l_bicep', 'l_bicep__l_tricep', '|muscle_geo|l_bicep', 'rr_bicep', '|l_bicep',
            'l_bicep_l', '|muscles_geo|bicep_l|muscle_l'
        ]

        results = list()

        for case in strings:
            results.append(mz.replace_long_name('(^|_)r($|_)', 'l', case))

        self.assertEqual(results, outputs)

    def test_get_zbones_case1(self):
        utl.build_anatomical_arm_with_no_popup()

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
        utl.build_anatomical_arm_with_no_popup()

        # testing command
        mc.select('r_humerus_bone', 'r_radius_bone', 'hand_bone')
        import zBuilder.zMaya as mz
        bones = mz.get_zBones(mc.ls(sl=True))

        # we should have 2 as the hand bone is not a zBone in this case
        self.assertEqual(len(bones), 2)


class BuilderUtilsTestCaseArm(VfxTestCase):
    def setUp(self):
        super(BuilderUtilsTestCaseArm, self).setUp()

        utl.build_anatomical_arm_with_no_popup()

    def tearDown(self):
        super(BuilderUtilsTestCaseArm, self).tearDown()

    def test_copy_paste(self):
        mc.select(cl=True)

        mc.duplicate('r_bicep_muscle', name='dupe')
        mc.polySmooth('dupe')
        mc.select('r_bicep_muscle', 'dupe')

        utility.copy_paste()
        self.assertSceneHasNodes(['dupe_r_radius_bone'])

    def test_utils_rig_copy_paste_clean(self):
        # testing menu command to copy and paste on ziva that has been cleaned
        mc.select('zSolver1')
        utility.rig_copy()

        mz.clean_scene()

        utility.rig_paste()
        self.assertSceneHasNodes(['zSolver1'])

    def test_utils_rig_cut(self):
        # testing the cut feature, removing ziva setup after copy
        mc.select('zSolver1')
        utility.rig_cut()

        # there should be no attachments in scene
        self.assertTrue(len(mc.ls(type='zAttachment')) is 0)

    def test_remove_single_items(self):

        types = ['zAttachment', 'zFiber']
        result = []

        all_items = mc.ls(type=types)
        utility.remove(all_items)

        result.extend(mc.ls(type=types))

        self.assertTrue(result == [])

    def test_remove_all_of_type(self):
        types = ['zAttachment', 'zFiber']
        result = []
        # testing removing all attachments

        for type_ in types:
            all_items = mc.ls(type=type_)

            # delete all attachments
            utility.remove(all_items)
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
            utility.remove(mc.ls(sl=True))
        mc.select(cl=True)
        self.assertIsNone(mm.eval('zQuery -bt'))

    def test_rig_copy_without_selection_should_raise(self):
        mc.select(cl=True)
        with self.assertRaises(StandardError):
            utility.rig_copy()

    def test_save_rig(self):
        # find a temp file location
        fd, file_name = tempfile.mkstemp(suffix='.zBuilder')

        mc.select('zSolver1')

        utility.save_rig(file_name)

        # simply check if file exists, if it does it passes
        self.assertTrue(os.path.exists(file_name))
        self.assertGreater(os.path.getsize(file_name), 1000)

        os.close(fd)
        os.remove(file_name)

    def test_load_rig(self):
        # find a temp file location
        fd, file_name = tempfile.mkstemp(suffix='.zBuilder')

        mc.select('zSolver1')

        utility.save_rig(file_name)

        # clean scene so we just have geo
        mz.clean_scene()

        utility.load_rig(file_name)
        self.assertSceneHasNodes(['zSolver1'])

        os.close(fd)
        os.remove(file_name)


class BuilderUtilsTestCase(VfxTestCase):
    def test_builder_factory_throws_when_class_is_not_found(self):
        with self.assertRaises(StandardError):
            bld.builder_factory('class_not_found_error')

    def test_remove_all_solvers(self):
        mm.eval('ziva -s')
        mm.eval('ziva -s')

        utility.remove_all_solvers()

        self.assertEqual(mc.ls(type='zSolver'), [])

    def test_remove_single_solver(self):
        mm.eval('ziva -s')
        mm.eval('ziva -s')

        utility.remove_solver(solvers=['zSolver1'])
        self.assertListEqual(mc.ls(type='zSolver'), ['zSolver2Shape'])


class BuilderUtilsMirrorTestCase(VfxTestCase):
    def test_copy_paste_with_substitution(self):
        utl.build_mirror_sample_geo()
        utl.ziva_mirror_sample_geo()
        mz.rename_ziva_nodes()

        mc.select('r_muscle')
        utility.copy_paste_with_substitution('^r', 'l')

        self.assertSceneHasNodes(['l_zMaterial', 'l_zTissue'])
