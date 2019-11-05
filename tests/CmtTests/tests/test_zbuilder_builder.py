import copy
import maya.cmds as mc

import zBuilder.builders.ziva as zva
import zBuilder.zMaya
from vfx_test_case import VfxTestCase
import tests.utils as test_utils


class ZivaBuilderTestCase(VfxTestCase):
    @classmethod
    def setUpClass(cls):
        pass

    def setUp(self):
        pass

    def test_builder_compare(self):
        """ Getting the generic scene and writing out a zBuilder file.  This will
        allow us to retrieve file and compare it against scene.

        We are going to compare builder from this setUp and a builder retrieved from 
        the file.
        """
        test_utils.build_generic_scene()
        file_name = test_utils.get_tmp_file_location()

        mc.select('zSolver1')
        builder_orig = zva.Ziva()
        builder_orig.retrieve_from_scene()
        builder_orig.write(file_name)
        # compare against this one
        mc.select('zSolver1')
        builder_from_file = zva.Ziva()
        builder_from_file.retrieve_from_file(file_name)
        # The bundles should be same
        self.assertEqual(builder_orig, builder_from_file)

        # change an item in the builder, lets compare.  should be not equal
        # in this case changing an attribute value.
        builder_from_file.get_scene_items(
            name_filter='c_tissue_3_zMaterial')[0].attrs['massDensity']['value'] = 1070.0

        self.assertFalse(builder_orig == builder_from_file)

    def test_builder_deepcopy_compare(self):
        """ Getting the generic scene and comparing 2 retrieves to retrieve.

        We are going to compare the 2 builders
        """
        test_utils.build_generic_scene()

        mc.select('zSolver1')
        builder_orig = zva.Ziva()
        builder_orig.retrieve_from_scene()
        builder_from_deepcopy = copy.deepcopy(builder_orig)

        # The bundles should be same
        self.assertEqual(builder_orig, builder_from_deepcopy)

        # change an item in the builder, lets compare.  should be not equal
        # in this case changing an attribute value.
        builder_from_deepcopy.get_scene_items(
            name_filter='c_tissue_3_zMaterial')[0].attrs['massDensity']['value'] = 1070.0

        self.assertFalse(builder_orig == builder_from_deepcopy)

    def test_build_does_not_change_builder(self):
        # Setup
        test_utils.build_generic_scene()
        builder = zva.Ziva()
        builder.retrieve_from_scene()
        orig_builder = copy.deepcopy(builder)
        zBuilder.zMaya.clean_scene()

        # Act
        builder.build()
        
        # Verify
        self.assertEqual(builder, orig_builder)
