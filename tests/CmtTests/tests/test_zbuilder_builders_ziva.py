from maya import cmds
from maya import mel
import os
import logging
import sys

import zBuilder.zMaya as mz
import zBuilder.builders.ziva as zva
import tests.utils as test_utils
import zBuilder.utils as utils

from vfx_test_case import VfxTestCase
from zBuilder.builders.ziva import SolverDisabler

from maya import cmds


class ZivaMirrorSelectedTestCase(VfxTestCase):
    def setUp(self):
        super(ZivaMirrorSelectedTestCase, self).setUp()
        test_utils.build_generic_scene(scene_name='mirror_example.ma')

    def test_mirror_selection(self):
        cmds.select('l_arm_muscles')

        builder = zva.Ziva()
        builder.retrieve_from_scene_selection()
        # before we build we want to mirror just the center geo
        for item in builder.get_scene_items(name_filter='c_chest_bone'):
            item.mirror()

        # and we want to interpolate any map associated with the center geo
        for item in builder.get_scene_items(type_filter='map'):
            if 'c_chest_bone' in item._mesh:
                item.interpolate()

        # now a simple string replace
        builder.string_replace('^l_', 'r_')

        builder.build()

        self.assertSceneHasNodes(['zAttachment2', 'zMaterial3', 'zMaterial4'])
        


class ZivaMirrorTestCase(VfxTestCase):
    def setUp(self):
        super(ZivaMirrorTestCase, self).setUp()
        # Build a basic setup
        test_utils.build_mirror_sample_geo()
        test_utils.ziva_mirror_sample_geo()

        cmds.select(cl=True)

        # use builder to retrieve from scene
        self.z = zva.Ziva()
        self.z.retrieve_from_scene()

        # string replace
        self.z.string_replace('^r_', 'l_')

    def test_mirror_existing_scene(self):
        # # build it on live scene
        self.z.build()

        # check if left muscle is connected to zGeo
        self.assertTrue(len(cmds.listConnections('l_muscle', type='zGeo')))


class ZivaBuildTestCase(VfxTestCase):
    def setUp(self):
        super(ZivaBuildTestCase, self).setUp()

        # This builds the Zivas anatomical arm demo with no pop up dialog.
        test_utils.build_anatomical_arm_with_no_popup()

        # clear selection.  It should retrieve whole scene
        cmds.select(cl=True)

        # use builder to retrieve from scene-----------------------------------
        self.builder = zva.Ziva()
        self.builder.retrieve_from_scene()

    def test_retrieve_selected(self):
        # This builds the Zivas anatomical arm demo with no pop up dialog.
        test_utils.build_anatomical_arm_with_no_popup()

        # select a muscle geo
        cmds.select('r_bicep_muscle')

        # use builder to retrieve from scene-----------------------------------
        z = zva.Ziva()
        z.retrieve_from_scene_selection()

        # build
        z.build()

        # check amount of zTissue and zTet.  Should be 1 of each
        items = z.get_scene_items(type_filter=['zTet', 'zTissue'])

        self.assertEqual(len(items), 2)

    def test_retrieve_from_scene(self):
        zAttachments = cmds.ls(type='zAttachment')
        # remove ziva nodes from scene so all we have left is geo
        mz.clean_scene()

        # build
        self.builder.build()
        self.assertTrue(len(zAttachments) == len(cmds.ls(type='zAttachment')))

    def test_string_replace(self):
        # remove ziva nodes from scene so all we have left is geo
        mz.clean_scene()

        cmds.rename('r_bicep_muscle', 'r_biceps_muscle')
        self.builder.string_replace('r_bicep_muscle', 'r_biceps_muscle')

        # build
        self.builder.build()

        # after its build check scene for the proper named zTissue
        self.assertSceneHasNodes(['r_biceps_muscle_zTissue'])

    def test_build_permissive_false(self):
        # remove ziva nodes from scene so all we have left is geo
        mz.clean_scene()

        # now lets delete bicep to see how build handles it
        cmds.delete('r_bicep_muscle')

        with self.assertRaises(Exception):
            self.builder.build(permissive=False)

    def test_bad_mesh_error(self):
        # make sure we get an error if mesh fails a check
        mz.clean_scene()

        # now lets scale muscle to make it invalid
        cmds.setAttr('r_bicep_muscle.scaleX', l=False)
        cmds.setAttr('r_bicep_muscle.scaleY', l=False)
        cmds.setAttr('r_bicep_muscle.scaleX', 0)
        cmds.setAttr('r_bicep_muscle.scaleY', 0)

        with self.assertRaises(Exception):
            self.builder.build()

    def test_tissue_attrs_not_updating(self):
        # this tests an issue of zTissues not updating attributes if the
        # tissue is not created.  In that case it would skip over the attr
        # changing.  As seen in VFXACT-89

        # to test this lets change an attribute on a tissue
        cmds.setAttr("r_bicep_muscle_zTissue.inertialDamping", .5)

        # now build from the zBuilder
        self.builder.build()

        # if the attribute is 0 we know it worked
        self.assertTrue(cmds.getAttr("r_bicep_muscle_zTissue.inertialDamping") == 0)

    def test_getting_intermediate_shape(self):
        # this tests getting intermediate shape if there is one instead
        # of deformed shape

        # This builds the Zivas anatomical arm demo with no pop up dialog.
        test_utils.build_anatomical_arm_with_no_popup()

        # capture point position of first vert at rest
        rest_point_position = cmds.pointPosition('r_bicep_muscle.vtx[0]')

        # advance a few frames to change it
        cmds.currentTime(2)
        cmds.currentTime(3)

        # retrrieve from scene
        cmds.select('zSolver1')
        import zBuilder.builders.ziva as zva
        z = zva.Ziva()
        z.retrieve_from_scene()

        # now check value of vert position.  Should be saem as rest
        mesh = z.get_scene_items(type_filter='mesh', name_filter='r_bicep_muscle')[0]

        print(mesh.get_point_list()[0], rest_point_position)

        self.assertTrue(mesh.get_point_list()[0] == rest_point_position)

    def test_retrieve_connections_single(self):
        # this tests retrieve_connections on a a full setup where you have 1 tissue
        # selected with no attachments.  This was a bug fix.  The expected result
        # is there should be 1 tissue in object.  What was happening is it was
        # getting whole scene.

        # the arm is built in scene so all we need to do is create sphere and retrieve
        sph = cmds.polySphere()
        mel.eval('ziva -t')
        cmds.select(sph)

        z = zva.Ziva()
        z.retrieve_connections()

        self.assertEqual(1, len(z.get_scene_items(type_filter='zTissue')))


class ZivaSolverDisableTestCase(VfxTestCase):
    def test_enable_connected(self):
        # build scene and connect the enable to something
        test_utils.build_generic_scene()
        loc = cmds.spaceLocator()[0]
        cmds.connectAttr('{}.translateX'.format(loc), 'zSolver1.enable')

        retrieved_builder = test_utils.retrieve_builder_from_scene()

        retrieved_builder.build()

        current_connection = cmds.listConnections('zSolver1.enable', plugs=True)[0]
        self.assertEqual(current_connection, '{}.translateX'.format(loc))

    def test_SolverDisabler_class_connected(self):
        mel.eval('ziva -s')
        loc = cmds.spaceLocator()[0]
        cmds.setAttr('{}.translateX'.format(loc), 1)  # So that enable will start off being True!
        cmds.connectAttr('{}.translateX'.format(loc), 'zSolver1.enable')

        self.assertTrue(cmds.getAttr('zSolver1.enable'))
        self.assertTrue(cmds.listConnections('zSolver1.enable'))

        with SolverDisabler('zSolver1'):
            self.assertFalse(cmds.getAttr('zSolver1.enable'))
            self.assertFalse(cmds.listConnections('zSolver1.enable'))

        self.assertTrue(cmds.getAttr('zSolver1.enable'))
        self.assertTrue(cmds.listConnections('zSolver1.enable'))

    def test_SolverDisabler_class_not_connected(self):
        mel.eval('ziva -s')
        self.assertTrue(cmds.getAttr('zSolver1.enable'))
        with SolverDisabler('zSolver1'):
            self.assertFalse(cmds.getAttr('zSolver1.enable'))
        self.assertTrue(cmds.getAttr('zSolver1.enable'))

    def test_SolverDisabler_does_not_enable_a_disabled_solver(self):
        mel.eval('ziva -s')
        cmds.setAttr('zSolver1.enable', False)
        with SolverDisabler('zSolver1'):
            self.assertFalse(cmds.getAttr('zSolver1.enable'))
        self.assertFalse(cmds.getAttr('zSolver1.enable'))
