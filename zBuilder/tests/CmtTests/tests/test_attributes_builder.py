import maya.cmds as mc
import maya.mel as mm
import os
import logging
import sys

import zBuilder.zMaya as mz
import zBuilder.builders.attributes as atr
import zBuilder.tests.utils as utl
import zBuilder.utils as utility

from vfx_test_case import VfxTestCase


class AttributesBuilderTestCase(VfxTestCase):
    @classmethod
    def setUpClass(cls):
        pass

    def setUp(self):
        super(AttributesBuilderTestCase, self).setUp()

    def tearDown(self):
        super(AttributesBuilderTestCase, self).tearDown()

    def test_retrieve_build(self):
        grp = mc.group(em=True)
        mc.setAttr(grp + '.translateX', 20)
        mc.select(grp)

        # use builder to retrieve from scene-----------------------------------
        z = atr.Attributes()
        z.retrieve_from_scene()

        mc.setAttr(grp + '.translateX', 0)

        z.build()

        self.assertTrue(mc.getAttr(grp + '.translateX') == 20)
