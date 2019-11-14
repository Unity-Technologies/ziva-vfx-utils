import maya.cmds as mc

import zBuilder.builders.ziva as zva
from vfx_test_case import VfxTestCase
import tests.utils as test_utils


class ZivaBaseTestCase(VfxTestCase):
    @classmethod
    def setUpClass(cls):
        pass

    def setUp(self):
        pass

    def test_node_compares(self):
        """ Getting the generic scene and writing out a zBuilder file.  This will
        allow us to retrieve file and copmpare it against scene.

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

        # get item from eachbuilder
        item1 = builder_orig.get_scene_items(type_filter='zMaterial')[0]
        item2 = builder_from_file.get_scene_items(type_filter='zMaterial')[0]

        # should be same
        self.assertEqual(item1, item2)

        # change a value in one and compare
        item1.attrs['massDensity']['value'] = 70.0
        self.assertNotEqual(item1, item2)
