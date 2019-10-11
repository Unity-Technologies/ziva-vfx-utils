import maya.cmds as mc
import maya.mel as mm
import os
import logging
import sys

import zBuilder.zMaya as mz
import zBuilder.builders.ziva as zva
import tests.utils as test_utils
import zBuilder.utils as utils

from vfx_test_case import VfxTestCase


class ZivaBuildTestCase(VfxTestCase):
    @classmethod
    def setUpClass(cls):
        pass

    def setUp(self):
        super(ZivaBuildTestCase, self).setUp()

        # This builds the Zivas anatomical arm demo with no pop up dialog.
        test_utils.build_anatomical_arm_with_no_popup()

        # clear selection.  It should retrieve whole scene
        mc.select(cl=True)

        # use builder to retrieve from scene-----------------------------------
        self.builder = zva.Ziva()
        self.builder.retrieve_from_scene()

    def tearDown(self):
        super(ZivaBuildTestCase, self).tearDown()

    def test_retrieve_selected(self):
        # This builds the Zivas anatomical arm demo with no pop up dialog.
        test_utils.build_anatomical_arm_with_no_popup()

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
        self.builder.build()
        self.assertTrue(len(zAttachments) == len(mc.ls(type='zAttachment')))

    def test_string_replace(self):
        # remove ziva nodes from scene so all we have left is geo
        mz.clean_scene()

        mc.rename('r_bicep_muscle', 'r_biceps_muscle')
        self.builder.string_replace('r_bicep_muscle', 'r_biceps_muscle')

        # build
        self.builder.build()

        # after its build check scene for the proper named zTissue
        self.assertSceneHasNodes(['r_biceps_muscle_zTissue'])

    def test_build_permissive_false(self):
        # remove ziva nodes from scene so all we have left is geo
        mz.clean_scene()

        # now lets delete bicep to see how build handles it
        mc.delete('r_bicep_muscle')

        with self.assertRaises(StandardError):
            self.builder.build(permissive=False)

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
            self.builder.build()

    def test_tissue_attrs_not_updating(self):
        # this tests an issue of zTissues not updating attributes if the
        # tissue is not created.  In that case it would skip over the attr
        # changing.  As seen in VFXACT-89

        # to test this lets change an attribute on a tissue
        mc.setAttr("r_bicep_muscle_zTissue.inertialDamping", .5)

        # now build from the zBuilder
        self.builder.build()

        # if the attribute is 0 we know it worked
        self.assertTrue(mc.getAttr("r_bicep_muscle_zTissue.inertialDamping") == 0)

    def test_getting_intermediate_shape(self):
        # this tests getting intermediate shape if there is one instead
        # of deformed shape

        # This builds the Zivas anatomical arm demo with no pop up dialog.
        test_utils.build_anatomical_arm_with_no_popup()

        # capture point position of first vert at rest
        rest_point_position = mc.pointPosition('r_bicep_muscle.vtx[0]')

        # advance a few frames to change it
        mc.currentTime(2)
        mc.currentTime(3)

        # retrrieve from scene
        mc.select('zSolver1')
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
        sph = mc.polySphere()
        mm.eval('ziva -t')
        mc.select(sph)

        z = zva.Ziva()
        z.retrieve_connections()

        self.assertEqual(1, len(z.get_scene_items(type_filter='zTissue')))

    def test_retrieving_invalid_mobjects(self):
        # remove ziva nodes from scene so all we have left is geo
        mz.clean_scene()

        mobjects = []
        # return mobjects from items, lets do all zAttachments
        # since the scene has been cleaned this should return no mobjects
        for item in self.builder.get_scene_items(type_filter='zAttachment'):
            mobjects.append(item.mobject)

        # this list should all be None
        self.assertTrue(all(x is None for x in mobjects))

    def test_retrieving_serialize_mobject(self):
        # testing retrieving, serializing then checking mobjects

        type_filter = ['zAttachment', 'zTissue', 'zBone', 'zSolverTransform', 'zSolver', 'zFiber']

        mobjects = []
        # loop through and serialize
        for item in self.builder.get_scene_items(type_filter=type_filter):
            item.serialize()
            mobjects.append(item)

        # this list should all be None
        self.assertTrue(all(x is not None for x in mobjects))

    def test_retrieving_writing_mobject_string(self):
        # testing retrieving, building then checking mobjects

        type_filter = ['zAttachment', 'zTissue', 'zBone', 'zSolverTransform', 'zSolver', 'zFiber']

        mobjects = []
        for item in self.builder.get_scene_items(type_filter=type_filter):
            mobjects.append(type(item.mobject))

        # this list should all be None
        self.assertTrue(all(x is not 'str' for x in mobjects))


class ZivaRestShapeTestCase(VfxTestCase):
    @classmethod
    def setUpClass(cls):
        pass

    def setUp(self):
        super(ZivaRestShapeTestCase, self).setUp()

        # setup simple scene
        # build simple zRestShape scene
        self.tissue_mesh = mc.polySphere(name='tissue_mesh')[0]
        target_a = mc.polySphere(name='a')[0]
        target_b = mc.polySphere(name='b')[0]

        mc.select(self.tissue_mesh)
        mm.eval('ziva -t')
        mc.select(self.tissue_mesh, target_a, target_b)
        mm.eval('zRestShape -a')

    def test_retrieve(self):

        mc.select(cl=True)

        # use builder to retrieve from scene-----------------------------------
        builder = zva.Ziva()
        builder.retrieve_from_scene()

        # check amount of zTissue and zTet.  Should be 1 of each
        items = builder.get_scene_items(type_filter=['zRestShape'])

        self.assertTrue(len(items) == 1)

    def test_retrieve_build_clean(self):

        mc.select(cl=True)

        # use builder to retrieve from scene-----------------------------------
        builder = zva.Ziva()
        builder.retrieve_from_scene()

        mz.clean_scene()

        builder.build()

        self.assertTrue(mc.objExists('zRestShape1'))

    def test_retrieve_selection(self):

        mc.select(self.tissue_mesh)

        # use builder to retrieve from scene-----------------------------------
        builder = zva.Ziva()
        builder.retrieve_from_scene_selection()

        # check amount of zRestShapes.  Should be 1
        items = builder.get_scene_items(type_filter=['zRestShape'])

        self.assertEqual(len(items), 1)

    def test_copy_non_restshape_selected(self):
        # make sure VFXACT-347 stays functional
        # create a tissue with no restShapes then select that and copy
        non_rest_tissue = mc.polySphere(name='c')[0]
        mc.select(non_rest_tissue)
        mm.eval('ziva -t')

        mc.select(non_rest_tissue)

        self.assertTrue(utils.rig_copy())

    def test_restshape_selected_with_unwanted_restshapes(self):
        # make sure VFXACT-358 stays functional
        tis2 = mc.polySphere(name='tissue_mesh2')[0]
        target_c = mc.polySphere(name='c')[0]

        mc.select(tis2)
        mm.eval('ziva -t')
        mc.select(tis2, target_c)
        mm.eval('zRestShape -a')

        # now we have 2 tissue and 2 restShapes.
        # select one and check contents of zBuilder.
        mc.select(tis2)

        builder = zva.Ziva()
        builder.retrieve_from_scene_selection()

        # there are 2 restShape nodes in scene, we should have captured 1
        items = builder.get_scene_items(type_filter=['zRestShape'])

        self.assertEqual(len(items), 1)
