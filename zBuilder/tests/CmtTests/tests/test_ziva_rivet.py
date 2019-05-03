import maya.cmds as mc
import maya.mel as mm
import os
import logging
import sys

import zBuilder.zMaya as mz
import zBuilder.builders.ziva as zva
import zBuilder.tests.utils as utl
import zBuilder.util as utility

from vfx_test_case import VfxTestCase


class ZivaRivetTestCase(VfxTestCase):

    @classmethod
    def setUpClass(cls):
        pass

    def setUp(self):
        super(ZivaRivetTestCase, self).setUp()

        # This builds the Zivas anatomical arm demo with no pop up dialog.
        utl.build_arm()

        # create l
        mc.select('r_tricepsLong_muscle')
        crv = mm.eval('zLineOfActionUtil')[0]
        mc.select(crv+'.cv[0]', 'r_humerus_bone')
        riv1 = mm.eval('zRivetToBone')
        mc.select(crv+'.cv[1]', 'r_scapula_bone')
        riv2 = mm.eval('zRivetToBone')
        mc.select('r_tricepsLong_muscle', crv)
        mm.eval('ziva -loa;')

    def tearDown(self):
        super(ZivaRivetTestCase, self).tearDown()

    def test_retrieve_rivet_scene(self):
        # use builder to retrieve from scene-----------------------------------
        mc.select(cl=True)
        z = zva.Ziva()
        z.retrieve_from_scene()

        # check that 2 rivets are in zBuilder
        rivets = z.get_scene_items(type_filter='zRivetToBone')
        self.assertTrue(len(rivets) == 2)

    def test_retrieve_rivet_selection(self):
        # use builder to retrieve from scene-----------------------------------
        mc.select('r_tricepsLong_muscle')
        z = zva.Ziva()
        z.retrieve_from_scene_selection()

        # check that 2 rivets are in zBuilder
        rivets = z.get_scene_items(type_filter='zRivetToBone')
        self.assertTrue(len(rivets) == 2)
        
    def test_retrieve_rivet_selection_none(self):
        # use builder to retrieve from scene-----------------------------------
        mc.select('r_bicep_muscle')
        z = zva.Ziva()
        z.retrieve_from_scene_selection()

        # check that 2 rivets are in zBuilder
        rivets = z.get_scene_items(type_filter='zRivetToBone')
        self.assertTrue(len(rivets) == 0)
        
    def test_build_rivet(self):
        # use builder to retrieve from scene-----------------------------------
        mc.select('r_tricepsLong_muscle')
        z = zva.Ziva()
        z.retrieve_from_scene()

        mz.clean_scene()

        z.build()

        # should be 2 in scene
        self.assertTrue(len(mc.ls(type='zRivetToBone')) == 2)

    def test_retrieve_rivet_scene_multiple_cvs(self):
        # create a rivetToBone driving 2 cv's
        mc.select('r_bicep_muscle')
        crv = mm.eval('zLineOfActionUtil')[0]
        mc.select(crv+'.cv[0]', crv+'.cv[1]', 'r_humerus_bone')
        riv2 = mm.eval('zRivetToBone')
        mc.select('r_bicep_muscle', crv)
        mm.eval('ziva -loa;')

        mc.select(cl=True)
        z = zva.Ziva()
        z.retrieve_from_scene()

        # check that 3 rivets are in zBuilder
        rivets = z.get_scene_items(type_filter='zRivetToBone')
        self.assertTrue(len(rivets) == 3)

    def test_build_rivet_multiple_cvs(self):
        # create a rivetToBone driving 2 cv's
        mc.select('r_bicep_muscle')
        crv = mm.eval('zLineOfActionUtil')[0]
        mc.select(crv+'.cv[0]', crv+'.cv[1]', 'r_humerus_bone')
        riv2 = mm.eval('zRivetToBone')
        mc.select('r_bicep_muscle', crv)
        mm.eval('ziva -loa;')

        # use builder to retrieve from scene-----------------------------------
        mc.select(cl=True)
        z = zva.Ziva()
        z.retrieve_from_scene()

        mz.clean_scene()

        z.build()

        # should be 2 in scene
        self.assertTrue(len(mc.ls(type='zRivetToBone')) == 3)
