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


class ZivaBuildTestCase(VfxTestCase):
    @classmethod
    def setUpClass(cls):
        pass

    def setUp(self):
        super(ZivaBuildTestCase, self).setUp()

        # This builds the Zivas anatomical arm demo with no pop up dialog.
        utl.build_arm()

        # clear selection.  It should retrieve whole scene
        mc.select(cl=True)

        # use builder to retrieve from scene-----------------------------------
        self.z = zva.Ziva()
        self.z.retrieve_from_scene()

    def tearDown(self):
        super(ZivaBuildTestCase, self).tearDown()

    def test_retrieve_selected(self):
        # This builds the Zivas anatomical arm demo with no pop up dialog.
        utl.build_arm()

        # select a muscle geo
        mc.select('r_bicep_muscle')

        # use builder to retrieve from scene-----------------------------------
        z = zva.Ziva()
        z.retrieve_from_scene_selection()

        # build
        z.build()

        # check amount of zTissue and zTet.  Should be 1 of each
        items = z.get_scene_items(type_filter=['zTet', 'zTissue'])

        self.assertTrue(len(items) == 2)

    def test_retrieve_from_scene(self):
        zAttachments = mc.ls(type='zAttachment')
        # remove ziva nodes from scene so all we have left is geo
        mz.clean_scene()

        # build
        self.z.build()
        self.assertTrue(len(zAttachments) == len(mc.ls(type='zAttachment')))

    def test_string_replace(self):
        # remove ziva nodes from scene so all we have left is geo
        mz.clean_scene()

        mc.rename('r_bicep_muscle', 'r_biceps_muscle')
        self.z.string_replace('r_bicep_muscle', 'r_biceps_muscle')

        # build
        self.z.build()

        # after its build check scene for the proper named zTissue
        self.assertSceneHasNodes(['r_biceps_muscle_zTissue'])

    def test_build_permissive_false(self):
        # remove ziva nodes from scene so all we have left is geo
        mz.clean_scene()

        # now lets delete bicep to see how build handles it
        mc.delete('r_bicep_muscle')

        with self.assertRaises(StandardError):
            self.z.build(permissive=False)

    def test_bad_mesh_error(self):
        # make sure we get an error if mesh fails a check
        mz.clean_scene()

        # now lets scale muscle to make it invalid
        mc.setAttr('r_bicep_muscle.scaleX', l=False)
        mc.setAttr('r_bicep_muscle.scaleY', l=False)
        mc.setAttr('r_bicep_muscle.scaleX', 0)
        mc.setAttr('r_bicep_muscle.scaleY', 0)

        # now build should raise a standard error
        with self.assertRaises(StandardError):
            self.z.build()

    def test_tissue_attrs_not_updating(self):
        # this tests an issue of zTissues not updating attributes if the
        # tissue is not created.  In that case it would skip over the attr
        # changing.  As seen in VFXACT-89

        # to test this lets change an attribute on a tissue
        mc.setAttr("r_bicep_muscle_zTissue.inertialDamping", .5)

        # now build from the zBuilder
        self.z.build()

        # if the attribute is 0 we know it worked
        self.assertTrue(
            mc.getAttr("r_bicep_muscle_zTissue.inertialDamping") == 0)
