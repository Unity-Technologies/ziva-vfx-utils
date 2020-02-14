import os
import zBuilder.builders.ziva as zva
import tests.utils as test_utils
import zBuilder.utils as utils
import zBuilder.zMaya as mz

from maya import cmds

from vfx_test_case import VfxTestCase


class ZivaMaterialGenericTestCase(VfxTestCase):
    @classmethod
    def setUpClass(cls):
        cls.material_names = [
            'r_tissue_2_zMaterial', 'c_tissue_3_zMaterial', 'c_cloth_1_zMaterial',
            'r_subtissue_1_zMaterial', 'l_tissue_1_zMaterial', 'l_cloth_1_zMaterial',
            'l_tissue_1_zMaterial1'
        ]
        cls.material_attrs = ["youngsModulus", "massDensity", "restScale"]

    def setUp(self):
        super(ZivaMaterialGenericTestCase, self).setUp()
        test_utils.load_scene()
        self.builder = zva.Ziva()
        self.builder.retrieve_from_scene()

    def tearDown(self):
        if os.path.exists(self.temp_file_path):
            os.remove(self.temp_file_path)
        super(ZivaMaterialGenericTestCase, self).tearDown()

    def check_retrieve_zmaterial_looks_good(self, builder, expected_plugs):
        """Args:
            builder (builders.ziva.Ziva()): builder object
            expected_plugs (dict): A dict of expected attribute/value pairs.
                                   {'zMaterial1.massDensity':1060, ...}.
                                   If None/empty/False, then attributes are taken from zBuilder
                                   and values are taken from the scene.
                                   Test fails if zBuilder is missing any of the keys
                                   or has any keys with different values.
        """
        self.check_retrieve_looks_good(builder, expected_plugs, self.material_names, "zMaterial")

    def test_retrieve(self):
        self.check_retrieve_zmaterial_looks_good(self.builder, {})

    def test_retrieve_connections(self):
        builder = zva.Ziva()
        builder.retrieve_connections()
        self.check_retrieve_zmaterial_looks_good(builder, {})

    def test_build_restores_attr_values(self):
        self.check_build_restores_attr_values(self.builder, self.material_names,
                                              self.material_attrs)

    def test_remove(self):
        self.check_ziva_remove_command(self.builder, "zMaterial")

    def test_builder_has_same_material_nodes_after_writing_to_disk(self):
        builder = self.get_builder_after_writing_and_reading_from_disk(self.builder)
        self.check_retrieve_zmaterial_looks_good(builder, {})

    def test_build(self):
        builder = self.get_builder_after_clean_and_build(self.builder)
        self.check_retrieve_zmaterial_looks_good(builder, {})

    def test_build_from_file(self):
        builder = self.get_builder_after_write_and_retrieve_from_file(self.builder)
        self.check_retrieve_zmaterial_looks_good(builder, {})

    def test_rename(self):
        ## SETUP
        cmds.select("r_tissue_1")
        cmds.ziva(t=True)

        ## VERIFY
        # check if an item exists before renaming
        self.assertEqual(cmds.ls("r_tissue_1_zMaterial"), [])

        ## ACT
        mz.rename_ziva_nodes()

        ## VERIFY
        self.assertEqual(len(cmds.ls("r_tissue_1_zMaterial")), 1)

    def test_string_replace(self):
        ## VERIFY
        # check if an item exists before string_replace
        r_material = self.builder.get_scene_items(name_filter="r_tissue_2_zMaterial")
        self.assertGreaterEqual(len(r_material), 1)

        ## ACT
        self.builder.string_replace("^r_", "l_")

        ## VERIFY
        r_material = self.builder.get_scene_items(name_filter="r_tissue_2_zMaterial")
        self.assertEqual(r_material, [])

    def test_cut_paste(self):
        builder = self.get_builder_after_cut_paste("l_tissue_1", "l_tissue_1_zMaterial")
        self.check_retrieve_zmaterial_looks_good(builder, {})

    def test_copy_paste(self):
        builder = self.get_builder_after_copy_paste("l_tissue_1", "l_tissue_1_zMaterial")
        self.check_retrieve_zmaterial_looks_good(builder, {})

    def test_copy_paste_with_name_substitution(self):
        ## VERIFY
        # check if zMaterial does not exist before making it
        self.assertEqual(cmds.ls("r_tissue_1_zMaterial"), [])

        ## ACT
        cmds.select("l_tissue_1")
        utils.copy_paste_with_substitution("(^|_)l($|_)", "r")

        ## VERIFY
        self.assertEqual(len(cmds.ls("r_tissue_1_zMaterial")), 1)

    def test_weight_interpolation(self):
        weights = [
            1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0,
            1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0,
            1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0,
            1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0,
            1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0,
            0.9999990463256836, 0.0, 0.0, 0.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0,
            0.9999997019767761, 0.9843137264251709, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 0.0,
            0.0, 0.0, 0.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 1.0, 1.0, 1.0,
            1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 1.0, 1.0, 1.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0,
            1.0, 1.0, 1.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 1.0, 1.0, 1.0, 1.0, 0.0, 0.0, 0.0,
            0.0, 0.0, 1.0, 1.0, 1.0, 1.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 1.0, 1.0, 1.0, 1.0,
            0.0, 0.0, 0.0, 0.0, 5.460792067424336e-07, 1.0, 1.0, 1.0, 1.0, 1.0, 0.0, 0.0, 0.0, 0.0,
            0.0, 1.0, 1.0, 1.0, 1.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 1.0, 1.0, 1.0, 1.0, 0.0,
            0.0, 0.0, 0.0, 0.0, 1.0, 1.0, 1.0, 1.0, 1.0, 0.0, 0.0, 0.0, 0.0, 5.455602831716533e-07,
            1.0, 1.0, 1.0, 1.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 1.0, 1.0, 1.0, 1.0, 0.0, 0.0,
            0.0, 0.0, 0.0, 1.0, 1.0, 1.0, 1.0, 1.0, 0.0, 0.0, 0.0, 0.0, 4.76837158203125e-07, 1.0,
            1.0, 1.0, 1.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 1.0, 1.0, 1.0, 1.0, 0.0, 0.0, 0.0,
            2.980232238769531e-07, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 1.0,
            1.0, 1.0, 1.0, 0.9999991059303284, 0.0, 0.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0,
            0.0, 0.0, 0.05098072811961174, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0,
            1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0,
            1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0,
            1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0,
            1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0,
            1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 0.9999999403953552, 0.0, 0.0, 0.0, 0.0,
            2.0760269592301483e-07, 1.0, 1.0, 1.0, 1.0, 0.9999999403953552, 0.0, 0.0, 0.0, 0.0,
            6.661877449687381e-08, 1.0, 1.0, 1.0, 1.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 1.0, 1.0,
            1.0, 1.0, 0.0, 0.0, 0.0, 0.0, 3.372956314251496e-07, 1.0, 1.0, 1.0, 1.0, 1.0, 0.0, 0.0,
            0.0, 0.0, 0.0, 1.0, 1.0, 1.0, 1.0, 1.0, 0.0, 0.0, 0.0, 0.0, 3.4121126191166695e-07, 1.0,
            1.0, 1.0, 1.0, 0.9999999403953552, 0.0, 0.0, 0.0, 0.0, 2.130416163481641e-07, 1.0, 1.0,
            1.0, 1.0, 0.9999999403953552, 0.0, 0.0, 0.0, 0.0, 6.93431019271884e-08, 1.0, 1.0, 1.0,
            1.0, 1.0, 1.0, 1.0, 0.9921568632125854, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
            0.0, 0.0, 0.0, 0.0, 0.025490285828709602, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0,
            0.9921568036079407, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
            0.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
            0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.5, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0,
            0.9999997615814209, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
            0.0, 0.0, 1.0, 1.0, 1.0, 1.0
        ]

        self.builder.string_replace("l_tissue_1", "l_tissue_1_high")
        # Rest shape has to be removed from the build list because there is no rest shape for
        # l_tissue_1_high mesh in the scene
        rest_shape_item = self.builder.get_scene_items(name_filter="l_tissue_1_high_zRestShape")[0]
        self.builder.bundle.remove_scene_item(rest_shape_item)
        self.builder.string_replace("l_tissue_1_high_embedded_cube", "l_tissue_1_embedded_cube")
        self.check_map_interpolation(self.builder, "l_tissue_1_high_zMaterial1", weights, 0)


class ZivaMaterialMirrorTestCase(VfxTestCase):
    """This Class tests a specific type of "mirroring" so there are some assumptions made

    - geometry has an identifiable qualifier, in this case it is l_ and r_
    - Both sides geometry are in the scene
    - One side has Ziva VFX nodes and other side does not, in this case l_ has Ziva nodes

    """

    def setUp(self):
        super(ZivaMaterialMirrorTestCase, self).setUp()
        test_utils.load_scene(scene_name='mirror_example.ma')
        self.builder = zva.Ziva()
        self.builder.retrieve_from_scene()

        # gather info
        self.type_ = 'zMaterial'
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
