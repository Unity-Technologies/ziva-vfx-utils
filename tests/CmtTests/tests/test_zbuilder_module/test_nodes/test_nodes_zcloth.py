import os
import zBuilder.builders.ziva as zva

from maya import cmds
from vfx_test_case import (VfxTestCase, ZivaMirrorTestCase, ZivaMirrorNiceNameTestCase,
                           ZivaUpdateTestCase, ZivaUpdateNiceNameTestCase)
from tests.utils import load_scene
from zBuilder.commands import rename_ziva_nodes, copy_paste_with_substitution
from zBuilder.nodes.ziva.zCloth import ClothNode


class ZivaClothTestCase(VfxTestCase):

    @classmethod
    def setUpClass(cls):
        cls.cloth_names = ["c_cloth_1_zCloth", "l_cloth_1_zCloth"]
        cls.cloth_attrs = ["inertialDamping", "pressureEnvelope", "collisions"]

    def setUp(self):
        super(ZivaClothTestCase, self).setUp()
        load_scene("generic_cloth.ma")
        self.builder = zva.Ziva()
        self.builder.retrieve_from_scene()

    def tearDown(self):
        if os.path.exists(self.temp_file_path):
            os.remove(self.temp_file_path)
        super(ZivaClothTestCase, self).tearDown()

    def tearDown(self):
        if os.path.exists(self.temp_file_path):
            os.remove(self.temp_file_path)
        super(ZivaClothTestCase, self).tearDown()

    def check_retrieve_zcloth_looks_good(self, builder, expected_plugs):
        """Args:
            builder (builders.ziva.Ziva()): builder object
            expected_plugs (dict): A dict of expected attribute/value pairs.
                                   {'zCloth1.collisions':True, ...}.
                                   If None/empty/False, then attributes are taken from zBuilder
                                   and values are taken from the scene.
                                   Test fails if zBuilder is missing any of the keys
                                   or has any keys with different values.
        """
        self.check_retrieve_looks_good(builder, expected_plugs, self.cloth_names, "zCloth")

    def test_retrieve(self):
        self.check_retrieve_zcloth_looks_good(self.builder, {})

    def test_retrieve_connections(self):
        builder = zva.Ziva()
        builder.retrieve_connections()
        self.check_retrieve_zcloth_looks_good(builder, {})

    def test_build_restores_attr_values(self):
        self.check_build_restores_attr_values(self.builder, self.cloth_names, self.cloth_attrs)

    def test_remove(self):
        self.check_ziva_remove_command(self.builder, "zCloth")

    def test_builder_has_same_cloth_nodes_after_writing_to_disk(self):
        builder = self.get_builder_after_writing_and_reading_from_disk(self.builder)
        self.check_retrieve_zcloth_looks_good(builder, {})

    def test_build(self):
        builder = self.get_builder_after_clean_and_build(self.builder)
        self.check_retrieve_zcloth_looks_good(builder, {})

    def test_build_from_file(self):
        builder = self.get_builder_after_write_and_read(self.builder)
        self.check_retrieve_zcloth_looks_good(builder, {})

    def test_rename(self):
        ## SETUP
        cmds.select("r_cloth_1")
        cmds.ziva(c=True)

        ## VERIFY
        # check if an item exists before renaming
        self.assertEqual(cmds.ls("r_cloth_1_zCloth"), [])

        ## ACT
        rename_ziva_nodes()

        ## VERIFY
        self.assertEqual(len(cmds.ls("r_cloth_1_zCloth")), 1)

    def test_string_replace(self):
        ## VERIFY
        # check if an item exists before string_replace
        l_cloth = self.builder.get_scene_items(name_filter="l_cloth_1_zCloth")
        self.assertGreaterEqual(len(l_cloth), 1)

        ## ACT
        self.builder.string_replace("^l_", "r_")

        ## VERIFY
        l_cloth = self.builder.get_scene_items(name_filter="l_cloth_1_zCloth")
        self.assertEqual(l_cloth, [])

    def test_cut_paste(self):
        builder = self.get_builder_after_cut_paste("l_cloth_1", "l_cloth_1_zCloth")
        self.check_retrieve_zcloth_looks_good(builder, {})

    def test_copy_paste(self):
        builder = self.get_builder_after_copy_paste("l_cloth_1", "l_cloth_1_zCloth")
        self.check_retrieve_zcloth_looks_good(builder, {})

    def test_copy_paste_with_name_substitution(self):
        ## VERIFY
        # check if zCloth does not exist before making it
        self.assertEqual(cmds.ls("r_cloth_1_zCloth"), [])

        ## ACT
        cmds.select("l_cloth_1")
        copy_paste_with_substitution("(^|_)l($|_)", "r")

        ## VERIFY
        self.assertEqual(len(cmds.ls("r_cloth_1_zCloth")), 1)

    def test_mirror_cloth(self):
        # this is a test for a bug in VFXACT-120
        # if you mirror a zCloth and it is not named with a side prefix it would get
        # confused and assert.  This should not assert now and result in a mirror
        # there should be 2 zCloth nodes in scene when done.

        # build a simple cloth scene
        a_cloth = cmds.polySphere(n='l_arm')[0]
        cmds.setAttr(a_cloth + '.translateX', 10)
        b_cloth = cmds.polySphere(n='r_arm')[0]
        cmds.setAttr(b_cloth + '.translateX', -10)
        cmds.select('l_arm')
        cmds.ziva(c=True)

        cmds.select('l_arm')

        z = zva.Ziva()

        z.retrieve_from_scene_selection()
        z.string_replace('l_', 'r_')
        z.build()

        self.assertSceneHasNodes(['zCloth1', 'zCloth2'])


class ZivaClothMirrorTestCase(ZivaMirrorTestCase):
    """This Class tests a specific type of "mirroring" so there are some assumptions made

    - geometry has an identifiable qualifier, in this case it is l_ and r_
    - Both sides geometry are in the scene
    - One side has Ziva VFX nodes and other side does not, in this case l_ has Ziva nodes
    - Ziva nodes are named default like so: zCloth1, zCloth2, zCloth3

    """

    def setUp(self):
        super(ZivaClothMirrorTestCase, self).setUp()

        load_scene('mirror_example.ma')
        self.builder = zva.Ziva()
        self.builder.retrieve_from_scene()
        # gather info
        self.scene_items_retrieved = self.builder.get_scene_items(type_filter=ClothNode.type)
        self.l_item_geo = [
            x for x in self.scene_items_retrieved if x.association[0].startswith('l_')
        ]

    def test_builder_change_with_string_replace(self):
        super(ZivaClothMirrorTestCase, self).builder_change_with_string_replace()

    def test_builder_build_with_string_replace(self):
        super(ZivaClothMirrorTestCase, self).builder_build_with_string_replace()


class ZivaClothUpdateNiceNameTestCase(ZivaUpdateNiceNameTestCase):
    """This Class tests a specific type of "mirroring" so there are some assumptions made

    - geometry has an identifiable qualifier, in this case it is l_ and r_
    - Both sides geometry are in the scene
    - Both sides have Ziva VFX nodes
    - The Ziva Nodes have a side identifier same as geo

    """

    def setUp(self):
        super(ZivaClothUpdateNiceNameTestCase, self).setUp()
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

        self.scene_items_retrieved = self.builder.get_scene_items(type_filter=ClothNode.type)
        self.l_item_geo = [
            x for x in self.scene_items_retrieved if x.association[0].startswith('l_')
        ]

    def test_builder_change_with_string_replace(self):
        super(ZivaClothUpdateNiceNameTestCase, self).builder_change_with_string_replace()

    def test_builder_build_with_string_replace(self):
        super(ZivaClothUpdateNiceNameTestCase, self).builder_build_with_string_replace()


class ZivaClothMirrorNiceNameTestCase(ZivaMirrorNiceNameTestCase):
    """This Class tests a specific type of "mirroring" so there are some assumptions made

    - geometry has an identifiable qualifier, in this case it is l_ and r_
    - Both sides geometry are in the scene
    - One side has Ziva VFX nodes and other side does not, in this case l_ has Ziva nodes

    """

    def setUp(self):
        super(ZivaClothMirrorNiceNameTestCase, self).setUp()
        # gather info

        # Bring in scene
        load_scene('mirror_example.ma')

        # force NICE NAMES
        rename_ziva_nodes()

        self.builder = zva.Ziva()
        self.builder.retrieve_from_scene()

        self.scene_items_retrieved = self.builder.get_scene_items(type_filter=ClothNode.type)
        self.l_item_geo = [
            x for x in self.scene_items_retrieved if x.association[0].startswith('l_')
        ]

    def test_builder_change_with_string_replace(self):
        super(ZivaClothMirrorNiceNameTestCase, self).builder_change_with_string_replace()

    def test_builder_build_with_string_replace(self):
        super(ZivaClothMirrorNiceNameTestCase, self).builder_build_with_string_replace()


class ZivaClothUpdateTestCase(ZivaUpdateTestCase):
    """This Class tests a specific type of "mirroring" so there are some assumptions made

    - geometry has an identifiable qualifier, in this case it is l_ and r_
    - Both sides geometry are in the scene
    - Both sides have Ziva nodes

    """

    def setUp(self):
        super(ZivaClothUpdateTestCase, self).setUp()
        load_scene('mirror_example.ma')
        self.builder = zva.Ziva()
        self.builder.retrieve_from_scene()

        # VERIFY
        self.compare_builder_nodes_with_scene_nodes(self.builder)
        self.compare_builder_attrs_with_scene_attrs(self.builder)

        # gather info
        self.scene_items_retrieved = self.builder.get_scene_items(type_filter=ClothNode.type)
        self.l_item_geo = [
            x.name for x in self.scene_items_retrieved if x.association[0].startswith('l_')
        ]
        cmds.select(self.l_item_geo)

        new_builder = zva.Ziva()
        new_builder.retrieve_from_scene()
        new_builder.string_replace("^l_", "r_")
        new_builder.build()

    def test_builder_change_with_string_replace(self):
        super(ZivaClothUpdateTestCase, self).builder_change_with_string_replace()

    def test_builder_build_with_string_replace(self):
        super(ZivaClothUpdateTestCase, self).builder_build_with_string_replace()
