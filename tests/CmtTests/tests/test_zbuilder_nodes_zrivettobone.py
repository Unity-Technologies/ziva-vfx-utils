import os
import zBuilder.builders.ziva as zva
import tests.utils as test_utils
import zBuilder.utils as utils
import zBuilder.zMaya as mz
from maya import cmds
from maya import mel

from vfx_test_case import VfxTestCase


class ZivaRivetToBoneGenericTestCase(VfxTestCase):
    @classmethod
    def setUpClass(cls):
        cls.rivet_to_bone_names = [
            "l_loa_curve_zRivetToBone1", "l_loa_curve_zRivetToBone2"
        ]
        cls.rivet_to_bone_attrs = ["envelope"]

    def setUp(self):
        super(ZivaRivetToBoneGenericTestCase, self).setUp()
        test_utils.build_generic_scene()
        self.builder = zva.Ziva()
        self.builder.retrieve_from_scene()

    def tearDown(self):
        if os.path.exists(self.temp_file_path):
            os.remove(self.temp_file_path)
        super(ZivaRivetToBoneGenericTestCase, self).tearDown()

    def check_retrieve_rivet_to_bone_looks_good(self, builder, expected_plugs):
        """Args:
            builder (builders.ziva.Ziva()): builder object
            expected_plugs (dict): A dict of expected attribute/value pairs.
                                   {'zRivetToBone1.envelope':1, ...}.
                                   If None/empty/False, then attributes are taken from zBuilder
                                   and values are taken from the scene.
                                   Test fails if zBuilder is missing any of the keys
                                   or has any keys with different values.
        """
        self.check_retrieve_looks_good(builder, expected_plugs, self.rivet_to_bone_names, "zRivetToBone")

    def test_retrieve(self):
        self.check_retrieve_rivet_to_bone_looks_good(self.builder, {})

    def test_retrieve_connections(self):
        builder = zva.Ziva()
        builder.retrieve_connections()
        self.check_retrieve_rivet_to_bone_looks_good(builder, {})

    def test_build_restores_attr_values(self):
        self.check_build_restores_attr_values(self.builder, self.rivet_to_bone_names, self.rivet_to_bone_attrs)

    def test_builder_has_same_rivet_to_bone_nodes_after_writing_to_disk(self):
        builder = self.get_builder_after_writing_and_reading_from_disk(self.builder)
        self.check_retrieve_rivet_to_bone_looks_good(builder, {})

    def test_build(self):
        builder = self.get_builder_after_clean_and_build(self.builder)
        self.check_retrieve_rivet_to_bone_looks_good(builder, {})

    def test_build_from_file(self):
        builder = self.get_builder_after_write_and_retrieve_from_file(self.builder)
        self.check_retrieve_rivet_to_bone_looks_good(builder, {})

    def test_string_replace(self):
        ## VERIFY
        # check if an item exists before string_replace
        r_rivet_to_bone = self.builder.get_scene_items(name_filter="l_loa_curve_zRivetToBone1")
        self.assertGreaterEqual(len(r_rivet_to_bone), 1)

        ## ACT
        self.builder.string_replace("^l_", "r_")

        ## VERIFY
        r_rivet_to_bone = self.builder.get_scene_items(name_filter="l_loa_curve_zRivetToBone1")
        self.assertEqual(r_rivet_to_bone, [])

    def test_copy_paste_with_name_substitution(self):
        ## VERIFY
        # check if zRivetToBone does not exist before making it
        self.assertEqual(cmds.ls("r_loa_curve_zRivetToBone1"), [])

        ## ACT
        cmds.select("l_tissue_1")
        utils.copy_paste_with_substitution("(^|_)l($|_)", "r")

        ## VERIFY
        self.assertEqual(len(cmds.ls("r_loa_curve_zRivetToBone1")), 1)