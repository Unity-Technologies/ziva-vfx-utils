from maya import cmds
from maya import mel

import zBuilder.zMaya as mz
import zBuilder.builders.ziva as zva
import zBuilder.utils as utils

from vfx_test_case import VfxTestCase


class ZivaRestShapeTestCase(VfxTestCase):
    def setUp(self):
        super(ZivaRestShapeTestCase, self).setUp()

        # setup simple scene
        # build simple zRestShape scene
        self.tissue_mesh = cmds.polySphere(name='tissue_mesh')[0]
        target_a = cmds.polySphere(name='a')[0]
        target_b = cmds.polySphere(name='b')[0]

        cmds.select(self.tissue_mesh)
        mel.eval('ziva -t')
        cmds.select(self.tissue_mesh, target_a, target_b)
        mel.eval('zRestShape -a')

    def test_retrieve(self):

        cmds.select(cl=True)

        # use builder to retrieve from scene-----------------------------------
        builder = zva.Ziva()
        builder.retrieve_from_scene()

        # check amount of zTissue and zTet.  Should be 1 of each
        items = builder.get_scene_items(type_filter=['zRestShape'])

        self.assertTrue(len(items) == 1)

    def test_retrieve_build_clean(self):

        cmds.select(cl=True)

        # use builder to retrieve from scene-----------------------------------
        builder = zva.Ziva()
        builder.retrieve_from_scene()

        mz.clean_scene()

        builder.build()

        self.assertTrue(cmds.objExists('zRestShape1'))

    def test_retrieve_selection(self):

        cmds.select(self.tissue_mesh)

        # use builder to retrieve from scene-----------------------------------
        builder = zva.Ziva()
        builder.retrieve_from_scene_selection()

        # check amount of zRestShapes.  Should be 1
        items = builder.get_scene_items(type_filter=['zRestShape'])

        self.assertEqual(len(items), 1)

    def test_copy_non_restshape_selected(self):
        # make sure VFXACT-347 stays functional
        # create a tissue with no restShapes then select that and copy
        non_rest_tissue = cmds.polySphere(name='c')[0]
        cmds.select(non_rest_tissue)
        mel.eval('ziva -t')

        cmds.select(non_rest_tissue)

        self.assertTrue(utils.rig_copy())

    def test_restshape_selected_with_unwanted_restshapes(self):
        # make sure VFXACT-358 stays functional
        tis2 = cmds.polySphere(name='tissue_mesh2')[0]
        target_c = cmds.polySphere(name='c')[0]

        cmds.select(tis2)
        mel.eval('ziva -t')
        cmds.select(tis2, target_c)
        mel.eval('zRestShape -a')

        # now we have 2 tissue and 2 restShapes.
        # select one and check contents of zBuilder.
        cmds.select(tis2)

        builder = zva.Ziva()
        builder.retrieve_from_scene_selection()

        # there are 2 restShape nodes in scene, we should have captured 1
        items = builder.get_scene_items(type_filter=['zRestShape'])

        self.assertEqual(len(items), 1)
