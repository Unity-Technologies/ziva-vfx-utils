import os
import zBuilder.builders.ziva as zva
import tests.utils as test_utils
import zBuilder.utils as utils
import zBuilder.zMaya as mz
from maya import cmds

from vfx_test_case import VfxTestCase, attr_values_from_scene, attr_values_from_zbuilder_nodes


class ZivaTissueGenericTestCase(VfxTestCase):
    @classmethod
    def setUpClass(cls):
        cls.tissue_names = [
            "l_tissue_1_zTissue", "r_tissue_2_zTissue", "c_tissue_3_zTissue",
            "r_subtissue_1_zTissue"
        ]
        cls.tissue_attrs = ["inertialDamping", "pressureEnvelope", "collisions"]

    def setUp(self):
        super(ZivaTissueGenericTestCase, self).setUp()
        test_utils.load_scene(scene_name="generic_tissue.ma")
        self.builder = zva.Ziva()
        self.builder.retrieve_from_scene()

    def tearDown(self):
        if os.path.exists(self.temp_file_path):
            os.remove(self.temp_file_path)
        super(ZivaTissueGenericTestCase, self).tearDown()

    def check_retrieve_ztissue_looks_good(self, builder, expected_plugs):
        """Args:
            builder (builders.ziva.Ziva()): builder object
            expected_plugs (dict): A dict of expected attribute/value pairs.
                                   {'zTissue1.collisions':True, ...}.
                                   If None/empty/False, then attributes are taken from zBuilder
                                   and values are taken from the scene.
                                   Test fails if zBuilder is missing any of the keys
                                   or has any keys with different values.
        """
        self.check_retrieve_looks_good(builder, expected_plugs, self.tissue_names, "zTissue")

    def test_retrieve(self):
        self.check_retrieve_ztissue_looks_good(self.builder, {})

    def test_retrieve_connections(self):
        builder = zva.Ziva()
        builder.retrieve_connections()
        self.check_retrieve_ztissue_looks_good(builder, {})

    def test_build_restores_attr_values(self):
        self.check_build_restores_attr_values(self.builder, self.tissue_names, self.tissue_attrs)

    def test_remove(self):
        self.check_ziva_remove_command(self.builder, "zTissue")

    def test_builder_has_same_tissue_nodes_after_writing_to_disk(self):
        builder = self.get_builder_after_writing_and_reading_from_disk(self.builder)
        self.check_retrieve_ztissue_looks_good(builder, {})

    def test_build(self):
        builder = self.get_builder_after_clean_and_build(self.builder)
        self.check_retrieve_ztissue_looks_good(builder, {})

    def test_build_from_file(self):
        builder = self.get_builder_after_write_and_retrieve_from_file(self.builder)
        self.check_retrieve_ztissue_looks_good(builder, {})

    def test_rename(self):
        ## SETUP
        cmds.select("r_tissue_1")
        cmds.ziva(t=True)

        ## VERIFY
        # check if an item exists before renaming
        self.assertEqual(cmds.ls("r_tissue_1_zTissue"), [])

        ## ACT
        mz.rename_ziva_nodes()

        ## VERIFY
        self.assertEqual(len(cmds.ls("r_tissue_1_zTissue")), 1)

    def test_cut_paste(self):
        builder = self.get_builder_after_cut_paste("l_tissue_1", "l_tissue_1_zTissue")
        self.check_retrieve_ztissue_looks_good(builder, {})

    def test_copy_paste(self):
        builder = self.get_builder_after_copy_paste("l_tissue_1", "l_tissue_1_zTissue")
        self.check_retrieve_ztissue_looks_good(builder, {})

    def test_copy_paste_with_name_substitution(self):
        ## VERIFY
        # check if zTissue does not exist before making it
        self.assertEqual(cmds.ls("r_tissue_1_zTissue"), [])

        ## ACT
        cmds.select("l_tissue_1")
        utils.copy_paste_with_substitution("(^|_)l($|_)", "r")

        ## VERIFY
        self.assertEqual(len(cmds.ls("r_tissue_1_zTissue")), 1)


class ZivaTissueMirrorTestCase(VfxTestCase):
    def setUp(self):
        super(ZivaTissueMirrorTestCase, self).setUp()
        test_utils.load_scene(scene_name='mirror_example.ma')
        self.builder = zva.Ziva()
        self.builder.retrieve_from_scene()

        # gather info
        self.tissue_items = self.builder.get_scene_items(type_filter='zTissue')
        self.l_tissue_geo = [x for x in self.tissue_items if x.association[0].startswith('l_')]

    def check_retrieve_ztissue_looks_good(self, builder, expected_plugs):
        """Args:
            builder (builders.ziva.Ziva()): builder object
            expected_plugs (dict): A dict of expected attribute/value pairs.
                                   {'zTissue1.collisions':True, ...}.
                                   If None/empty/False, then attributes are taken from zBuilder
                                   and values are taken from the scene.
                                   Test fails if zBuilder is missing any of the keys
                                   or has any keys with different values.
        """
        tissue_names = [x.name for x in self.tissue_items]
        self.check_retrieve_looks_good(builder, expected_plugs, tissue_names, "zTissue")

    def test_builder_change_with_string_replace(self):
        ## VERIFY

        # find left and right tissue items regardless of name, by looking at mesh they
        # are tied to
        r_tissue_geo = [x for x in self.tissue_items if x.association[0].startswith('r_')]
        self.assertNotEqual(len(self.l_tissue_geo), 0)
        self.assertEqual(r_tissue_geo, [])

        ## ACT
        self.builder.string_replace("^l_", "r_")

        ## VERIFY
        new_left_geo = [x for x in self.tissue_items if x.association[0].startswith('l_')]
        r_tissue_geo = [x for x in self.tissue_items if x.association[0].startswith('r_')]
        self.assertEqual(len(self.l_tissue_geo), len(r_tissue_geo))
        self.assertEqual(new_left_geo, [])

    def test_builder_build_with_string_replace(self):
        # ACT
        self.builder.string_replace("^l_", "r_")
        self.builder.build()

        # VERIFY
        tissue_names_in_builder = [x.name for x in self.tissue_items]
        self.assertSceneHasNodes(tissue_names_in_builder)

        for item in self.tissue_items:
            scene_name = item.name
            for attr in item.attrs.keys():
                scene_value = cmds.getAttr('{}.{}'.format(scene_name, attr))
                self.assertTrue(scene_value == item.attrs[attr]['value'])


# class ZivaMirrorSelectedTestCase(VfxTestCase):
#     def setUp(self):
#         super(ZivaMirrorSelectedTestCase, self).setUp()
#         test_utils.load_scene(scene_name='mirror_example.ma')

#     def test_mirror_selection(self):
#         cmds.select('l_arm_muscles')

#         builder = zva.Ziva()
#         builder.retrieve_from_scene_selection()
#         # before we build we want to mirror just the center geo
#         for item in builder.get_scene_items(name_filter='c_chest_bone'):
#             item.mirror()

#         # and we want to interpolate any map associated with the center geo
#         for item in builder.get_scene_items(type_filter='map'):
#             if 'c_chest_bone' in item._mesh:
#                 item.interpolate()

#         # now a simple string replace
#         builder.string_replace('^l_', 'r_')

#         builder.build()

#         self.assertSceneHasNodes(['zAttachment2', 'zMaterial3', 'zMaterial4'])
