import maya.cmds as mc
import maya.mel as mm
import os
import logging
import sys

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

        print 'This should match: ', outputs
        print '             this: ', results

        self.assertTrue(results == outputs)

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

        print 'This should match: ', outputs
        print '             this: ', results

        self.assertTrue(results == outputs)

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

        print 'This should match: ', outputs
        print '             this: ', results

        self.assertTrue(results == outputs)
