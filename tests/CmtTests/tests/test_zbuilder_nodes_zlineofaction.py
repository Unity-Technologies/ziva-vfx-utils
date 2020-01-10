from maya import cmds
from maya import mel
import os
import logging
import sys

import zBuilder.zMaya as mz
import zBuilder.builders.ziva as zva

from vfx_test_case import VfxTestCase


class ZivaMultiCurveLoaTestCase(VfxTestCase):
    def setUp(self):
        super(ZivaMultiCurveLoaTestCase, self).setUp()
        # setup a scene with 2 curves on 1 zLineOfAction

        # create geometry
        cmds.polySphere(name='bone')
        cmds.setAttr('bone.translateY', 2)
        cmds.polySphere(name='tissue')

        # create zTissue and zBone
        cmds.select('tissue')
        mel.eval('ziva -t')

        cmds.select('bone')
        mel.eval('ziva -b')

        # create an attachment, probably not needed
        cmds.select('tissue', 'bone')
        mel.eval('ziva -a')

        # create teh fiber
        cmds.select('tissue')
        fiber = mel.eval('ziva -f')[0]

        # create 2 curves on fiber and create a loa
        cmds.select(fiber)
        curve1 = mel.eval('zLineOfActionUtil')[0]
        cmds.select(fiber)
        curve2 = mel.eval('zLineOfActionUtil')[0]
        curve1 = curve1.replace('Shape', '')
        curve2 = curve2.replace('Shape', '')
        cmds.select(fiber, curve1, curve2)
        mel.eval('ziva -loa')

        cmds.select('zSolver1')

        self.builder = zva.Ziva()
        self.builder.retrieve_from_scene()

    def test_retrieve(self):

        loa = self.builder.get_scene_items(type_filter='zLineOfAction')[0]

        # loa.association should have 2 elements.
        self.assertEqual(len(loa.association), 2)

    def test_build(self):
        mz.clean_scene()

        self.builder.build()

        # after it is built there should be 2 curves hooked up to loa
        curves = cmds.listConnections('zLineOfAction1.curves')
        self.assertEqual(len(curves), 2)

    def test_retrieve_connections_loa_selected(self):

        loa = self.builder.get_scene_items(type_filter='zLineOfAction')[0]

        # now retrieve
        cmds.select(loa.name)
        builder = zva.Ziva()
        builder.retrieve_connections()
        builder.stats()
        print(builder.get_scene_items())
        # should not be empty
        self.assertGreater(len(builder.get_scene_items()), 0)

    def test_retrieve_connections_loa_selected_check(self):

        loa = self.builder.get_scene_items(type_filter='zLineOfAction')[0]

        # now retrieve
        cmds.select(loa.name)
        builder = zva.Ziva()
        builder.retrieve_connections()

        # this should have grabbed the specific loa
        result = builder.get_scene_items(name_filter=loa.name)

        # result will have named loa
        self.assertEqual(len(result), 1)
