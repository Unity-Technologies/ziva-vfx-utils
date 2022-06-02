import os
import zBuilder.builders.ziva as zva

from maya import cmds
from vfx_test_case import (VfxTestCase, ZivaMirrorTestCase, ZivaMirrorNiceNameTestCase,
                           ZivaUpdateTestCase, ZivaUpdateNiceNameTestCase)
from tests.utils import load_scene
from zBuilder.commands import rename_ziva_nodes, copy_paste_with_substitution, remove_solver
from zBuilder.nodes.ziva.zTissue import TissueNode


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
        load_scene("generic_tissue.ma")
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

        # check sub-tissues got stored properly in scene item
        for item in builder.get_scene_items(type_filter='zTissue'):

            # check node name in zBuilder and in scene check if it has a parent sub-tissue
            if cmds.objExists(item.name):
                parent_attr = '{}.iParentTissue'.format(item.name)
                parent_tissue = cmds.listConnections(parent_attr)
                if parent_tissue:
                    self.assertEqual(parent_tissue[0], item.parent_tissue.name)

    def test_retrieve(self):
        self.check_retrieve_ztissue_looks_good(self.builder, {})

    def test_retrieve_connections(self):
        builder = zva.Ziva()
        builder.retrieve_connections()
        self.check_retrieve_ztissue_looks_good(builder, {})

    def test_VFXACT_645_regression(self):
        # ACT
        cmds.select('r_subtissue_1')
        builder = zva.Ziva()
        builder.retrieve_connections()
        # VERIFY
        self.compare_builder_nodes_with_scene_nodes(builder)
        self.compare_builder_attrs_with_scene_attrs(builder)

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
        builder = self.get_builder_after_write_and_read(self.builder)
        self.check_retrieve_ztissue_looks_good(builder, {})

    def test_rename(self):
        ## SETUP
        cmds.select("r_tissue_1")
        cmds.ziva(t=True)

        ## VERIFY
        # check if an item exists before renaming
        self.assertEqual(cmds.ls("r_tissue_1_zTissue"), [])

        ## ACT
        rename_ziva_nodes()

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
        copy_paste_with_substitution("(^|_)l($|_)", "r")

        ## VERIFY
        self.assertEqual(len(cmds.ls("r_tissue_1_zTissue")), 1)

    def test_roundtrip_collision_set_attr(self):
        """ Retrieve and build the collision set attr.
        It is a non-keyable string type attr.
        """
        # Setup, create a tissue
        cmds.file(new=True, force=True)
        cmds.polySphere()
        cmds.ziva("pSphere1", t=True)
        # Set collision set value and retrieve
        cmds.setAttr("zTissue1.collisionSets", "1, 2", type="string")
        builder = zva.Ziva()
        builder.retrieve_from_scene()

        # Action
        tissue_node = builder.get_scene_items(name_filter="zTissue1")[0]
        # Verify
        self.assertIn("collisionSets", tissue_node.attrs)

        # Action
        remove_solver()
        builder.build()
        # Verify
        self.assertEqual(cmds.getAttr("zTissue1.collisionSets"), "1, 2")


class ZivaTissueMirrorTestCase(ZivaMirrorTestCase):
    """This Class tests a specific type of "mirroring" so there are some assumptions made

    - geometry has an identifiable qualifier, in this case it is l_ and r_
    - Both sides geometry are in the scene
    - One side has Ziva VFX nodes and other side does not, in this case l_ has Ziva nodes
    - Ziva nodes are named default like so: zTissue1, zTissue2, zTissue3

    """

    def setUp(self):
        super(ZivaTissueMirrorTestCase, self).setUp()

        load_scene('mirror_example.ma')
        self.builder = zva.Ziva()
        self.builder.retrieve_from_scene()
        # gather info
        self.scene_items_retrieved = self.builder.get_scene_items(type_filter=TissueNode.type)
        self.l_item_geo = [
            x for x in self.scene_items_retrieved if x.association[0].startswith('l_')
        ]

    def test_builder_change_with_string_replace(self):
        super(ZivaTissueMirrorTestCase, self).builder_change_with_string_replace()

    def test_builder_build_with_string_replace(self):
        super(ZivaTissueMirrorTestCase, self).builder_build_with_string_replace()


class ZivaTissueUpdateNiceNameTestCase(ZivaUpdateNiceNameTestCase):
    """This Class tests a specific type of "mirroring" so there are some assumptions made

    - geometry has an identifiable qualifier, in this case it is l_ and r_
    - Both sides geometry are in the scene
    - Both sides have Ziva VFX nodes
    - The Ziva Nodes have a side identifier same as geo

    """

    def setUp(self):
        super(ZivaTissueUpdateNiceNameTestCase, self).setUp()
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

        self.scene_items_retrieved = self.builder.get_scene_items(type_filter=TissueNode.type)
        self.l_item_geo = [
            x for x in self.scene_items_retrieved if x.association[0].startswith('l_')
        ]

    def test_builder_change_with_string_replace(self):
        super(ZivaTissueUpdateNiceNameTestCase, self).builder_change_with_string_replace()

    def test_builder_build_with_string_replace(self):
        super(ZivaTissueUpdateNiceNameTestCase, self).builder_build_with_string_replace()


class ZivaTissueMirrorNiceNameTestCase(ZivaMirrorNiceNameTestCase):
    """This Class tests a specific type of "mirroring" so there are some assumptions made

    - geometry has an identifiable qualifier, in this case it is l_ and r_
    - Both sides geometry are in the scene
    - One side has Ziva VFX nodes and other side does not, in this case l_ has Ziva nodes

    """

    def setUp(self):
        super(ZivaTissueMirrorNiceNameTestCase, self).setUp()
        # gather info

        # Bring in scene
        load_scene('mirror_example.ma')

        # force NICE NAMES
        rename_ziva_nodes()

        self.builder = zva.Ziva()
        self.builder.retrieve_from_scene()

        self.scene_items_retrieved = self.builder.get_scene_items(type_filter=TissueNode.type)
        self.l_item_geo = [
            x for x in self.scene_items_retrieved if x.association[0].startswith('l_')
        ]

    def test_builder_change_with_string_replace(self):
        super(ZivaTissueMirrorNiceNameTestCase, self).builder_change_with_string_replace()

    def test_builder_build_with_string_replace(self):
        super(ZivaTissueMirrorNiceNameTestCase, self).builder_build_with_string_replace()


class ZivaTissueUpdateTestCase(ZivaUpdateTestCase):
    """This Class tests a specific type of "mirroring" so there are some assumptions made

    - geometry has an identifiable qualifier, in this case it is l_ and r_
    - Both sides geometry are in the scene
    - Both sides have Ziva nodes

    """

    def setUp(self):
        super(ZivaTissueUpdateTestCase, self).setUp()
        load_scene('mirror_example.ma')
        self.builder = zva.Ziva()
        self.builder.retrieve_from_scene()

        # VERIFY
        self.compare_builder_nodes_with_scene_nodes(self.builder)
        self.compare_builder_attrs_with_scene_attrs(self.builder)

        # gather info
        self.scene_items_retrieved = self.builder.get_scene_items(type_filter=TissueNode.type)
        self.l_item_geo = [
            x.name for x in self.scene_items_retrieved if x.association[0].startswith('l_')
        ]
        cmds.select(self.l_item_geo)

        new_builder = zva.Ziva()
        new_builder.retrieve_from_scene()
        new_builder.string_replace("^l_", "r_")
        new_builder.build()

    def test_builder_change_with_string_replace(self):
        super(ZivaTissueUpdateTestCase, self).builder_change_with_string_replace()

    def test_builder_build_with_string_replace(self):
        super(ZivaTissueUpdateTestCase, self).builder_build_with_string_replace()
