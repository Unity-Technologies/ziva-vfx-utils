import os
import zBuilder.builders.ziva as zva

from maya import cmds
from vfx_test_case import (VfxTestCase, ZivaMirrorTestCase, ZivaMirrorNiceNameTestCase,
                           ZivaUpdateTestCase, ZivaUpdateNiceNameTestCase)
from tests.utils import load_scene
from zBuilder.commands import rename_ziva_nodes, clean_scene, rig_copy, rig_paste, copy_paste_with_substitution
from zBuilder.nodes.ziva.zRivetToBone import RivetToBoneNode


class ZivaRivetToBoneGenericTestCase(VfxTestCase):

    @classmethod
    def setUpClass(cls):
        cls.rivet_to_bone_names = ["l_loa_curve_zRivetToBone1", "l_loa_curve_zRivetToBone2"]
        cls.rivet_to_bone_attrs = ["envelope"]

    def setUp(self):
        super(ZivaRivetToBoneGenericTestCase, self).setUp()
        load_scene("generic_tissue.ma")
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

        # adding rivet name and rivet transform parent
        for item in builder.get_scene_items(type_filter='zRivetToBone'):
            scene_name = cmds.ls(item.name)[0]
            self.assertEqual(item.name, scene_name)
            # self.assertEqual(item.rivet_locator_parent, cmds.listRelatives(item.name, p=True))

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
        clean_scene()

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
        builder = self.get_builder_after_write_and_read(self.builder)
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
        rename_ziva_nodes([])

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
        rig_copy()

        ## VERIFY
        # check that node was not removed
        self.assertEqual(len(cmds.ls("l_loa_curve_zRivetToBone1")), 1)

        ## SETUP
        clean_scene()

        ## ACT
        cmds.select("l_tissue_1")
        rig_paste()

        builder = zva.Ziva()
        builder.retrieve_from_scene()
        self.check_retrieve_rivet_to_bone_looks_good(builder, {})

    def test_copy_paste_with_name_substitution(self):
        ## VERIFY
        # check if zRivetToBone does not exist before making it
        self.assertEqual(cmds.ls("r_loa_curve_zRivetToBone1"), [])

        ## ACT
        cmds.select("l_tissue_1")
        copy_paste_with_substitution("(^|_)l($|_)", "r")

        ## VERIFY
        self.assertEqual(len(cmds.ls("r_loa_curve_zRivetToBone1")), 1)


class ZivaRivetToBoneRenameGroupTestCase(VfxTestCase):

    def setUp(self):
        super(ZivaRivetToBoneRenameGroupTestCase, self).setUp()
        load_scene("generic_tissue.ma")

        # rename rivets to test
        riv1 = cmds.rename('zRivet1', 'zRivet1_NEW')
        riv2 = cmds.rename('zRivet2', 'zRivet2_NEW')
        # add to a group
        grp = cmds.group(em=True, n='loc_gr')
        cmds.parent('zRivet1_NEW', 'zRivet2_NEW', grp)
        cmds.select('zSolver1')
        self.builder = zva.Ziva()
        self.builder.retrieve_from_scene()

    def test_name_group(self):
        # adding rivet name and rivet transform parent
        for item in self.builder.get_scene_items(type_filter='zRivetToBone'):
            self.assertEqual([item.name], cmds.ls(item.name))
            self.assertEqual([item.rivet_locator_parent],
                             cmds.listRelatives(item.rivet_locator, p=True))


class ZivaRivetToBoneMirrorTestCase(ZivaMirrorTestCase):
    """This Class tests a specific type of "mirroring" so there are some assumptions made

    - geometry has an identifiable qualifier, in this case it is l_ and r_
    - Both sides geometry are in the scene
    - One side has Ziva VFX nodes and other side does not, in this case l_ has Ziva nodes
    - Ziva nodes are named default like so: zRivetToBone1, zRivetToBone2, zRivetToBone3

    """

    def setUp(self):
        super(ZivaRivetToBoneMirrorTestCase, self).setUp()

        load_scene('mirror_example-lineofaction_rivet.ma')
        self.builder = zva.Ziva()
        self.builder.retrieve_from_scene()
        # gather info
        self.scene_items_retrieved = self.builder.get_scene_items(type_filter=RivetToBoneNode.type)
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
        load_scene('mirror_example-lineofaction_rivet.ma')

        # NICE NAMES
        rename_ziva_nodes()

        # make FULL setup based on left
        builder = zva.Ziva()
        builder.retrieve_from_scene()
        builder.string_replace('^l_', 'r_')
        builder.build()

        # gather info
        cmds.select('l_armA_muscle_geo')
        self.builder = zva.Ziva()
        self.builder.retrieve_from_scene_selection()

        self.scene_items_retrieved = self.builder.get_scene_items(type_filter=RivetToBoneNode.type)
        self.l_item_geo = [
            x for x in self.scene_items_retrieved if x.association[0].startswith('l_')
        ]

    def test_builder_change_with_string_replace(self):
        super(ZivaTissueUpdateNiceNameTestCase, self).builder_change_with_string_replace()

    def test_builder_build_with_string_replace(self):
        super(ZivaTissueUpdateNiceNameTestCase, self).builder_build_with_string_replace()


class ZivaRivetToBoneMirrorNiceNameTestCase(ZivaMirrorNiceNameTestCase):
    """This Class tests a specific type of "mirroring" so there are some assumptions made

    - geometry has an identifiable qualifier, in this case it is l_ and r_
    - Both sides geometry are in the scene
    - One side has Ziva VFX nodes and other side does not, in this case l_ has Ziva nodes

    """

    def setUp(self):
        super(ZivaRivetToBoneMirrorNiceNameTestCase, self).setUp()
        # gather info

        # Bring in scene
        load_scene('mirror_example-lineofaction_rivet.ma')

        # force NICE NAMES
        rename_ziva_nodes()

        self.builder = zva.Ziva()
        self.builder.retrieve_from_scene()

        self.scene_items_retrieved = self.builder.get_scene_items(type_filter=RivetToBoneNode.type)
        self.l_item_geo = [
            x for x in self.scene_items_retrieved if x.association[0].startswith('l_')
        ]

    def test_builder_change_with_string_replace(self):
        super(ZivaRivetToBoneMirrorNiceNameTestCase, self).builder_change_with_string_replace()

    def test_builder_build_with_string_replace(self):
        super(ZivaRivetToBoneMirrorNiceNameTestCase, self).builder_build_with_string_replace()


class ZivaRivetToBoneUpdateTestCase(ZivaUpdateTestCase):
    """This Class tests a specific type of "mirroring" so there are some assumptions made

    - geometry has an identifiable qualifier, in this case it is l_ and r_
    - Both sides geometry are in the scene
    - Both sides have Ziva nodes

    """

    def setUp(self):
        super(ZivaRivetToBoneUpdateTestCase, self).setUp()
        load_scene('mirror_example-lineofaction_rivet.ma')
        self.builder = zva.Ziva()
        self.builder.retrieve_from_scene()

        # VERIFY
        self.compare_builder_nodes_with_scene_nodes(self.builder)
        self.compare_builder_attrs_with_scene_attrs(self.builder)

        # gather info
        self.scene_items_retrieved = self.builder.get_scene_items(type_filter=RivetToBoneNode.type)
        self.l_item_geo = [
            x.name for x in self.scene_items_retrieved if x.association[0].startswith('l_')
        ]
        # select a left tissue mesh
        tissue = self.builder.get_scene_items(type_filter='zTissue')[0]
        cmds.select(tissue.association[0])

        new_builder = zva.Ziva()
        new_builder.retrieve_from_scene()
        new_builder.string_replace("^l_", "r_")
        new_builder.build()

    def test_builder_change_with_string_replace(self):
        super(ZivaRivetToBoneUpdateTestCase, self).builder_change_with_string_replace()

    def test_builder_build_with_string_replace(self):
        super(ZivaRivetToBoneUpdateTestCase, self).builder_build_with_string_replace()


class ZivaRivetToBoneRenameBugTestCase(ZivaUpdateTestCase):
    """This is a bug fixed by VFXACT-1525 that affects zRivetToBoneLocators
    When rename_ziva_nodes was ran multiple times the name would add another
    instance of the curve to the name, growing everytime.  To check this fix worked
    we simply run rename_ziva_nodes multple times and check scene.

    """

    def setUp(self):
        super(ZivaRivetToBoneRenameBugTestCase, self).setUp()
        load_scene('mirror_example-lineofaction_rivet.ma')

    def test_rename_multiple_times(self):
        rename_ziva_nodes()
        rename_ziva_nodes()

        self.assertSceneHasNodes(['l_fiber1_curve_zRivet1', 'l_fiber1_curve_zRivet2'])