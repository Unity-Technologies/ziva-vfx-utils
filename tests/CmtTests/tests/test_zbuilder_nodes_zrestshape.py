import maya.cmds as mc
import maya.mel as mm

import zBuilder.zMaya as mz
import zBuilder.builders.ziva as zva
import zBuilder.utils as utils

from vfx_test_case import VfxTestCase


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
