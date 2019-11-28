import maya.cmds as mc

import zBuilder.builders.ziva as zva
from vfx_test_case import VfxTestCase
import tests.utils as test_utils


class ZivaBundleTestCase(VfxTestCase):
    def test_bundle_compare(self):
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

        # The bundles should be same
        self.assertEqual(builder_orig.bundle, builder_from_file.bundle)

        # remove an element from one of them and should not be equal
        builder_from_file.bundle.scene_items.insert(10, builder_from_file.bundle.scene_items.pop(5))

        self.assertNotEqual(builder_orig.bundle, builder_from_file.bundle)
