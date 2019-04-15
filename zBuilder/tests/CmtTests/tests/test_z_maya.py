import maya.cmds as mc
import maya.mel as mm
import os
import logging
import sys
import zBuilder.tests.utils as utl

import zBuilder.zMaya as mz
from vfx_test_case import VfxTestCase


class ZivaMayaTestCase(VfxTestCase):

    def test_replace_long_name_usecase1(self):
        # searching and replacing r_ at begining of string
        # check long name use case
        strings = ['r_bicep',
                   'r_bicep__r_tricep',
                   '|muscle_geo|r_bicep',
                   'rr_bicep',
                   '|r_bicep',
                   'r_bicep_r']

        outputs = ['l_bicep',
                   'l_bicep__r_tricep',
                   '|muscle_geo|l_bicep',
                   'rr_bicep',
                   '|l_bicep',
                   'l_bicep_r']

        results = list()

        for case in strings:
            results.append(mz.replace_long_name('^r_', 'l_', case))

        self.assertEqual(results, outputs)

    def test_replace_long_name_usecase2(self):
        strings = ['r_bicep',
                   'r_bicep__r_tricep',
                   '|muscle_geo|r_bicep',
                   'rr_bicep',
                   '|r_bicep',
                   'r_bicep_r']

        outputs = ['r_bicep',
                   'r_bicep__l_tricep',
                   '|muscle_geo|r_bicep',
                   'rr_bicep',
                   '|r_bicep',
                   'r_bicep_r']

        results = list()

        for case in strings:
            results.append(mz.replace_long_name('_r_', '_l_', case))

        self.assertEqual(results, outputs)

    def test_replace_long_name_usecase3(self):
        strings = ['r_bicep',
                   'r_bicep__r_tricep',
                   '|muscle_geo|r_bicep',
                   'rr_bicep',
                   '|r_bicep',
                   'r_bicep_r',
                   '|muscles_geo|bicep_r|muscle_r']

        outputs = ['l_bicep',
                   'l_bicep__l_tricep',
                   '|muscle_geo|l_bicep',
                   'rr_bicep',
                   '|l_bicep',
                   'l_bicep_l',
                   '|muscles_geo|bicep_l|muscle_l']

        results = list()

        for case in strings:
            results.append(mz.replace_long_name('(^|_)r($|_)', 'l', case))

        self.assertEqual(results, outputs)

    def test_get_zbones_case1(self):
        # This builds the Zivas anatomical arm demo with no pop up dialog.
        utl.build_arm()

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
        # This builds the Zivas anatomical arm demo with no pop up dialog.
        utl.build_arm()

        # testing command
        mc.select('r_humerus_bone', 'r_radius_bone', 'hand_bone')
        import zBuilder.zMaya as mz
        bones = mz.get_zBones(mc.ls(sl=True))

        # we should have 2 as the hand bone is not a zBone in this case
        self.assertEqual(len(bones), 2)
