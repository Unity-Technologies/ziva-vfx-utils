import os
import zBuilder.builders.ziva as zva

from maya import cmds
from maya import mel
from vfx_test_case import VfxTestCase, ZivaMirrorTestCase, ZivaUpdateTestCase, ZivaUpdateNiceNameTestCase
from tests.utils import load_scene
from zBuilder.commands import clean_scene, rename_ziva_nodes, copy_paste_with_substitution
from zBuilder.nodes.ziva.zLineOfAction import LineOfActionNode


class ZivaLineOfActionGenericTestCase(VfxTestCase):

    @classmethod
    def setUpClass(cls):
        cls.loa_names = ["l_tissue_1_zFiber1_zLineOfAction", "r_subtissue_1_zFiber1_zLineOfAction"]
        cls.loa_attrs = ["maxExcitation", "stretchBias", "posSensitivity"]

    def setUp(self):
        super(ZivaLineOfActionGenericTestCase, self).setUp()
        load_scene("generic_tissue.ma")
        self.builder = zva.Ziva()
        self.builder.retrieve_from_scene()

    def tearDown(self):
        if os.path.exists(self.temp_file_path):
            os.remove(self.temp_file_path)
        super(ZivaLineOfActionGenericTestCase, self).tearDown()

    def check_retrieve_loa_looks_good(self, builder, expected_plugs):
        """Args:
            builder (builders.ziva.Ziva()): builder object
            expected_plugs (dict): A dict of expected attribute/value pairs.
                                   {'zLineOfAction1.stretchBias':1, ...}.
                                   If None/empty/False, then attributes are taken from zBuilder
                                   and values are taken from the scene.
                                   Test fails if zBuilder is missing any of the keys
                                   or has any keys with different values.
        """
        self.check_retrieve_looks_good(builder, expected_plugs, self.loa_names, "zLineOfAction")

    def test_retrieve(self):
        self.check_retrieve_loa_looks_good(self.builder, {})

    def test_retrieve_connections(self):
        builder = zva.Ziva()
        builder.retrieve_connections()
        self.check_retrieve_loa_looks_good(builder, {})

    def test_build_restores_attr_values(self):
        self.check_build_restores_attr_values(self.builder, self.loa_names, self.loa_attrs)

    def test_remove(self):
        self.check_ziva_remove_command(self.builder, "zLineOfAction")

    def test_builder_has_same_loa_nodes_after_writing_to_disk(self):
        builder = self.get_builder_after_writing_and_reading_from_disk(self.builder)
        self.check_retrieve_loa_looks_good(builder, {})

    def test_build(self):
        builder = self.get_builder_after_clean_and_build(self.builder)
        self.check_retrieve_loa_looks_good(builder, {})

    def test_build_from_file(self):
        builder = self.get_builder_after_write_and_read(self.builder)
        self.check_retrieve_loa_looks_good(builder, {})

    def test_rename(self):
        ## SETUP
        cmds.select("r_tissue_2")
        # create fiber
        fiber = cmds.ziva(f=True)[0]
        # create zLineOfAction
        cmds.select([fiber, "r_loa_curve"])
        cmds.ziva(loa=True)

        ## VERIFY
        # check if an item exists before renaming
        self.assertEqual(cmds.ls("r_tissue_2_zFiber1_zLineOfAction"), [])

        ## ACT
        rename_ziva_nodes()

        ## VERIFY
        self.assertEqual(len(cmds.ls("r_tissue_2_zFiber1_zLineOfAction")), 1)

    def test_string_replace(self):
        ## VERIFY
        # check if an item exists before string_replace
        r_loa = self.builder.get_scene_items(name_filter="l_tissue_1_zFiber1_zLineOfAction")
        self.assertGreaterEqual(len(r_loa), 1)

        ## ACT
        self.builder.string_replace("^l_", "r_")

        ## VERIFY
        r_loa = self.builder.get_scene_items(name_filter="l_tissue_1_zFiber1_zLineOfAction")
        self.assertEqual(r_loa, [])

    def test_cut_paste(self):
        builder = self.get_builder_after_cut_paste("l_tissue_1", "l_tissue_1_zFiber1_zLineOfAction")
        self.check_retrieve_loa_looks_good(builder, {})

    def test_copy_paste(self):
        builder = self.get_builder_after_copy_paste("l_tissue_1",
                                                    "l_tissue_1_zFiber1_zLineOfAction")
        self.check_retrieve_loa_looks_good(builder, {})

    def test_copy_paste_with_name_substitution(self):
        ## VERIFY
        # check if zLineOfAction does not exist before making it
        self.assertEqual(cmds.ls("r_tissue_1_zFiber1_zLineOfAction"), [])

        ## ACT
        cmds.select("l_tissue_1")
        copy_paste_with_substitution("(^|_)l($|_)", "r")

        ## VERIFY
        self.assertEqual(len(cmds.ls("r_tissue_1_zFiber1_zLineOfAction")), 1)


class ZivaMultiCurveLoaTestCase(VfxTestCase):

    def setUp(self):
        super(ZivaMultiCurveLoaTestCase, self).setUp()
        # setup a scene with 2 curves on 1 zLineOfAction

        # create geometry
        cmds.polySphere(name='bone')
        cmds.setAttr('bone.translateY', 2)
        cmds.polySphere(name='tissue')

        # create zLineOfAction and zBone
        cmds.select('tissue')
        mel.eval('ziva -t')

        cmds.select('bone')
        mel.eval('ziva -b')

        # create an attachment, probably not needed
        cmds.select('tissue', 'bone')
        mel.eval('ziva -a')

        # create teh fiber
        cmds.select('tissue')
        fiber = mel.eval('ziva -f')[0]

        # create 2 curves on fiber and create a loa
        cmds.select(fiber)
        curve1 = mel.eval('zLineOfActionUtil')[0]
        cmds.select(fiber)
        curve2 = mel.eval('zLineOfActionUtil')[0]
        curve1 = curve1.replace('Shape', '')
        curve2 = curve2.replace('Shape', '')
        cmds.select(fiber, curve1, curve2)
        mel.eval('ziva -loa')

        cmds.select('zSolver1')

        self.builder = zva.Ziva()
        self.builder.retrieve_from_scene()

    def test_retrieve(self):

        loa = self.builder.get_scene_items(type_filter='zLineOfAction')[0]

        # loa.association should have 2 elements.
        self.assertEqual(len(loa.association), 2)

    def test_build(self):
        clean_scene()

        self.builder.build()

        # after it is built there should be 2 curves hooked up to loa
        curves = cmds.listConnections('zLineOfAction1.curves')
        self.assertEqual(len(curves), 2)

    def test_retrieve_connections_loa_selected(self):

        loa = self.builder.get_scene_items(type_filter='zLineOfAction')[0]

        # now retrieve
        cmds.select(loa.name)
        builder = zva.Ziva()
        builder.retrieve_connections()
        builder.stats()
        print(builder.get_scene_items())
        # should not be empty
        self.assertGreater(len(builder.get_scene_items()), 0)

    def test_retrieve_connections_loa_selected_check(self):

        loa = self.builder.get_scene_items(type_filter='zLineOfAction')[0]

        # now retrieve
        cmds.select(loa.name)
        builder = zva.Ziva()
        builder.retrieve_connections()

        # this should have grabbed the specific loa
        result = builder.get_scene_items(name_filter=loa.name)

        # result will have named loa
        self.assertEqual(len(result), 1)


class ZivaLineOfActionMirrorTestCase(ZivaMirrorTestCase):
    """This Class tests a specific type of "mirroring" so there are some assumptions made

    - geometry has an identifiable qualifier, in this case it is l_ and r_
    - Both sides geometry are in the scene
    - One side has Ziva VFX nodes and other side does not, in this case l_ has Ziva nodes
    - Ziva nodes are named default like so: zLineOfAction1, zLineOfAction2, zLineOfAction3

    """

    def setUp(self):
        super(ZivaLineOfActionMirrorTestCase, self).setUp()

        load_scene('mirror_example-lineofaction_rivet.ma')
        self.builder = zva.Ziva()
        self.builder.retrieve_from_scene()
        # gather info
        self.scene_items_retrieved = self.builder.get_scene_items(type_filter=LineOfActionNode.type)
        self.l_item_geo = [
            x for x in self.scene_items_retrieved if x.association[0].startswith('l_')
        ]

    def test_builder_change_with_string_replace(self):
        super(ZivaLineOfActionMirrorTestCase, self).builder_change_with_string_replace()

    def test_builder_build_with_string_replace(self):
        super(ZivaLineOfActionMirrorTestCase, self).builder_build_with_string_replace()


class ZivaLineOfActionUpdateNiceNameTestCase(ZivaUpdateNiceNameTestCase):
    """This Class tests a specific type of "mirroring" so there are some assumptions made

    - geometry has an identifiable qualifier, in this case it is l_ and r_
    - Both sides geometry are in the scene
    - Both sides have Ziva VFX nodes
    - The Ziva Nodes have a side identifier same as geo

    """

    def setUp(self):
        super(ZivaLineOfActionUpdateNiceNameTestCase, self).setUp()
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

        self.scene_items_retrieved = self.builder.get_scene_items(type_filter=LineOfActionNode.type)
        self.l_item_geo = [
            x for x in self.scene_items_retrieved if x.association[0].startswith('l_')
        ]

    def test_builder_change_with_string_replace(self):
        super(ZivaLineOfActionUpdateNiceNameTestCase, self).builder_change_with_string_replace()

    def test_builder_build_with_string_replace(self):
        super(ZivaLineOfActionUpdateNiceNameTestCase, self).builder_build_with_string_replace()


class ZivaLineOfActionUpdateTestCase(ZivaUpdateTestCase):
    """This Class tests a specific type of "mirroring" so there are some assumptions made

    - geometry has an identifiable qualifier, in this case it is l_ and r_
    - Both sides geometry are in the scene
    - Both sides have Ziva nodes

    """

    def setUp(self):
        super(ZivaLineOfActionUpdateTestCase, self).setUp()
        load_scene('mirror_example-lineofaction_rivet.ma')
        self.builder = zva.Ziva()
        self.builder.retrieve_from_scene()

        # VERIFY
        self.compare_builder_nodes_with_scene_nodes(self.builder)
        self.compare_builder_attrs_with_scene_attrs(self.builder)

        # gather info
        self.scene_items_retrieved = self.builder.get_scene_items(type_filter=LineOfActionNode.type)
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
        super(ZivaLineOfActionUpdateTestCase, self).builder_change_with_string_replace()

    def test_builder_build_with_string_replace(self):
        super(ZivaLineOfActionUpdateTestCase, self).builder_build_with_string_replace()
