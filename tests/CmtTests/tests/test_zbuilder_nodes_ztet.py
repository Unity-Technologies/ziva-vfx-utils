import os
import zBuilder.builders.ziva as zva
import tests.utils as test_utils
import zBuilder.utils as utils
import zBuilder.zMaya as mz
from maya import cmds

from vfx_test_case import VfxTestCase


class ZivaTetGenericTestCase(VfxTestCase):
    @classmethod
    def setUpClass(cls):
        cls.tet_names = [
            "r_tissue_2_zTet", "c_tissue_3_zTet", "r_subtissue_1_zTet", "l_tissue_1_zTet"
        ]
        cls.tet_attrs = ["tetSize", "fillInterior", "maxResolution"]

    def setUp(self):
        super(ZivaTetGenericTestCase, self).setUp()
        test_utils.load_scene(scene_name="generic_tissue.ma")
        self.builder = zva.Ziva()
        self.builder.retrieve_from_scene()

    def tearDown(self):
        if os.path.exists(self.temp_file_path):
            os.remove(self.temp_file_path)
        super(ZivaTetGenericTestCase, self).tearDown()

    def check_retrieve_ztet_looks_good(self, builder, expected_plugs):
        """Args:
            builder (builders.ziva.Ziva()): builder object
            expected_plugs (dict): A dict of expected attribute/value pairs.
                                   {'zTet1.tetSize':1, ...}.
                                   If None/empty/False, then attributes are taken from zBuilder
                                   and values are taken from the scene.
                                   Test fails if zBuilder is missing any of the keys
                                   or has any keys with different values.
        """
        self.check_retrieve_looks_good(builder, expected_plugs, self.tet_names, "zTet")

    def test_retrieve(self):
        self.check_retrieve_ztet_looks_good(self.builder, {})

    def test_retrieve_connections(self):
        builder = zva.Ziva()
        builder.retrieve_connections()
        self.check_retrieve_ztet_looks_good(builder, {})

    def test_build_restores_attr_values(self):
        self.check_build_restores_attr_values(self.builder, self.tet_names, self.tet_attrs)

    def test_remove(self):
        self.check_ziva_remove_command(self.builder, "zTet")

    def test_builder_has_same_tet_nodes_after_writing_to_disk(self):
        builder = self.get_builder_after_writing_and_reading_from_disk(self.builder)
        self.check_retrieve_ztet_looks_good(builder, {})

    def test_build(self):
        builder = self.get_builder_after_clean_and_build(self.builder)
        self.check_retrieve_ztet_looks_good(builder, {})

    def test_build_from_file(self):
        builder = self.get_builder_after_write_and_retrieve_from_file(self.builder)
        self.check_retrieve_ztet_looks_good(builder, {})

    def test_rename(self):
        ## SETUP
        cmds.select("r_tissue_1")
        cmds.ziva(t=True)

        ## VERIFY
        # check if an item exists before renaming
        self.assertEqual(cmds.ls("r_tissue_1_zTet"), [])

        ## ACT
        mz.rename_ziva_nodes()

        ## VERIFY
        self.assertEqual(len(cmds.ls("r_tissue_1_zTet")), 1)

    def test_string_replace(self):
        ## VERIFY
        # check if an item exists before string_replace
        r_tet = self.builder.get_scene_items(name_filter="r_tissue_2_zTet")
        self.assertGreaterEqual(len(r_tet), 1)

        ## ACT
        self.builder.string_replace("^r_", "l_")

        ## VERIFY
        r_tet = self.builder.get_scene_items(name_filter="r_tissue_2_zTet")
        self.assertEqual(r_tet, [])

    def test_cut_paste(self):
        builder = self.get_builder_after_cut_paste("l_tissue_1", "l_tissue_1_zTet")
        self.check_retrieve_ztet_looks_good(builder, {})

    def test_copy_paste(self):
        builder = self.get_builder_after_copy_paste("l_tissue_1", "l_tissue_1_zTet")
        self.check_retrieve_ztet_looks_good(builder, {})

    def test_copy_paste_with_name_substitution(self):
        ## VERIFY
        # check if zTet does not exist before making it
        self.assertEqual(cmds.ls("r_tissue_1_zTet"), [])

        ## ACT
        cmds.select("l_tissue_1")
        utils.copy_paste_with_substitution("(^|_)l($|_)", "r")

        ## VERIFY
        self.assertEqual(len(cmds.ls("r_tissue_1_zTet")), 1)


class ZivaTetMirrorTestCase(VfxTestCase):
    """This Class tests a specific type of "mirroring" so there are some assumptions made

    - geometry has an identifiable qualifier, in this case it is l_ and r_
    - Both sides geometry are in the scene
    - One side has Ziva VFX nodes and other side does not, in this case l_ has Ziva nodes

    """

    def setUp(self):
        super(ZivaTetMirrorTestCase, self).setUp()
        test_utils.load_scene(scene_name='mirror_example.ma')
        self.builder = zva.Ziva()
        self.builder.retrieve_from_scene()

        # gather info
        self.type_ = 'zTet'
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
        self.compare_builder_maps_with_scene_maps(self.builder)


