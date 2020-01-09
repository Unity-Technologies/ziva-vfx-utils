from maya import cmds
from maya import mel
import os
import zBuilder.builders.ziva as zva
import tests.utils as test_utils
import zBuilder.utils as utils
import zBuilder.zMaya as mz

from vfx_test_case import VfxTestCase


class ZivaClothTestCase(VfxTestCase):
    @classmethod
    def setUpClass(cls):
        cls.cloth_names = ["c_cloth_1_zCloth", "l_cloth_1_zCloth"]
        cls.cloth_attrs = ["inertialDamping", "pressureEnvelope", "collisions"]

    def setUp(self):
        super(ZivaClothTestCase, self).setUp()
        test_utils.build_generic_scene()
        self.builder = zva.Ziva()
        self.builder.retrieve_from_scene()

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
        builder = self.get_builder_after_write_and_retrieve_from_file(self.builder)
        self.check_retrieve_zcloth_looks_good(builder, {})

    def test_rename(self):
        ## SETUP
        mc.select("r_cloth_1")
        mc.ziva(c=True)

        ## VERIFY
        # check if an item exists before renaming
        self.assertEqual(mc.ls("r_cloth_1_zCloth"), [])

        ## ACT
        mz.rename_ziva_nodes()

        ## VERIFY
        self.assertEqual(len(mc.ls("r_cloth_1_zCloth")), 1)

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
        self.assertEqual(mc.ls("r_cloth_1_zCloth"), [])

        ## ACT
        mc.select("l_cloth_1")
        utils.copy_paste_with_substitution("(^|_)l($|_)", "r")

        ## VERIFY
        self.assertEqual(len(mc.ls("r_cloth_1_zCloth")), 1)

    def test_mirror_cloth(self):
        # this is a test for a bug in VFXACT-120
        # if you mirror a zCloth and it is not named with a side prefix it would get
        # confused and assert.  This should not assert now and result in a mirror
        # there should be 2 zCloth nodes in scene when done.
        
        # build a simple cloth scene
        a_cloth = mc.polySphere(n='l_arm')[0]
        b_cloth = mc.polySphere(n='r_arm')[0]
        cmds.setAttr(b_cloth + '.translateX', -10)
        cmds.select('l_arm')
        mel.eval('ziva -c')
        
        cmds.select('l_arm')
        cmds.setAttr(a_cloth + '.translateX', 10)

        z = zva.Ziva()

        z.retrieve_from_scene_selection()
        z.string_replace('l_', 'r_')
        z.build()

        self.assertSceneHasNodes(['zCloth1', 'zCloth2'])
