import os
import zBuilder.builders.ziva as zva
import tests.utils as test_utils
import zBuilder.utils as utils
import zBuilder.zMaya as mz
import maya.OpenMaya as om
import maya.cmds as mc

from vfx_test_case import VfxTestCase, attr_values_from_scene, attr_values_from_zbuilder_nodes


class ZivaBoneGenericTestCase(VfxTestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp_file_path = test_utils.get_tmp_file_location()
        cls.bone_names = [
            "c_bone_1_zBone", "c_bone_2_zBone", "l_bone_1_zBone"
        ]
        cls.bone_attrs = ["contactSliding", "contactStiffnessExp", "collisions"]

    def setUp(self):
        super(ZivaBoneGenericTestCase, self).setUp()
        test_utils.build_generic_scene()
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
        bone_nodes = builder.get_scene_items(type_filter="zBone")

        self.assertItemsEqual(self.bone_names, [x.name for x in bone_nodes])

        for node in bone_nodes:
            self.assertEqual(node.type, "zBone")
            self.assertIsInstance(node.mobject, om.MObject)

        zbuilder_plugs = attr_values_from_zbuilder_nodes(bone_nodes)
        expected_plugs = expected_plugs or attr_values_from_scene(zbuilder_plugs.keys())
        self.assertGreaterEqual(zbuilder_plugs, expected_plugs)

    def test_retrieve(self):
        self.check_retrieve_zbone_looks_good(self.builder, {})

    def test_build_restores_attr_values(self):
        plug_names = {
            '{}.{}'.format(geo, attr)
            for geo in self.bone_names for attr in self.bone_attrs
        }
        attrs_before = attr_values_from_scene(plug_names)

        # remove all Ziva nodes from the scene and build them
        mz.clean_scene()
        self.builder.build()

        attrs_after = attr_values_from_scene(plug_names)
        self.assertEqual(attrs_before, attrs_after)

    def test_remove(self):
        ## SETUP
        tissue_nodes = self.builder.get_scene_items(type_filter="zBone")
        # clear selection
        mc.select(cl=True)
        for tissue in tissue_nodes:
            mc.select(tissue.long_association, add=True)

        ## ACT
        mc.ziva(rm=True)

        ## VERIFY
        mc.select(cl=True)
        builder = zva.Ziva()
        builder.retrieve_from_scene()
        tissue_nodes = builder.get_scene_items(type_filter="zBone")
        self.assertEqual(tissue_nodes, [])

    def test_builder_has_same_tissue_nodes_after_writing_to_disk(self):
        self.builder.write(self.temp_file_path)
        self.assertTrue(os.path.exists(self.temp_file_path))

        builder = zva.Ziva()
        builder.retrieve_from_file(self.temp_file_path)
        self.check_retrieve_zbone_looks_good(builder, {})

    def test_build(self):
        ## SETUP
        mz.clean_scene()

        ## ACT
        self.builder.build()

        ## VERIFY
        builder = zva.Ziva()
        builder.retrieve_from_scene()
        self.check_retrieve_zbone_looks_good(builder, {})

    def test_build_from_file(self):
        ## SETUP
        self.builder.write(self.temp_file_path)
        mz.clean_scene()

        ## ACT
        builder = zva.Ziva()
        builder.retrieve_from_file(self.temp_file_path)
        builder.build()

        ## VERIFY
        builder = zva.Ziva()
        builder.retrieve_from_scene()
        self.check_retrieve_zbone_looks_good(builder, {})

    def test_rename(self):
        ## SETUP
        mc.select("r_bone_1")
        mc.ziva(b=True)

        ## VERIFY
        # check if an item exists before renaming
        self.assertEqual(mc.ls("r_bone_1_zBone"), [])

        ## ACT
        mz.rename_ziva_nodes([])

        ## VERIFY
        self.assertEqual(len(mc.ls("r_bone_1_zBone")), 1)

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
        ## ACT
        mc.select("l_bone_1")
        utils.rig_cut()

        ## VERIFY
        self.assertEqual(mc.ls("l_bone_1_zBone"), [])

        ## ACT
        mc.select("l_bone_1")
        utils.rig_paste()

        ## VERIFY
        builder = zva.Ziva()
        builder.retrieve_from_scene()
        self.check_retrieve_zbone_looks_good(builder, {})

    def test_copy_paste(self):
        ## ACT
        # check if zBone exists
        self.assertEqual(len(mc.ls("l_bone_1_zBone")), 1)
        mc.select("l_bone_1")
        utils.rig_copy()

        ## VERIFY
        # check that zBone was not removed
        self.assertEqual(len(mc.ls("l_bone_1_zBone")), 1)

        ## SETUP
        mc.ziva(rm=True)

        ## ACT
        mc.select("l_bone_1")
        utils.rig_paste()

        ## VERIFY
        builder = zva.Ziva()
        builder.retrieve_from_scene()
        self.check_retrieve_zbone_looks_good(builder, {})

    def test_copy_paste_with_name_substitution(self):
        ## VERIFY
        # check if zBone does not exist before making it
        self.assertEqual(mc.ls("r_bone_1_zBone"), [])

        ## ACT
        mc.select("l_bone_1")
        utils.copy_paste_with_substitution("(^|_)l($|_)", "r")

        ## VERIFY
        self.assertEqual(len(mc.ls("r_bone_1_zBone")), 1)
