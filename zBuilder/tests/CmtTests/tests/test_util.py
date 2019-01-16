import maya.cmds as mc
import maya.mel as mel
import os
import logging
import sys

import zBuilder.zMaya as mz
import zBuilder.builders.ziva as zva
import zBuilder.tests.utils as utl
import zBuilder.util as utility

from zmaya_test_case import ZMayaTestCase


class UtilTestCase(ZMayaTestCase):

    @classmethod
    def setUpClass(cls):
        pass

    def setUp(self):
        super(UtilTestCase, self).setUp()

    def tearDown(self):
        super(UtilTestCase, self).tearDown()

    def test_copy_paste(self):
        # This builds the Zivas anatomical arm demo with no pop up dialog.
        # mc.loadPlugin('ziva.mll')
        utl.build_arm()

        mc.select(cl=True)

        mc.duplicate('r_bicep_muscle', name='dupe')
        mc.polySmooth('dupe')
        mc.select('r_bicep_muscle', 'dupe')

        utility.copy_paste()
        mc.ls(type='zAttachment')
        self.assertSceneHasNodes(['dupe_r_radius_bone'])
