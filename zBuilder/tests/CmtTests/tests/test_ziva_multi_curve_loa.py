import maya.cmds as mc
import maya.mel as mm
import os
import logging
import sys

import zBuilder.zMaya as mz
import zBuilder.builders.ziva as zva
import zBuilder.tests.utils as utl
import zBuilder.utils as utility

from vfx_test_case import VfxTestCase


class ZivaMultiCurveLoaTestCase(VfxTestCase):
    @classmethod
    def setUpClass(cls):
        pass

    def setUp(self):
        super(ZivaMultiCurveLoaTestCase, self).setUp()
        # setup a scene with 2 curves on 1 zLineOfAction

        # create geometry
        mc.polySphere(name='bone')
        mc.setAttr('bone.translateY', 2)
        mc.polySphere(name='tissue')

        # create zTissue and zBone
        mc.select('tissue')
        mm.eval('ziva -t')

        mc.select('bone')
        mm.eval('ziva -b')

        # create an attachment, probably not needed
        mc.select('tissue', 'bone')
        mm.eval('ziva -a')

        # create teh fiber
        mc.select('tissue')
        fiber = mm.eval('ziva -f')[0]

        # create 2 curves on fiber and create a loa
        mc.select(fiber)
        curve1 = mm.eval('zLineOfActionUtil')[0]
        mc.select(fiber)
        curve2 = mm.eval('zLineOfActionUtil')[0]
        curve1 = curve1.replace('Shape', '')
        curve2 = curve2.replace('Shape', '')
        mc.select(fiber, curve1, curve2)
        mm.eval('ziva -loa')

        mc.select('zSolver1')

        self.builder = zva.Ziva()
        self.builder.retrieve_from_scene()

    def test_retrieve(self):

        loa = self.builder.get_scene_items(type_filter='zLineOfAction')[0]

        # loa.association should have 2 elements.
        self.assertTrue(len(loa.association) == 2)

    def test_build(self):
        mz.clean_scene()

        self.builder.build()

        # after it is built there should be 2 curves hooked up to loa
        curves = mc.listConnections('zLineOfAction1.curves')
        self.assertTrue(len(curves) == 2)

    def test_retrieve_connections_loa_selected(self):

        loa = self.builder.get_scene_items(type_filter='zLineOfAction')[0]

        # now retrieve
        mc.select(loa.name)
        builder = zva.Ziva()
        builder.retrieve_connections()
        builder.stats()
        print builder.get_scene_items()
        # should not be empty
        self.assertTrue(len(builder.get_scene_items()) > 0)

    def test_retrieve_connections_loa_selected_check(self):

        loa = self.builder.get_scene_items(type_filter='zLineOfAction')[0]

        # now retrieve
        mc.select(loa.name)
        builder = zva.Ziva()
        builder.retrieve_connections()

        # this should have grabbed the specific loa
        result = builder.get_scene_items(name_filter=loa.name)

        # result will have named loa
        self.assertTrue(len(result) == 1)
