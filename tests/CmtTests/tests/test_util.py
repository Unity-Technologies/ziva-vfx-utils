import maya.cmds as mc
import maya.mel as mel
import os
import logging
import sys

import zBuilder.zMaya as mz
import zBuilder.builders.ziva as zva
import tests.utils as utl
import zBuilder.utils as utility
import zBuilder.builder as bld
from vfx_test_case import VfxTestCase


class UtilTestCase(VfxTestCase):
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
        utl.build_anatomical_arm_with_no_popup()

        mc.select(cl=True)

        mc.duplicate('r_bicep_muscle', name='dupe')
        mc.polySmooth('dupe')
        mc.select('r_bicep_muscle', 'dupe')

        utility.copy_paste()
        mc.ls(type='zAttachment')
        self.assertSceneHasNodes(['dupe_r_radius_bone'])

    def test_builder_factories_false(self):
        # this tests the case in builder_factory if a class was not found.
        # it should raise a StandardError

        with self.assertRaises(StandardError):
            obj = bld.builder_factory('class_not_found_error')

    #
    # commenting out this test until it is needed. Please keep.
    #
    # def test_builder_factories(self):
    #     # this tests the builder_factory to make sure it finds known classes.
    #     class_names = [
    #                   'Ziva',
    #                   'Attributes',
    #                   'Constraints',
    #                   'Deformers',
    #                   'DeltaMush',
    #                   'Fields',
    #                   'Selection',
    #                   'SkinCluster',
    #                   ]

    #     bools = []
    #     for class_name in class_names:
    #         obj = bld.builder_factory(class_name)
    #         bools.append(class_name in str(obj.__class__))
    #     self.assertTrue(all(bools))
