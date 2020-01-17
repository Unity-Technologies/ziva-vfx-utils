import os
import zBuilder.builders.ziva as zva
import tests.utils as test_utils
import zBuilder.utils as utils
import zBuilder.zMaya as mz
from maya import cmds

from vfx_test_case import VfxTestCase


class ZivaAttachmentGenericTestCase(VfxTestCase):
    @classmethod
    def setUpClass(cls):
        cls.attachment_names = [
            'r_tissue_2__c_bone_1_zAttachment', 'c_tissue_3__c_bone_2_zAttachment',
            'c_cloth_1__c_bone_1_zAttachment', 'l_tissue_1__c_bone_1_zAttachment',
            'l_tissue_1__l_bone_1_zAttachment', 'l_cloth_1__c_bone_1_zAttachment',
            'l_cloth_1__c_tissue_3_zAttachment'
        ]

        cls.attachment_attrs = ["attachmentMode", "stiffness", "show"]

    def setUp(self):
        super(ZivaAttachmentGenericTestCase, self).setUp()
        test_utils.build_generic_scene()
        self.builder = zva.Ziva()
        self.builder.retrieve_from_scene()

    def tearDown(self):
        if os.path.exists(self.temp_file_path):
            os.remove(self.temp_file_path)
        super(ZivaAttachmentGenericTestCase, self).tearDown()

    def check_retrieve_zattachment_looks_good(self, builder, expected_plugs):
        """Args:
            builder (builders.ziva.Ziva()): builder object
            expected_plugs (dict): A dict of expected attribute/value pairs.
                                   {'zAttachment1.stiffness':1, ...}.
                                   If None/empty/False, then attributes are taken from zBuilder
                                   and values are taken from the scene.
                                   Test fails if zBuilder is missing any of the keys
                                   or has any keys with different values.
        """
        self.check_retrieve_looks_good(builder, expected_plugs, self.attachment_names, "zAttachment")

    def test_retrieve(self):
        self.check_retrieve_zattachment_looks_good(self.builder, {})

    def test_retrieve_connections(self):
        builder = zva.Ziva()
        builder.retrieve_connections()
        self.check_retrieve_zattachment_looks_good(builder, {})

    def test_build_restores_attr_values(self):
        self.check_build_restores_attr_values(self.builder, self.attachment_names, self.attachment_attrs)

    def test_remove(self):
        self.check_ziva_remove_command(self.builder, "zAttachment")

    def test_builder_has_same_attachment_nodes_after_writing_to_disk(self):
        builder = self.get_builder_after_writing_and_reading_from_disk(self.builder)
        self.check_retrieve_zattachment_looks_good(builder, {})

    def test_build(self):
        builder = self.get_builder_after_clean_and_build(self.builder)
        self.check_retrieve_zattachment_looks_good(builder, {})

    def test_build_from_file(self):
        builder = self.get_builder_after_write_and_retrieve_from_file(self.builder)
        self.check_retrieve_zattachment_looks_good(builder, {})

    def test_rename(self):
        ## SETUP
        cmds.select("r_tissue_1")
        cmds.ziva(t=True)
        cmds.select(["r_tissue_1", "c_bone_1"])
        cmds.ziva(a=True)

        ## VERIFY
        # check if an item exists before renaming
        self.assertEqual(cmds.ls("r_tissue_1__c_bone_1_zAttachment"), [])

        ## ACT
        mz.rename_ziva_nodes([])

        ## VERIFY
        self.assertEqual(len(cmds.ls("r_tissue_1__c_bone_1_zAttachment")), 1)

    def test_string_replace(self):
        ## VERIFY
        # check if an item exists before string_replace
        r_attachment = self.builder.get_scene_items(name_filter="r_tissue_2__c_bone_1_zAttachment")
        self.assertGreaterEqual(len(r_attachment), 1)

        ## ACT
        self.builder.string_replace("^r_", "l_")

        ## VERIFY
        r_attachment = self.builder.get_scene_items(name_filter="r_tissue_2__c_bone_1_zAttachment")
        self.assertEqual(r_attachment, [])

    def test_cut_paste(self):
        builder = self.get_builder_after_cut_paste("l_tissue_1", "l_tissue_1__l_bone_1_zAttachment")
        self.check_retrieve_zattachment_looks_good(builder, {})

    def test_copy_paste(self):
        builder = self.get_builder_after_copy_paste("l_tissue_1", "l_tissue_1__l_bone_1_zAttachment")
        self.check_retrieve_zattachment_looks_good(builder, {})

    def test_copy_paste_with_name_substitution(self):
        ## VERIFY
        # check if zAttachment does not exist before making it
        self.assertEqual(cmds.ls("r_tissue_1__c_bone_1_zAttachment"), [])

        ## ACT
        cmds.select("l_tissue_1")
        utils.copy_paste_with_substitution("(^|_)l($|_)", "r")

        ## VERIFY
        self.assertEqual(len(cmds.ls("l_tissue_1__c_bone_1_zAttachment")), 1)
