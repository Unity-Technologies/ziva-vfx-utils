import copy
import os
import maya.cmds as mc
import zBuilder.zMaya
import zBuilder.zMaya as mz
import zBuilder.builders.ziva as zva
from vfx_test_case import VfxTestCase, attr_values_from_zbuilder_nodes
import tests.utils as test_utils
from tests.utils import retrieve_builder_from_scene, retrieve_builder_from_file


class ZivaBuilderTestCase(VfxTestCase):
    def setUp(self):
        super(ZivaBuilderTestCase, self).setUp()
        test_utils.build_generic_scene()

    def test_builders_built_the_same_way_are_equal_until_modified(self):
        # Act
        builder1 = retrieve_builder_from_scene()
        builder2 = retrieve_builder_from_scene()

        # Verify
        self.assertEqual(builder1, builder2)

        # Act
        builder2.get_scene_items(type_filter='zMaterial')[0].attrs['massDensity']['value'] += 777

        # Verify
        self.assertNotEqual(builder1, builder2)

    def test_builder_written_and_read_from_file_is_equal_to_original(self):
        # Setup
        builder_orig = retrieve_builder_from_scene()
        file_name = test_utils.get_tmp_file_location()

        # Act
        builder_orig.write(file_name)
        builder_from_file = retrieve_builder_from_file(file_name)

        # Verify
        self.assertTrue(os.path.exists(file_name))
        self.assertEqual(builder_orig, builder_from_file)

    def test_deepcopy_of_builder_is_equal_to_original(self):
        # Setup
        builder_orig = retrieve_builder_from_scene()

        # Act
        builder_from_deepcopy = copy.deepcopy(builder_orig)

        # Verify
        self.assertEqual(builder_orig, builder_from_deepcopy)

    def test_build_does_not_change_builder(self):
        # Setup
        builder = retrieve_builder_from_scene()
        builder_orig = copy.deepcopy(builder)

        # Act
        zBuilder.zMaya.clean_scene()
        builder.build()

        # Verify
        self.assertEqual(builder, builder_orig)

    def test_retrieving_multiple_times_with_new_attributes_gets_the_new_attributes(self):
        # Setup
        material_plug = mc.ls(type='zMaterial')[0] + '.youngsModulus'
        mc.setAttr(material_plug, 111)
        builder = retrieve_builder_from_scene()
        old_names = [item.name for item in builder.get_scene_items()]

        # Act
        mc.setAttr(material_plug, 222)
        builder = retrieve_builder_from_scene()

        # Verify
        new_names = [item.name for item in builder.get_scene_items()]
        material_items = builder.get_scene_items(type_filter='zMaterial')
        attrs = attr_values_from_zbuilder_nodes(material_items)
        self.assertEqual(attrs.get(material_plug), 222)
        self.assertEqual(old_names, new_names)

    def test_retrieving_the_same_scene_with_new_nodes_does_not_change_the_list_of_scene_items(self):
        # Setup
        builder = zva.Ziva()
        builder.retrieve_from_scene()
        old_names = [item.name for item in builder.get_scene_items()]

        # Act
        mz.clean_scene()
        builder.build()  # Make the same scene, but with all new Ziva nodes
        builder.retrieve_from_scene()
        new_names = [item.name for item in builder.get_scene_items()]

        # Verify
        self.assertEqual(old_names, new_names)
