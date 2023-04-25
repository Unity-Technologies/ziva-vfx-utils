import os
import zBuilder.builders.ziva as zva

from maya import cmds
from vfx_test_case import (VfxTestCase, ZivaMirrorTestCase, ZivaMirrorNiceNameTestCase,
                           ZivaUpdateTestCase, ZivaUpdateNiceNameTestCase)
from tests.utils import load_scene
from zBuilder.commands import rename_ziva_nodes, copy_paste_with_substitution
from zBuilder.nodes.ziva.zMaterial import MaterialNode


class ZivaMaterialGenericTestCase(VfxTestCase):

    @classmethod
    def setUpClass(cls):
        cls.material_names = [
            'r_tissue_2_zMaterial', 'c_tissue_3_zMaterial', 'c_cloth_1_zMaterial',
            'r_subtissue_1_zMaterial', 'l_tissue_1_zMaterial', 'l_cloth_1_zMaterial',
            'l_tissue_1_zMaterial1'
        ]
        cls.material_attrs = ["youngsModulus", "massDensity", "restScale"]

    def setUp(self):
        super(ZivaMaterialGenericTestCase, self).setUp()
        load_scene("generic.ma")
        self.builder = zva.Ziva()
        self.builder.retrieve_from_scene()

    def tearDown(self):
        if os.path.exists(self.temp_file_path):
            os.remove(self.temp_file_path)
        super(ZivaMaterialGenericTestCase, self).tearDown()

    def check_retrieve_zmaterial_looks_good(self, builder, expected_plugs):
        """Args:
            builder (builders.ziva.Ziva()): builder object
            expected_plugs (dict): A dict of expected attribute/value pairs.
                                   {'zMaterial1.massDensity':1060, ...}.
                                   If None/empty/False, then attributes are taken from zBuilder
                                   and values are taken from the scene.
                                   Test fails if zBuilder is missing any of the keys
                                   or has any keys with different values.
        """
        self.check_retrieve_looks_good(builder, expected_plugs, self.material_names, "zMaterial")

    def test_retrieve(self):
        self.check_retrieve_zmaterial_looks_good(self.builder, {})

    def test_retrieve_connections(self):
        builder = zva.Ziva()
        builder.retrieve_connections()
        self.check_retrieve_zmaterial_looks_good(builder, {})

    def test_build_restores_attr_values(self):
        self.check_build_restores_attr_values(self.builder, self.material_names,
                                              self.material_attrs)

    def test_remove(self):
        self.check_ziva_remove_command(self.builder, "zMaterial")

    def test_builder_has_same_material_nodes_after_writing_to_disk(self):
        builder = self.get_builder_after_writing_and_reading_from_disk(self.builder)
        self.check_retrieve_zmaterial_looks_good(builder, {})

    def test_build(self):
        builder = self.get_builder_after_clean_and_build(self.builder)
        self.check_retrieve_zmaterial_looks_good(builder, {})

    def test_build_from_file(self):
        builder = self.get_builder_after_write_and_read(self.builder)
        self.check_retrieve_zmaterial_looks_good(builder, {})

    def test_rename(self):
        ## SETUP
        cmds.select("r_tissue_1")
        cmds.ziva(t=True)

        ## VERIFY
        # check if an item exists before renaming
        self.assertEqual(cmds.ls("r_tissue_1_zMaterial1"), [])

        ## ACT
        rename_ziva_nodes()

        ## VERIFY
        self.assertEqual(len(cmds.ls("r_tissue_1_zMaterial1")), 1)

    def test_safe_rename(self):
        # testing to make sure ziva_rename_nodes doesn't rename nodes user has already renamed
        ## SETUP
        cmds.select("r_tissue_1")
        cmds.ziva(t=True)
        cmds.rename('zMaterial1', 'my_material')
        cmds.rename('zRivet1', 'my_rivet')
        ## ACT
        rename_ziva_nodes()

        ## VERIFY
        self.assertEqual(len(cmds.ls("my_material")), 1)
        self.assertEqual(len(cmds.ls("my_rivet")), 1)

    def test_string_replace(self):
        ## VERIFY
        # check if an item exists before string_replace
        r_material = self.builder.get_scene_items(name_filter="r_tissue_2_zMaterial")
        self.assertGreaterEqual(len(r_material), 1)

        ## ACT
        self.builder.string_replace("^r_", "l_")

        ## VERIFY
        r_material = self.builder.get_scene_items(name_filter="r_tissue_2_zMaterial")
        self.assertEqual(r_material, [])

    def test_cut_paste(self):
        builder = self.get_builder_after_cut_paste("l_tissue_1", "l_tissue_1_zMaterial")
        self.check_retrieve_zmaterial_looks_good(builder, {})

    def test_copy_paste(self):
        builder = self.get_builder_after_copy_paste("l_tissue_1", "l_tissue_1_zMaterial")
        self.check_retrieve_zmaterial_looks_good(builder, {})

    def test_copy_paste_with_name_substitution(self):
        ## VERIFY
        # check if zMaterial does not exist before making it
        self.assertEqual(cmds.ls("r_tissue_1_zMaterial"), [])

        ## ACT
        cmds.select("l_tissue_1")
        copy_paste_with_substitution("(^|_)l($|_)", "r")

        ## VERIFY
        self.assertEqual(len(cmds.ls("r_tissue_1_zMaterial")), 1)

    def test_weight_interpolation(self):
        weights = [
            1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0,
            1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0,
            1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0,
            1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0,
            1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0,
            0.9999990463256836, 0.0, 0.0, 0.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0,
            0.9999997019767761, 0.9843137264251709, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 0.0,
            0.0, 0.0, 0.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 0.0, 0.0, 0.0, 0.0, 1.0, 1.0, 1.0, 1.0,
            1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 1.0, 1.0, 1.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0,
            1.0, 1.0, 1.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 1.0, 1.0, 1.0, 1.0, 0.0, 0.0, 0.0,
            0.0, 0.0, 1.0, 1.0, 1.0, 1.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 1.0, 1.0, 1.0, 1.0,
            0.0, 0.0, 0.0, 0.0, 5.460792067424336e-07, 1.0, 1.0, 1.0, 1.0, 1.0, 0.0, 0.0, 0.0, 0.0,
            0.0, 1.0, 1.0, 1.0, 1.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 1.0, 1.0, 1.0, 1.0, 0.0,
            0.0, 0.0, 0.0, 0.0, 1.0, 1.0, 1.0, 1.0, 1.0, 0.0, 0.0, 0.0, 0.0, 5.455602831716533e-07,
            1.0, 1.0, 1.0, 1.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 1.0, 1.0, 1.0, 1.0, 0.0, 0.0,
            0.0, 0.0, 0.0, 1.0, 1.0, 1.0, 1.0, 1.0, 0.0, 0.0, 0.0, 0.0, 4.76837158203125e-07, 1.0,
            1.0, 1.0, 1.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 1.0, 1.0, 1.0, 1.0, 0.0, 0.0, 0.0,
            2.980232238769531e-07, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 1.0,
            1.0, 1.0, 1.0, 0.9999991059303284, 0.0, 0.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0,
            0.0, 0.0, 0.05098072811961174, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0,
            1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0,
            1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0,
            1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0,
            1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0,
            1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 0.9999999403953552, 0.0, 0.0, 0.0, 0.0,
            2.0760269592301483e-07, 1.0, 1.0, 1.0, 1.0, 0.9999999403953552, 0.0, 0.0, 0.0, 0.0,
            6.661877449687381e-08, 1.0, 1.0, 1.0, 1.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 1.0, 1.0,
            1.0, 1.0, 0.0, 0.0, 0.0, 0.0, 3.372956314251496e-07, 1.0, 1.0, 1.0, 1.0, 1.0, 0.0, 0.0,
            0.0, 0.0, 0.0, 1.0, 1.0, 1.0, 1.0, 1.0, 0.0, 0.0, 0.0, 0.0, 3.4121126191166695e-07, 1.0,
            1.0, 1.0, 1.0, 0.9999999403953552, 0.0, 0.0, 0.0, 0.0, 2.130416163481641e-07, 1.0, 1.0,
            1.0, 1.0, 0.9999999403953552, 0.0, 0.0, 0.0, 0.0, 6.93431019271884e-08, 1.0, 1.0, 1.0,
            1.0, 1.0, 1.0, 1.0, 0.9921568632125854, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
            0.0, 0.0, 0.0, 0.0, 0.025490285828709602, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0,
            0.9921568036079407, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
            0.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
            0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.5, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0,
            0.9999997615814209, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
            0.0, 0.0, 1.0, 1.0, 1.0, 1.0
        ]

        self.builder.string_replace("l_tissue_1", "l_tissue_1_high")
        # Rest shape has to be removed from the build list because there is no rest shape for
        # l_tissue_1_high mesh in the scene
        rest_shape_item = self.builder.get_scene_items(name_filter="l_tissue_1_high_zRestShape")[0]
        self.builder.remove_scene_item(rest_shape_item)
        self.builder.string_replace("l_tissue_1_high_embedded_cube", "l_tissue_1_embedded_cube")
        self.check_map_interpolation(self.builder, "l_tissue_1_high_zMaterial1", weights, 0)


class ZivaMaterialMirrorTestCase(ZivaMirrorTestCase):
    """This Class tests a specific type of "mirroring" so there are some assumptions made

    - geometry has an identifiable qualifier, in this case it is l_ and r_
    - Both sides geometry are in the scene
    - One side has Ziva VFX nodes and other side does not, in this case l_ has Ziva nodes
    - Ziva nodes are named default like so: zMaterial1, zMaterial2, zMaterial3

    """

    def setUp(self):
        super(ZivaMaterialMirrorTestCase, self).setUp()

        load_scene('mirror_example.ma')
        self.builder = zva.Ziva()
        self.builder.retrieve_from_scene()
        # gather info
        self.scene_items_retrieved = self.builder.get_scene_items(type_filter=MaterialNode.type)
        self.l_item_geo = [
            x for x in self.scene_items_retrieved if x.association[0].startswith('l_')
        ]

    def test_builder_change_with_string_replace(self):
        super(ZivaMaterialMirrorTestCase, self).builder_change_with_string_replace()

    def test_builder_build_with_string_replace(self):
        super(ZivaMaterialMirrorTestCase, self).builder_build_with_string_replace()


class ZivaMaterialUpdateNiceNameTestCase(ZivaUpdateNiceNameTestCase):
    """This Class tests a specific type of "mirroring" so there are some assumptions made

    - geometry has an identifiable qualifier, in this case it is l_ and r_
    - Both sides geometry are in the scene
    - Both sides have Ziva VFX nodes
    - The Ziva Nodes have a side identifier same as geo

    """

    def setUp(self):
        super(ZivaMaterialUpdateNiceNameTestCase, self).setUp()
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

        self.scene_items_retrieved = self.builder.get_scene_items(type_filter=MaterialNode.type)
        self.l_item_geo = [
            x for x in self.scene_items_retrieved if x.association[0].startswith('l_')
        ]

    def test_builder_change_with_string_replace(self):
        super(ZivaMaterialUpdateNiceNameTestCase, self).builder_change_with_string_replace()

    def test_builder_build_with_string_replace(self):
        super(ZivaMaterialUpdateNiceNameTestCase, self).builder_build_with_string_replace()


class ZivaMaterialMirrorNiceNameTestCase(ZivaMirrorNiceNameTestCase):
    """This Class tests a specific type of "mirroring" so there are some assumptions made

    - geometry has an identifiable qualifier, in this case it is l_ and r_
    - Both sides geometry are in the scene
    - One side has Ziva VFX nodes and other side does not, in this case l_ has Ziva nodes

    """

    def setUp(self):
        super(ZivaMaterialMirrorNiceNameTestCase, self).setUp()
        # gather info

        # Bring in scene
        load_scene('mirror_example.ma')

        # force NICE NAMES
        rename_ziva_nodes()

        self.builder = zva.Ziva()
        self.builder.retrieve_from_scene()

        self.scene_items_retrieved = self.builder.get_scene_items(type_filter=MaterialNode.type)
        self.l_item_geo = [
            x for x in self.scene_items_retrieved if x.association[0].startswith('l_')
        ]

    def test_builder_change_with_string_replace(self):
        super(ZivaMaterialMirrorNiceNameTestCase, self).builder_change_with_string_replace()

    def test_builder_build_with_string_replace(self):
        super(ZivaMaterialMirrorNiceNameTestCase, self).builder_build_with_string_replace()


class ZivaMaterialUpdateTestCase(ZivaUpdateTestCase):
    """This Class tests a specific type of "mirroring" so there are some assumptions made

    - geometry has an identifiable qualifier, in this case it is l_ and r_
    - Both sides geometry are in the scene
    - Both sides have Ziva nodes

    """

    def setUp(self):
        super(ZivaMaterialUpdateTestCase, self).setUp()
        load_scene('mirror_example.ma')
        self.builder = zva.Ziva()
        self.builder.retrieve_from_scene()

        # VERIFY
        self.compare_builder_nodes_with_scene_nodes(self.builder)
        self.compare_builder_attrs_with_scene_attrs(self.builder)

        # gather info
        self.scene_items_retrieved = self.builder.get_scene_items(type_filter=MaterialNode.type)
        self.l_item_geo = [
            x.name for x in self.scene_items_retrieved if x.association[0].startswith('l_')
        ]
        cmds.select(self.l_item_geo)

        new_builder = zva.Ziva()
        new_builder.retrieve_from_scene()
        new_builder.string_replace("^l_", "r_")
        new_builder.build()

    def test_builder_change_with_string_replace(self):
        super(ZivaMaterialUpdateTestCase, self).builder_change_with_string_replace()

    def test_builder_build_with_string_replace(self):
        super(ZivaMaterialUpdateTestCase, self).builder_build_with_string_replace()


class ZivaMaterialCenterTestCase(ZivaUpdateTestCase):

    def setUp(self):
        super(ZivaMaterialCenterTestCase, self).setUp()
        cmds.polySphere(n='c_muscle')

        cmds.select('c_muscle')
        cmds.ziva(t=True)

        cmds.select('c_muscle')
        results = cmds.ziva(m=True)
        cmds.rename(results[0], 'l_zMaterial1')
        results = cmds.ziva(m=True)
        cmds.rename(results[0], 'l_zMaterial2')

        cmds.select('zSolver1')
        self.builder = zva.Ziva()
        self.builder.retrieve_from_scene_selection()
        # VERIFY
        self.compare_builder_nodes_with_scene_nodes(self.builder)
        self.compare_builder_attrs_with_scene_attrs(self.builder)

    def test_builder_center_materials(self):
        # this test is for VFXACT-1482 as this test passes with the fix for it
        # Without the fix for this no new materials would get created on center
        self.builder.string_replace('^l_', 'r_')
        self.builder.build()

        cmds.select('c_muscle')

        self.assertEqual(len(cmds.zQuery(t='zMaterial')), 5)


class ZivaMaterialConnectionsTestCase(VfxTestCase):

    def setUp(self):
        super(ZivaMaterialConnectionsTestCase, self).setUp()

        cmds.polySphere(n='ball')
        cmds.ziva(t=True)
        cmds.spaceLocator(name='loc')
        cmds.connectAttr('loc.translateX', 'zMaterial1.volumeConservation')

        cmds.select(cl=True)
        self.builder = zva.Ziva()
        self.builder.retrieve_from_scene()

    def test_restore_connection(self):
        ## ACT
        cmds.disconnectAttr('loc.translateX', 'zMaterial1.volumeConservation')
        self.builder.build()

        ## VERIFY
        self.assertTrue(cmds.isConnected('loc.translateX', 'zMaterial1.volumeConservation'))
