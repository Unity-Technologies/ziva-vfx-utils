import os
import zBuilder.builders.ziva as zva
import tests.utils as test_utils
import zBuilder.utils as utils
import zBuilder.zMaya as mz
from maya import cmds

from vfx_test_case import VfxTestCase, ZivaMirrorTestCase, ZivaUpdateTestCase

NODE_TYPE = 'zBone'


class ZivaBoneGenericTestCase(VfxTestCase):
    @classmethod
    def setUpClass(cls):
        cls.bone_names = ["c_bone_1_zBone", "c_bone_2_zBone", "l_bone_1_zBone"]
        cls.bone_attrs = ["contactSliding", "contactStiffnessExp", "collisions"]

    def setUp(self):
        super(ZivaBoneGenericTestCase, self).setUp()
        test_utils.load_scene(scene_name="generic_bone.ma")
        self.builder = zva.Ziva()
        self.builder.retrieve_from_scene()

    def tearDown(self):
        if os.path.exists(self.temp_file_path):
            os.remove(self.temp_file_path)
        super(ZivaBoneGenericTestCase, self).tearDown()

    def check_retrieve_zbone_looks_good(self, builder, expected_plugs):
        """Args:
            builder (builders.ziva.Ziva()): builder object
            expected_plugs (dict): A dict of expected attribute/value pairs.
                                   {'zBone1.collisions':True, ...}.
                                   If None/empty/False, then attributes are taken from zBuilder
                                   and values are taken from the scene.
                                   Test fails if zBuilder is missing any of the keys
                                   or has any keys with different values.
        """
        self.check_retrieve_looks_good(builder, expected_plugs, self.bone_names, "zBone")

    def test_retrieve(self):
        self.check_retrieve_zbone_looks_good(self.builder, {})

    def test_retrieve_connections(self):
        builder = zva.Ziva()
        builder.retrieve_connections()
        self.check_retrieve_zbone_looks_good(builder, {})

    def test_build_restores_attr_values(self):
        self.check_build_restores_attr_values(self.builder, self.bone_names, self.bone_attrs)

    def test_remove(self):
        self.check_ziva_remove_command(self.builder, "zBone")

    def test_builder_has_same_tissue_nodes_after_writing_to_disk(self):
        builder = self.get_builder_after_writing_and_reading_from_disk(self.builder)
        self.check_retrieve_zbone_looks_good(builder, {})

    def test_build(self):
        builder = self.get_builder_after_clean_and_build(self.builder)
        self.check_retrieve_zbone_looks_good(builder, {})

    def test_build_from_file(self):
        builder = self.get_builder_after_write_and_retrieve_from_file(self.builder)
        self.check_retrieve_zbone_looks_good(builder, {})

    def test_rename(self):
        ## SETUP
        cmds.select("r_bone_1")
        cmds.ziva(b=True)

        ## VERIFY
        # check if an item exists before renaming
        self.assertEqual(cmds.ls("r_bone_1_zBone"), [])

        ## ACT
        mz.rename_ziva_nodes([])

        ## VERIFY
        self.assertEqual(len(cmds.ls("r_bone_1_zBone")), 1)

    def test_string_replace(self):
        ## VERIFY
        # check if an item exists before string_replace
        r_tissue = self.builder.get_scene_items(name_filter="l_bone_1_zBone")
        self.assertGreaterEqual(len(r_tissue), 1)

        ## ACT
        self.builder.string_replace("^l_", "r_")

        ## VERIFY
        r_tissue = self.builder.get_scene_items(name_filter="l_bone_1_zBone")
        self.assertEqual(r_tissue, [])

    def test_cut_paste(self):
        builder = self.get_builder_after_cut_paste("l_bone_1", "l_bone_1_zBone")
        self.check_retrieve_zbone_looks_good(builder, {})

    def test_copy_paste(self):
        builder = self.get_builder_after_copy_paste("l_bone_1", "l_bone_1_zBone")
        self.check_retrieve_zbone_looks_good(builder, {})

    def test_copy_paste_with_name_substitution(self):
        ## VERIFY
        # check if zBone does not exist before making it
        self.assertEqual(cmds.ls("r_bone_1_zBone"), [])

        ## ACT
        cmds.select("l_bone_1")
        utils.copy_paste_with_substitution("(^|_)l($|_)", "r")

        ## VERIFY
        self.assertEqual(len(cmds.ls("r_bone_1_zBone")), 1)


class ZivaBoneMirrorTestCase(ZivaMirrorTestCase):
    """This Class tests a specific type of "mirroring" so there are some assumptions made

    - geometry has an identifiable qualifier, in this case it is l_ and r_
    - Both sides geometry are in the scene
    - One side has Ziva VFX nodes and other side does not, in this case l_ has Ziva nodes
    - Ziva nodes are named default like so: zBone1, zBone2, zBone3

    """

    def setUp(self):
        super(ZivaBoneMirrorTestCase, self).setUp()

        test_utils.load_scene(scene_name='mirror_example.ma')
        self.builder = zva.Ziva()
        self.builder.retrieve_from_scene()
        # gather info
        self.scene_items_retrieved = self.builder.get_scene_items(type_filter=NODE_TYPE)
        self.l_item_geo = [
            x for x in self.scene_items_retrieved if x.association[0].startswith('l_')
        ]

    def test_builder_change_with_string_replace(self):
        super(ZivaBoneMirrorTestCase, self).builder_change_with_string_replace()

    def test_builder_build_with_string_replace(self):
        super(ZivaBoneMirrorTestCase, self).builder_build_with_string_replace()


class ZivaBoneUpdateTestCase(ZivaUpdateTestCase):
    """This Class tests a specific type of "mirroring" so there are some assumptions made

    - geometry has an identifiable qualifier, in this case it is l_ and r_
    - Both sides geometry are in the scene
    - Both sides have Ziva nodes

    """

    def setUp(self):
        super(ZivaBoneUpdateTestCase, self).setUp()
        test_utils.load_scene(scene_name='mirror_example.ma')
        self.builder = zva.Ziva()
        self.builder.retrieve_from_scene()

        # VERIFY
        self.compare_builder_nodes_with_scene_nodes(self.builder)
        self.compare_builder_attrs_with_scene_attrs(self.builder)

        # gather info
        self.type_ = 'zAttachment'
        self.scene_items_retrieved = self.builder.get_scene_items(type_filter=self.type_)
        self.l_item_geo = [
            x.name for x in self.scene_items_retrieved if x.association[0].startswith('l_')
        ]
        cmds.select(self.l_item_geo)

        new_builder = zva.Ziva()
        new_builder.retrieve_from_scene()
        new_builder.string_replace("^l_", "r_")
        new_builder.build()

    def test_builder_change_with_string_replace(self):
        super(ZivaBoneUpdateTestCase, self).builder_change_with_string_replace()

    def test_builder_build_with_string_replace(self):
        super(ZivaBoneUpdateTestCase, self).builder_build_with_string_replace()
