import maya.cmds as mc
import maya.mel as mel
import os
import logging
import sys

import zBuilder.zMaya as mz
import zBuilder.builders.ziva as zva
import zBuilder.tests.utils as utl
import zBuilder.util as utility

from vfx_test_case import VfxTestCase


class ZivaMirrorTestCase(VfxTestCase):

    @classmethod
    def setUpClass(cls):
        pass

    def setUp(self):
        super(ZivaMirrorTestCase, self).setUp()
        # Build a basic setup
        utl.build_mirror_sample_geo()
        utl.ziva_mirror_sample_geo()

        mc.select(cl=True)

        # use builder to retrieve from scene
        self.z = zva.Ziva()
        self.z.retrieve_from_scene()

        # string replace
        self.z.string_replace('^r_', 'l_')


    def tearDown(self):
        super(ZivaMirrorTestCase, self).tearDown()

    def test_mirror_clean_scene(self):
        # remove ziva nodes from scene so all we have left is geo
        mz.clean_scene()

        # # build it on live scene
        self.z.build()
        # check if left muscle is connected to zGeo
        self.assertTrue(len(mc.listConnections('l_muscle', type='zGeo')))

    def test_mirror_existing_scene(self):
        # # build it on live scene
        self.z.build()

        # check if left muscle is connected to zGeo
        self.assertTrue(len(mc.listConnections('l_muscle', type='zGeo')))

