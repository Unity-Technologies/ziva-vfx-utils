import os
import zBuilder.builders.ziva as zva
import tests.utils as test_utils
import zBuilder.utils as utils
import zBuilder.zMaya as mz
from maya import cmds
from maya import mel

from vfx_test_case import VfxTestCase, ZivaMirrorTestCase, ZivaUpdateNiceNameTestCase

NODE_TYPE = 'zRivetToBone'


class ZivaRivetToBoneGenericTestCase(VfxTestCase):
    @classmethod
    def setUpClass(cls):
        cls.rivet_to_bone_names = ["l_loa_curve_zRivetToBone1", "l_loa_curve_zRivetToBone2"]
        cls.rivet_to_bone_attrs = ["envelope"]

    def setUp(self):
        super(ZivaRivetToBoneGenericTestCase, self).setUp()
        test_utils.load_scene(scene_name="generic_tissue.ma")
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
        self.check_retrieve_looks_good(builder, expected_plugs, self.rivet_to_bone_names,
                                       "zRivetToBone")

    def test_retrieve(self):
        self.check_retrieve_rivet_to_bone_looks_good(self.builder, {})

    def test_retrieve_connections(self):
        builder = zva.Ziva()
        builder.retrieve_connections()
        self.check_retrieve_rivet_to_bone_looks_good(builder, {})

    def test_build_restores_attr_values(self):
        self.check_build_restores_attr_values(self.builder, self.rivet_to_bone_names,
                                              self.rivet_to_bone_attrs)

    def test_remove(self):
        ## ACT
        mz.clean_scene()

        ## VERIFY
        rivet_to_bone = cmds.zQuery(rtb=True)
        self.assertIsNone(rivet_to_bone)

    def test_builder_has_same_rivet_to_bone_nodes_after_writing_to_disk(self):
        builder = self.get_builder_after_writing_and_reading_from_disk(self.builder)
        self.check_retrieve_rivet_to_bone_looks_good(builder, {})

    def test_build(self):
        builder = self.get_builder_after_clean_and_build(self.builder)
        self.check_retrieve_rivet_to_bone_looks_good(builder, {})

    def test_build_from_file(self):
        builder = self.get_builder_after_write_and_retrieve_from_file(self.builder)
        self.check_retrieve_rivet_to_bone_looks_good(builder, {})

    def test_rename(self):
        ## SETUP
        cmds.select(["r_loa_curve.cv[0]", "c_bone_1"])
        cmds.zRivetToBone()

        ## VERIFY
        # check if an item exists before renaming
        self.assertEqual(cmds.ls("r_loa_curve_zRivetToBone1"), [])

        ## ACT
        cmds.select(cl=True)
        mz.rename_ziva_nodes([])

        ## VERIFY
        self.assertEqual(len(cmds.ls("r_loa_curve_zRivetToBone1")), 1)

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

    def test_copy_paste(self):
        ## VERIFY
        # check if node exists
        self.assertEqual(len(cmds.ls("l_loa_curve_zRivetToBone1")), 1)
        ## ACT
        cmds.select("l_tissue_1")
        utils.rig_copy()

        ## VERIFY
        # check that node was not removed
        self.assertEqual(len(cmds.ls("l_loa_curve_zRivetToBone1")), 1)

        ## SETUP
        mz.clean_scene()

        ## ACT
        cmds.select("l_tissue_1")
        utils.rig_paste()

        builder = zva.Ziva()
        builder.retrieve_from_scene()
        self.check_retrieve_rivet_to_bone_looks_good(builder, {})

    def test_copy_paste_with_name_substitution(self):
        ## VERIFY
        # check if zRivetToBone does not exist before making it
        self.assertEqual(cmds.ls("r_loa_curve_zRivetToBone1"), [])

        ## ACT
        cmds.select("l_tissue_1")
        utils.copy_paste_with_substitution("(^|_)l($|_)", "r")

        ## VERIFY
        self.assertEqual(len(cmds.ls("r_loa_curve_zRivetToBone1")), 1)


class ZivaRivetToBoneMirrorTestCase(ZivaMirrorTestCase):
    """This Class tests a specific type of "mirroring" so there are some assumptions made

    - geometry has an identifiable qualifier, in this case it is l_ and r_
    - Both sides geometry are in the scene
    - One side has Ziva VFX nodes and other side does not, in this case l_ has Ziva nodes
    - Ziva nodes are named default like so: zTissue1, zTissue2, zTissue3

    """

    def setUp(self):
        super(ZivaRivetToBoneMirrorTestCase, self).setUp()

        test_utils.load_scene(scene_name='mirror_example-lineofaction_rivet.ma')
        self.builder = zva.Ziva()
        self.builder.retrieve_from_scene()
        # gather info
        self.scene_items_retrieved = self.builder.get_scene_items(type_filter=NODE_TYPE)
        self.l_item_geo = [
            x for x in self.scene_items_retrieved if x.association[0].startswith('l_')
        ]

    def test_builder_change_with_string_replace(self):
        super(ZivaRivetToBoneMirrorTestCase, self).builder_change_with_string_replace()

    def test_builder_build_with_string_replace(self):
        super(ZivaRivetToBoneMirrorTestCase, self).builder_build_with_string_replace()


class ZivaTissueUpdateNiceNameTestCase(ZivaUpdateNiceNameTestCase):
    """This Class tests a specific type of "mirroring" so there are some assumptions made

    - geometry has an identifiable qualifier, in this case it is l_ and r_
    - Both sides geometry are in the scene
    - Both sides have Ziva VFX nodes
    - The Ziva Nodes have a side identifier same as geo

    """

    def setUp(self):
        super(ZivaTissueUpdateNiceNameTestCase, self).setUp()
        test_utils.load_scene(scene_name='mirror_example-lineofaction_rivet.ma')

        # NICE NAMES
        mz.rename_ziva_nodes()

        # make FULL setup based on left
        builder = zva.Ziva()
        builder.retrieve_from_scene()
        builder.string_replace('^l_', 'r_')
        builder.build()

        # gather info
        cmds.select('l_armA_muscle_geo', 'l_armA_subtissue_geo')
        self.builder = zva.Ziva()
        self.builder.retrieve_from_scene_selection()

        self.scene_items_retrieved = self.builder.get_scene_items(type_filter=NODE_TYPE)
        self.l_item_geo = [
            x for x in self.scene_items_retrieved if x.association[0].startswith('l_')
        ]

        self.compare_builder_nodes_with_scene_nodes(self.builder)
        self.compare_builder_attrs_with_scene_attrs(self.builder)

    def test_builder_change_with_string_replace(self):
        super(ZivaTissueUpdateNiceNameTestCase, self).builder_change_with_string_replace()

    def test_builder_build_with_string_replace(self):
        super(ZivaTissueUpdateNiceNameTestCase, self).builder_build_with_string_replace()
