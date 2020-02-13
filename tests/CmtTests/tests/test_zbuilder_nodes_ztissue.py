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
    """This Class tests a specific type of "mirroring" so there are some assumptions made

    - geometry has an identifiable qualifier, in this case it is l_ and r_
    - Both sides geometry are in the scene
    - One side has Ziva VFX nodes and other side does not, in this case l_ has Ziva nodes

    """

    def setUp(self):
        super(ZivaTissueMirrorTestCase, self).setUp()
        test_utils.load_scene(scene_name='mirror_example.ma')
        self.builder = zva.Ziva()
        self.builder.retrieve_from_scene()

        # gather info
        self.type_ = 'zTissue'
        self.scene_items_retrieved = self.builder.get_scene_items(type_filter=self.type_)
        self.l_item_geo = [
            x for x in self.scene_items_retrieved if x.association[0].startswith('l_')
        ]

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
        item_names = [x.name for x in self.scene_items_retrieved]
        self.check_retrieve_looks_good(builder, expected_plugs, item_names, self.type_)

    def test_builder_change_with_string_replace(self):
        ## VERIFY

        # find left and right tissue items regardless of name, by looking at mesh they
        # are tied to
        r_item_geo = [x for x in self.scene_items_retrieved if x.association[0].startswith('r_')]
        self.assertNotEqual(len(self.l_item_geo), 0)  # Left geo should have been all renamerd to r_
        self.assertEqual(r_item_geo, [])  # Make sure no r_ geo is in original scene

        ## ACT
        self.builder.string_replace("^l_", "r_")

        ## VERIFY
        new_left_geo = [x for x in self.scene_items_retrieved if x.association[0].startswith('l_')]
        r_item_geo = [x for x in self.scene_items_retrieved if x.association[0].startswith('r_')]
        self.assertEqual(len(self.l_item_geo),
                         len(r_item_geo))  # number of right geos equal original left
        self.assertEqual(new_left_geo, [])  # after replace left geo should have been renamed

    def test_builder_build_with_string_replace(self):
        # ACT
        self.builder.string_replace("^l_", "r_")
        self.builder.build()

        # VERIFY
        item_names_in_builder = [x.name for x in self.scene_items_retrieved]
        # Original Ziva nodes should still be in scene
        self.assertSceneHasNodes(item_names_in_builder)

        # comparing attribute values between builder and scene
        for scene_item in self.scene_items_retrieved:
            scene_name = scene_item.name
            for attr in scene_item.attrs.keys():
                scene_value = cmds.getAttr('{}.{}'.format(scene_name, attr))
                self.assertTrue(scene_value == scene_item.attrs[attr]['value'])

        # Tissue specific sub-tissue check
        parents = {
            x.name: x.parent_tissue.name
            for x in self.scene_items_retrieved if x.parent_tissue
        }

        for key, value in parents.iteritems():
            self.assertEqual(value, cmds.listConnections(key + '.iParentTissue')[0])
