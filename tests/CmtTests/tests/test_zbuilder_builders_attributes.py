from maya import cmds
from maya import mel
import os
import logging
import sys

import zBuilder.zMaya as mz
import zBuilder.builders.attributes as atr

from vfx_test_case import VfxTestCase


class AttributesBuilderTestCase(VfxTestCase):
    def test_retrieve_build(self):
        grp = cmds.group(em=True)
        cmds.setAttr(grp + '.translateX', 20)
        cmds.select(grp)

        # use builder to retrieve from scene-----------------------------------
        z = atr.Attributes()
        z.retrieve_from_scene()

        cmds.setAttr(grp + '.translateX', 0)

        z.build()

        self.assertTrue(cmds.getAttr(grp + '.translateX') == 20)
