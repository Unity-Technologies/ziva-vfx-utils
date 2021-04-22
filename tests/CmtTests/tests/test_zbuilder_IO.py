import zBuilder.builders.ziva as zva
from zBuilder.utils import clean_scene
from vfx_test_case import VfxTestCase
import tests.utils as test_utils
from maya import cmds
import os
import tempfile

class IOTestCase(VfxTestCase):
    def setUp(self):
        super(IOTestCase, self).setUp()
        # Build a basic setup
        test_utils.build_mirror_sample_geo()
        test_utils.ziva_mirror_sample_geo()

        cmds.select(cl=True)

        # use builder to retrieve from scene
        self.z = zva.Ziva()
        self.z.retrieve_from_scene()

        self.temp_files = []

    def tearDown(self):
        # delete temp files
        for temp_file in self.temp_files:
            if os.path.exists(temp_file):
                os.remove(temp_file)
        super(IOTestCase, self).tearDown()

    def test_builder_write(self):
        # find a temp file location
        temp = tempfile.TemporaryFile()

        # build it on live scene
        self.z.write(temp.name)

        self.temp_files.append(temp.name)

        # simply check if file exists, if it does it passes
        self.assertTrue(os.path.exists(temp.name))

    def test_builder_write_build(self):
        # tests a case where you write out a zBuilder file then immediatly build
        # this could potentially screw up during the build.

        # find a temp file location
        temp = tempfile.TemporaryFile()

        cmds.file(new=True, f=True)
        test_utils.build_anatomical_arm_with_no_popup()

        cmds.select('zSolver1')
        z = zva.Ziva()
        z.retrieve_from_scene()
        # build it on live scene
        z.write(temp.name)

        clean_scene()

        z.build()

        self.assertSceneHasNodes(['r_bicep_muscle_zTissue'])
