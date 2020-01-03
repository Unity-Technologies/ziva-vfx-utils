import maya.cmds as mc
import maya.mel as mm
import os
import logging
import sys

import zBuilder.zMaya as mz
import zBuilder.builders.ziva as zva

from vfx_test_case import VfxTestCase


class ZivaClothTestCase(VfxTestCase):
    @classmethod
    def setUpClass(cls):
        pass

    def setUp(self):
        super(ZivaClothTestCase, self).setUp()

        # build a simple cloth scene
        a_cloth = mc.polySphere(n='l_arm')[0]
        mc.setAttr(a_cloth + '.translateX', 10)
        b_cloth = mc.polySphere(n='r_arm')[0]
        mc.setAttr(b_cloth + '.translateX', -10)
        mc.select('l_arm')
        mm.eval('ziva -c')

    def tearDown(self):
        super(ZivaClothTestCase, self).tearDown()

    def test_mirror_cloth(self):
        # this is a test for a bug in VFXACT-120
        # if you mirror a zCloth and it is not named with a side prefix it would get
        # confused and assert.  This should not assert now and result in a mirror
        # there should be 2 zCloth nodes in scene when done.
        mc.select('l_arm')

        z = zva.Ziva()

        z.retrieve_from_scene_selection()
        z.string_replace('l_', 'r_')
        z.build()

        self.assertSceneHasNodes(['zCloth1', 'zCloth2'])
