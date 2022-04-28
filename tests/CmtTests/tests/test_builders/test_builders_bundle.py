from maya import cmds
from tests.utils import load_scene, get_tmp_file_location
from vfx_test_case import VfxTestCase
from zBuilder.builders.ziva import Ziva


class BundleTestCase(VfxTestCase):

    def test_bundle_compare(self):
        """ Getting the generic scene and writing out a zBuilder file.
        This will allow us to retrieve file and copmpare it against scene.

        We are going to compare builder from this setUp and a builder retrieved from the file.
        """
        # Setup
        load_scene()
        file_name = get_tmp_file_location()

        cmds.select('zSolver1')
        builder_orig = Ziva()
        builder_orig.retrieve_from_scene()
        builder_orig.write(file_name)

        # Action: compare against this one
        cmds.select('zSolver1')
        builder_from_file = Ziva()
        builder_from_file.retrieve_from_file(file_name)

        # Verify: The bundles should be same
        self.assertEqual(builder_orig.bundle, builder_from_file.bundle)

        # Action: remove an element from one of them and should not be equal
        builder_from_file.bundle.scene_items.insert(10, builder_from_file.bundle.scene_items.pop(5))

        # Verify
        self.assertNotEqual(builder_orig.bundle, builder_from_file.bundle)
