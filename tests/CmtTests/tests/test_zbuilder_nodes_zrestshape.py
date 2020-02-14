import os
import zBuilder.builders.ziva as zva
import tests.utils as test_utils
import zBuilder.utils as utils
import zBuilder.zMaya as mz
from maya import cmds
from maya import mel

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


class ZivaRestShapeGenericTestCase(VfxTestCase):
    @classmethod
    def setUpClass(cls):
        cls.rest_shape_names = ['l_tissue_1_zRestShape']
        cls.rest_shape_attrs = ["surfacePenalty"]

    def setUp(self):
        super(ZivaRestShapeGenericTestCase, self).setUp()
        test_utils.load_scene(scene_name="generic_tissue.ma")
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
        builder = self.get_builder_after_write_and_retrieve_from_file(self.builder)
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
        mz.rename_ziva_nodes()

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
        utils.copy_paste_with_substitution("(^|_)l($|_)", "r")

        ## VERIFY
        self.assertEqual(len(cmds.ls("r_tissue_1_zRestShape")), 1)


class ZivaRestShapeMirrorTestCase(VfxTestCase):
    """This Class tests a specific type of "mirroring" so there are some assumptions made

    - geometry has an identifiable qualifier, in this case it is l_ and r_
    - Both sides geometry are in the scene
    - One side has Ziva VFX nodes and other side does not, in this case l_ has Ziva nodes

    """

    def setUp(self):
        super(ZivaRestShapeMirrorTestCase, self).setUp()
        test_utils.load_scene(scene_name='mirror_example.ma')
        self.builder = zva.Ziva()
        self.builder.retrieve_from_scene()

        # gather info
        self.type_ = 'zRestShape'
        self.scene_items_retrieved = self.builder.get_scene_items(type_filter=self.type_)
        self.l_item_geo = [
            x for x in self.scene_items_retrieved if x.association[0].startswith('l_')
        ]

    def test_builder_change_with_string_replace(self):
        # VERIFY
        self.compare_builder_nodes_with_scene_nodes(self.builder)
        self.compare_builder_attrs_with_scene_attrs(self.builder)

        self.check_node_association_amount_equal(self.scene_items_retrieved, 'r_', 0)
        self.check_node_association_amount_not_equal(self.scene_items_retrieved, 'l_', 0)

        # ACT
        self.builder.string_replace("^l_", "r_")

        # VERIFY
        self.check_node_association_amount_equal(self.scene_items_retrieved, 'l_', 0)
        self.check_node_association_amount_equal(self.scene_items_retrieved, 'r_',
                                                 len(self.l_item_geo))

    def test_builder_build_with_string_replace(self):
        self.compare_builder_nodes_with_scene_nodes(self.builder)
        self.compare_builder_attrs_with_scene_attrs(self.builder)

        # ACT
        self.builder.string_replace("^l_", "r_")
        self.builder.build()

        # VERIFY
        self.compare_builder_nodes_with_scene_nodes(self.builder)
        self.compare_builder_attrs_with_scene_attrs(self.builder)

        self.compare_maps_in_builder_with_scene(self.scene_items_retrieved)

        # checking the actual restshapes got hooked up in maya
        for item in self.builder.get_scene_items(type_filter='zRestShape'):
            connections = cmds.listConnections('{}.target'.format(item.name))
            connections_long_name = cmds.ls(connections, long=True)

            self.assertEqual(item.targets, connections_long_name)
