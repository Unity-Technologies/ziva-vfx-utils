import maya.cmds as mc
import maya.mel as mel
import os
import logging
import sys
import tempfile

import zBuilder.zMaya as mz
import zBuilder.builders.ziva as zva
import zBuilder.tests.utils as utl
import zBuilder.util as utility

from vfx_test_case import VfxTestCase


class IOTestCase(VfxTestCase):

    @classmethod
    def setUpClass(cls):
        pass

    def setUp(self):
        super(IOTestCase, self).setUp()
        # Build a basic setup
        utl.build_mirror_sample_geo()
        utl.ziva_mirror_sample_geo()

        mc.select(cl=True)

        # use builder to retrieve from scene
        self.z = zva.Ziva()
        self.z.retrieve_from_scene()

        self.temp_files = []

    def tearDown(self):
        super(IOTestCase, self).tearDown()

        # delete temp files
        for temp_file in self.temp_files:
            if os.path.exists(temp_file):
                os.remove(temp_file)

    def test_builder_write(self):
        # find a temp file location
        temp = tempfile.TemporaryFile()

        # build it on live scene
        self.z.write(temp.name)

        self.temp_files.append(temp.name)

        # simply check if file exists, if it does it passes
        self.assertTrue(os.path.exists(temp.name))

    def test_scene_item_write(self):
        # loop through each scene item and write individually to see if they 
        # write
        bools = []  # to store if the files exist
        for item in self.z.get_scene_items():
            # for each scene item find a temp file
            temp = tempfile.TemporaryFile()
            item.write(temp.name)
            bools.append(os.path.exists(temp.name))
            self.temp_files.append(temp.name)

        # check to see if all files exist in one go
        self.assertTrue(all(bools))
