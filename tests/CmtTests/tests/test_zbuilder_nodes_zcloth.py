from maya import cmds
from maya import mel
import os
import logging
import sys

import zBuilder.zMaya as mz
import zBuilder.builders.ziva as zva

from vfx_test_case import VfxTestCase


class ZivaClothTestCase(VfxTestCase):
    def setUp(self):
        super(ZivaClothTestCase, self).setUp()

        # build a simple cloth scene
        a_cloth = cmds.polySphere(n='l_arm')[0]
        cmds.setAttr(a_cloth + '.translateX', 10)
        b_cloth = cmds.polySphere(n='r_arm')[0]
        cmds.setAttr(b_cloth + '.translateX', -10)
        cmds.select('l_arm')
        mel.eval('ziva -c')

    def test_mirror_cloth(self):
        # this is a test for a bug in VFXACT-120
        # if you mirror a zCloth and it is not named with a side prefix it would get
        # confused and assert.  This should not assert now and result in a mirror
        # there should be 2 zCloth nodes in scene when done.
        cmds.select('l_arm')

        z = zva.Ziva()

        z.retrieve_from_scene_selection()
        z.string_replace('l_', 'r_')
        z.build()

        self.assertSceneHasNodes(['zCloth1', 'zCloth2'])
