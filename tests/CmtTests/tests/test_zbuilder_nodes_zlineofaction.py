import os
import zBuilder.builders.ziva as zva
import tests.utils as test_utils
import zBuilder.utils as utils
import zBuilder.zMaya as mz
from maya import cmds
from maya import mel

from vfx_test_case import VfxTestCase


class ZivaLineOfActionGenericTestCase(VfxTestCase):
    @classmethod
    def setUpClass(cls):
        cls.loa_names = ["l_tissue_1_zLineOfAction", "r_subtissue_1_zLineOfAction"]
        cls.loa_attrs = ["maxExcitation", "stretchBias", "posSensitivity"]

    def setUp(self):
        super(ZivaLineOfActionGenericTestCase, self).setUp()
        test_utils.load_scene(scene_name="generic_tissue.ma")
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
        builder = self.get_builder_after_write_and_retrieve_from_file(self.builder)
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
        self.assertEqual(cmds.ls("r_tissue_2_zLineOfAction"), [])

        ## ACT
        mz.rename_ziva_nodes()

        ## VERIFY
        self.assertEqual(len(cmds.ls("r_tissue_2_zLineOfAction")), 1)

    def test_string_replace(self):
        ## VERIFY
        # check if an item exists before string_replace
        r_loa = self.builder.get_scene_items(name_filter="l_tissue_1_zLineOfAction")
        self.assertGreaterEqual(len(r_loa), 1)

        ## ACT
        self.builder.string_replace("^l_", "r_")

        ## VERIFY
        r_loa = self.builder.get_scene_items(name_filter="l_tissue_1_zLineOfAction")
        self.assertEqual(r_loa, [])

    def test_cut_paste(self):
        builder = self.get_builder_after_cut_paste("l_tissue_1", "l_tissue_1_zLineOfAction")
        self.check_retrieve_loa_looks_good(builder, {})

    def test_copy_paste(self):
        builder = self.get_builder_after_copy_paste("l_tissue_1", "l_tissue_1_zLineOfAction")
        self.check_retrieve_loa_looks_good(builder, {})

    def test_copy_paste_with_name_substitution(self):
        ## VERIFY
        # check if zLineOfAction does not exist before making it
        self.assertEqual(cmds.ls("r_tissue_1_zLineOfAction"), [])

        ## ACT
        cmds.select("l_tissue_1")
        utils.copy_paste_with_substitution("(^|_)l($|_)", "r")

        ## VERIFY
        self.assertEqual(len(cmds.ls("r_tissue_1_zLineOfAction")), 1)


class ZivaMultiCurveLoaTestCase(VfxTestCase):
    def setUp(self):
        super(ZivaMultiCurveLoaTestCase, self).setUp()
        # setup a scene with 2 curves on 1 zLineOfAction

        # create geometry
        cmds.polySphere(name='bone')
        cmds.setAttr('bone.translateY', 2)
        cmds.polySphere(name='tissue')

        # create zTissue and zBone
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
        mz.clean_scene()

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


class ZivaLineOfActionMirrorTestCase(VfxTestCase):
    """This Class tests a specific type of "mirroring" so there are some assumptions made

    - geometry has an identifiable qualifier, in this case it is l_ and r_
    - Both sides geometry are in the scene
    - One side has Ziva VFX nodes and other side does not, in this case l_ has Ziva nodes

    """

    def setUp(self):
        super(ZivaLineOfActionMirrorTestCase, self).setUp()
        test_utils.load_scene(scene_name='mirror_example-lineofaction_rivet.ma')
        self.builder = zva.Ziva()
        self.builder.retrieve_from_scene()

        # gather info
        self.type_ = 'zLineOfAction'
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
        from zBuilder.parameters.maps import get_weights
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
