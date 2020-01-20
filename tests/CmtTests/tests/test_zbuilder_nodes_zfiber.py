import os
import zBuilder.builders.ziva as zva
import tests.utils as test_utils
import zBuilder.utils as utils
import zBuilder.zMaya as mz
from maya import cmds

from vfx_test_case import VfxTestCase


class ZivaFiberGenericTestCase(VfxTestCase):
    @classmethod
    def setUpClass(cls):
        cls.fiber_names = ['r_subtissue_1_zFiber', 'l_tissue_1_zFiber']
        cls.fiber_attrs = ["strength", "contractionLimit", "excitation"]

    def setUp(self):
        super(ZivaFiberGenericTestCase, self).setUp()
        test_utils.build_generic_scene()
        self.builder = zva.Ziva()
        self.builder.retrieve_from_scene()

    def tearDown(self):
        if os.path.exists(self.temp_file_path):
            os.remove(self.temp_file_path)
        super(ZivaFiberGenericTestCase, self).tearDown()

    def check_retrieve_zfiber_looks_good(self, builder, expected_plugs):
        """Args:
            builder (builders.ziva.Ziva()): builder object
            expected_plugs (dict): A dict of expected attribute/value pairs.
                                   {'zFiber1.strength':1, ...}.
                                   If None/empty/False, then attributes are taken from zBuilder
                                   and values are taken from the scene.
                                   Test fails if zBuilder is missing any of the keys
                                   or has any keys with different values.
        """
        self.check_retrieve_looks_good(builder, expected_plugs, self.fiber_names, "zFiber")

    def test_retrieve(self):
        self.check_retrieve_zfiber_looks_good(self.builder, {})

    def test_retrieve_connections(self):
        builder = zva.Ziva()
        builder.retrieve_connections()
        self.check_retrieve_zfiber_looks_good(builder, {})

    def test_build_restores_attr_values(self):
        self.check_build_restores_attr_values(self.builder, self.fiber_names, self.fiber_attrs)

    def test_remove(self):
        self.check_ziva_remove_command(self.builder, "zFiber")

    def test_builder_has_same_fiber_nodes_after_writing_to_disk(self):
        builder = self.get_builder_after_writing_and_reading_from_disk(self.builder)
        self.check_retrieve_zfiber_looks_good(builder, {})

    def test_build(self):
        builder = self.get_builder_after_clean_and_build(self.builder)
        self.check_retrieve_zfiber_looks_good(builder, {})

    def test_build_from_file(self):
        builder = self.get_builder_after_write_and_retrieve_from_file(self.builder)
        self.check_retrieve_zfiber_looks_good(builder, {})

    def test_rename(self):
        ## SETUP
        cmds.select("r_tissue_2")
        cmds.ziva(f=True)

        ## VERIFY
        # check if an item exists before renaming
        self.assertEqual(cmds.ls("r_tissue_2_zFiber"), [])

        ## ACT
        mz.rename_ziva_nodes()

        ## VERIFY
        self.assertEqual(len(cmds.ls("r_tissue_2_zFiber")), 1)

    def test_string_replace(self):
        ## VERIFY
        # check if an item exists before string_replace
        r_fiber = self.builder.get_scene_items(name_filter="l_tissue_1_zFiber")
        self.assertGreaterEqual(len(r_fiber), 1)

        ## ACT
        self.builder.string_replace("^l_", "r_")

        ## VERIFY
        r_fiber = self.builder.get_scene_items(name_filter="l_tissue_1_zFiber")
        self.assertEqual(r_fiber, [])

    def test_cut_paste(self):
        builder = self.get_builder_after_cut_paste("l_tissue_1", "l_tissue_1_zFiber")
        self.check_retrieve_zfiber_looks_good(builder, {})

    def test_copy_paste(self):
        builder = self.get_builder_after_copy_paste("l_tissue_1", "l_tissue_1_zFiber")
        self.check_retrieve_zfiber_looks_good(builder, {})

    def test_copy_paste_with_name_substitution(self):
        ## VERIFY
        # check if zFiber does not exist before making it
        self.assertEqual(cmds.ls("r_tissue_1_zFiber"), [])

        ## ACT
        cmds.select("l_tissue_1")
        utils.copy_paste_with_substitution("(^|_)l($|_)", "r")

        ## VERIFY
        self.assertEqual(len(cmds.ls("r_tissue_1_zFiber")), 1)
