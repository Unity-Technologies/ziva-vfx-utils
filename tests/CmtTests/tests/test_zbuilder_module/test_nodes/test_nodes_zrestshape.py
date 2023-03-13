import os
import zBuilder.builders.ziva as zva

from maya import cmds
from vfx_test_case import (VfxTestCase, ZivaMirrorTestCase, ZivaMirrorNiceNameTestCase,
                           ZivaUpdateTestCase, ZivaUpdateNiceNameTestCase)
from tests.utils import load_scene
from zBuilder.commands import rename_ziva_nodes, copy_paste_with_substitution, rig_copy
from zBuilder.nodes.ziva.zRestShape import RestShapeNode


class ZivaRestShapeTestCase(VfxTestCase):

    def setUp(self):
        super(ZivaRestShapeTestCase, self).setUp()

        # setup simple scene
        # build simple zRestShape scene
        self.tissue_mesh = cmds.polySphere(name='tissue_mesh')[0]
        target_a = cmds.polySphere(name='a')[0]
        target_b = cmds.polySphere(name='b')[0]

        cmds.select(self.tissue_mesh)
        cmds.ziva(t=True)
        cmds.select(self.tissue_mesh, target_a, target_b)
        cmds.zRestShape(a=True)

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
        cmds.ziva(t=True)

        cmds.select(non_rest_tissue)

        self.assertTrue(rig_copy())

    def test_restshape_selected_with_unwanted_restshapes(self):
        # make sure VFXACT-358 stays functional
        tis2 = cmds.polySphere(name='tissue_mesh2')[0]
        target_c = cmds.polySphere(name='c')[0]

        cmds.select(tis2)
        cmds.ziva(t=True)
        cmds.select(tis2, target_c)
        cmds.zRestShape(a=True)

        # now we have 2 tissue and 2 restShapes.
        # select one and check contents of zBuilder.
        cmds.select(tis2)

        builder = zva.Ziva()
        builder.retrieve_from_scene_selection()

        # there are 2 restShape nodes in scene, we should have captured 1
        items = builder.get_scene_items(type_filter=['zRestShape'])

        self.assertEqual(len(items), 1)

    def test_retrieve_build_on_aliased_attributes(self):
        ## SETUP
        # change alias attributes
        cmds.setAttr("zRestShape1.a", 2)
        cmds.setAttr("zRestShape1.b", 0)

        ## ACT
        # store values
        cmds.select(cl=True)
        builder = zva.Ziva()
        builder.retrieve_from_scene()

        # change values and re-build
        cmds.setAttr("zRestShape1.a", 1)
        cmds.setAttr("zRestShape1.b", 1)
        builder.build()

        ## VERIFY

        self.assertEqual(cmds.getAttr("zRestShape1.a"), 2)
        self.assertEqual(cmds.getAttr("zRestShape1.b"), 0)


class ZivaRestShapeGenericTestCase(VfxTestCase):

    @classmethod
    def setUpClass(cls):
        cls.rest_shape_names = ['l_tissue_1_zRestShape']
        cls.rest_shape_attrs = ["surfacePenalty"]

    def setUp(self):
        super(ZivaRestShapeGenericTestCase, self).setUp()
        load_scene("generic_tissue.ma")
        self.builder = zva.Ziva()
        self.builder.retrieve_from_scene()

    def tearDown(self):
        if os.path.exists(self.temp_file_path):
            os.remove(self.temp_file_path)
        super(ZivaRestShapeGenericTestCase, self).tearDown()

    def check_retrieve_rest_shape_looks_good(self, builder, expected_plugs):
        """Args:
            builder (builders.ziva.Ziva()): builder object
            expected_plugs (dict): A dict of expected attribute/value pairs.
                                   {'zRestShape1.surfacePenalty':1, ...}.
                                   If None/empty/False, then attributes are taken from zBuilder
                                   and values are taken from the scene.
                                   Test fails if zBuilder is missing any of the keys
                                   or has any keys with different values.
        """
        self.check_retrieve_looks_good(builder, expected_plugs, self.rest_shape_names, "zRestShape")

    def test_retrieve(self):
        self.check_retrieve_rest_shape_looks_good(self.builder, {})

    def test_retrieve_connections(self):
        builder = zva.Ziva()
        builder.retrieve_connections()
        self.check_retrieve_rest_shape_looks_good(builder, {})

    def test_build_restores_attr_values(self):
        self.check_build_restores_attr_values(self.builder, self.rest_shape_names,
                                              self.rest_shape_attrs)

    def test_remove(self):
        self.check_ziva_remove_command(self.builder, "zRestShape")

    def test_builder_has_same_rest_shape_nodes_after_writing_to_disk(self):
        builder = self.get_builder_after_writing_and_reading_from_disk(self.builder)
        self.check_retrieve_rest_shape_looks_good(builder, {})

    def test_build(self):
        builder = self.get_builder_after_clean_and_build(self.builder)
        self.check_retrieve_rest_shape_looks_good(builder, {})

    def test_build_from_file(self):
        builder = self.get_builder_after_write_and_read(self.builder)
        self.check_retrieve_rest_shape_looks_good(builder, {})

    def test_rename(self):
        ## SETUP
        cmds.select("r_tissue_1")
        cmds.ziva(t=True)
        cmds.select(["r_tissue_1", "r_tissue_1_restShape"])
        cmds.zRestShape(a=True)

        ## VERIFY
        # check if an item exists before renaming
        self.assertEqual(cmds.ls("r_tissue_1_zRestShape"), [])

        ## ACT
        rename_ziva_nodes()

        ## VERIFY
        self.assertEqual(len(cmds.ls("r_tissue_1_zRestShape")), 1)

    def test_string_replace(self):
        ## VERIFY
        # check if an item exists before string_replace
        r_rest_shape = self.builder.get_scene_items(name_filter="l_tissue_1_zRestShape")
        self.assertGreaterEqual(len(r_rest_shape), 1)

        ## ACT
        self.builder.string_replace("^l_", "r_")

        ## VERIFY
        r_rest_shape = self.builder.get_scene_items(name_filter="l_tissue_1_zRestShape")
        self.assertEqual(r_rest_shape, [])

    def test_cut_paste(self):
        builder = self.get_builder_after_cut_paste("l_tissue_1", "l_tissue_1_zRestShape")
        self.check_retrieve_rest_shape_looks_good(builder, {})

    def test_copy_paste(self):
        builder = self.get_builder_after_copy_paste("l_tissue_1", "l_tissue_1_zRestShape")
        self.check_retrieve_rest_shape_looks_good(builder, {})

    def test_copy_paste_with_name_substitution(self):
        ## VERIFY
        # check if zRestShape does not exist before making it
        self.assertEqual(cmds.ls("r_tissue_1_zRestShape"), [])

        ## ACT
        cmds.select("l_tissue_1")
        copy_paste_with_substitution("(^|_)l($|_)", "r")

        ## VERIFY
        self.assertEqual(len(cmds.ls("r_tissue_1_zRestShape")), 1)


class ZivaRestShapeMirrorTestCase(ZivaMirrorTestCase):
    """This Class tests a specific type of "mirroring" so there are some assumptions made

    - geometry has an identifiable qualifier, in this case it is l_ and r_
    - Both sides geometry are in the scene
    - One side has Ziva VFX nodes and other side does not, in this case l_ has Ziva nodes
    - Ziva nodes are named default like so: zRestShape1, zRestShape2, zRestShape3

    """

    def setUp(self):
        super(ZivaRestShapeMirrorTestCase, self).setUp()

        load_scene('mirror_example.ma')
        self.builder = zva.Ziva()
        self.builder.retrieve_from_scene()
        # gather info
        self.scene_items_retrieved = self.builder.get_scene_items(type_filter=RestShapeNode.type)
        self.l_item_geo = [
            x for x in self.scene_items_retrieved if x.association[0].startswith('l_')
        ]

    def test_builder_change_with_string_replace(self):
        super(ZivaRestShapeMirrorTestCase, self).builder_change_with_string_replace()

    def test_builder_build_with_string_replace(self):
        super(ZivaRestShapeMirrorTestCase, self).builder_build_with_string_replace()


class ZivaTissueUpdateNiceNameTestCase(ZivaUpdateNiceNameTestCase):
    """This Class tests a specific type of "mirroring" so there are some assumptions made

    - geometry has an identifiable qualifier, in this case it is l_ and r_
    - Both sides geometry are in the scene
    - Both sides have Ziva VFX nodes
    - The Ziva Nodes have a side identifier same as geo

    """

    def setUp(self):
        super(ZivaTissueUpdateNiceNameTestCase, self).setUp()
        load_scene('mirror_example.ma')

        # NICE NAMES
        rename_ziva_nodes()

        # make FULL setup based on left
        builder = zva.Ziva()
        builder.retrieve_from_scene()
        builder.string_replace('^l_', 'r_')
        builder.build()

        # gather info
        cmds.select('l_armA_muscle_geo', 'l_armA_subtissue_geo')
        self.builder = zva.Ziva()
        self.builder.retrieve_from_scene_selection()

        self.scene_items_retrieved = self.builder.get_scene_items(type_filter=RestShapeNode.type)
        self.l_item_geo = [
            x for x in self.scene_items_retrieved if x.association[0].startswith('l_')
        ]

    def test_builder_change_with_string_replace(self):
        super(ZivaTissueUpdateNiceNameTestCase, self).builder_change_with_string_replace()

    def test_builder_build_with_string_replace(self):
        super(ZivaTissueUpdateNiceNameTestCase, self).builder_build_with_string_replace()


class ZivaRestShapeMirrorNiceNameTestCase(ZivaMirrorNiceNameTestCase):
    """This Class tests a specific type of "mirroring" so there are some assumptions made

    - geometry has an identifiable qualifier, in this case it is l_ and r_
    - Both sides geometry are in the scene
    - One side has Ziva VFX nodes and other side does not, in this case l_ has Ziva nodes

    """

    def setUp(self):
        super(ZivaRestShapeMirrorNiceNameTestCase, self).setUp()
        # gather info

        # Bring in scene
        load_scene('mirror_example.ma')

        # force NICE NAMES
        rename_ziva_nodes()

        self.builder = zva.Ziva()
        self.builder.retrieve_from_scene()

        self.scene_items_retrieved = self.builder.get_scene_items(type_filter=RestShapeNode.type)
        self.l_item_geo = [
            x for x in self.scene_items_retrieved if x.association[0].startswith('l_')
        ]

    def test_builder_change_with_string_replace(self):
        super(ZivaRestShapeMirrorNiceNameTestCase, self).builder_change_with_string_replace()

    def test_builder_build_with_string_replace(self):
        super(ZivaRestShapeMirrorNiceNameTestCase, self).builder_build_with_string_replace()


class ZivaRestShapeUpdateTestCase(ZivaUpdateTestCase):
    """This Class tests a specific type of "mirroring" so there are some assumptions made

    - geometry has an identifiable qualifier, in this case it is l_ and r_
    - Both sides geometry are in the scene
    - Both sides have Ziva nodes

    """

    def setUp(self):
        super(ZivaRestShapeUpdateTestCase, self).setUp()
        load_scene('mirror_example.ma')
        self.builder = zva.Ziva()
        self.builder.retrieve_from_scene()

        # VERIFY
        self.compare_builder_nodes_with_scene_nodes(self.builder)
        self.compare_builder_attrs_with_scene_attrs(self.builder)

        # gather info
        self.scene_items_retrieved = self.builder.get_scene_items(type_filter=RestShapeNode.type)
        self.l_item_geo = [
            x.name for x in self.scene_items_retrieved if x.association[0].startswith('l_')
        ]
        cmds.select(self.l_item_geo)

        new_builder = zva.Ziva()
        new_builder.retrieve_from_scene()
        new_builder.string_replace("^l_", "r_")
        new_builder.build()

    def test_builder_change_with_string_replace(self):
        super(ZivaRestShapeUpdateTestCase, self).builder_change_with_string_replace()

    def test_builder_build_with_string_replace(self):
        super(ZivaRestShapeUpdateTestCase, self).builder_build_with_string_replace()
