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
            'r_subtissue_1_zMaterial', 'l_tissue_1_zMaterial', 'l_cloth_1_zMaterial'
        ]
        cls.material_attrs = ["youngsModulus", "massDensity", "restScale"]

    def setUp(self):
        super(ZivaMaterialGenericTestCase, self).setUp()
        test_utils.build_generic_scene()
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
        self.check_build_restores_attr_values(self.builder, self.material_names, self.material_attrs)

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
