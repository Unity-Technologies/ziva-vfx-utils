import os
import zBuilder.builders.ziva as zva

from maya import cmds
from vfx_test_case import VfxTestCase
from tests.utils import (build_mirror_sample_geo, get_tmp_file_location,
                         build_anatomical_arm_with_no_popup, get_test_asset_path)
from zBuilder.commands import clean_scene, load_rig


class SerializeTestCase(VfxTestCase):

    def setUp(self):
        super(SerializeTestCase, self).setUp()
        self.temp_files = []
        # NOTE: Leave setup() function not running any zBuilder class registration code
        # to make test_0load_zBuilder_file() unit test work.
        # The test_0load_zBuilder_file() verifies the zBuilder node types have been registered
        # before loading zBuilder setup. It happens implicitly in the __init__.py, zBuilder.nodes package.

    def tearDown(self):
        # delete temp files
        for temp_file in self.temp_files:
            if os.path.exists(temp_file):
                os.remove(temp_file)
        super(SerializeTestCase, self).tearDown()

    def test_builder_write(self):
        # Setup
        build_mirror_sample_geo()
        cmds.select(cl=True)
        # use builder to retrieve from scene
        self.z = zva.Ziva()
        self.z.retrieve_from_scene()

        # Action
        file_name = get_tmp_file_location()
        self.z.write(file_name)
        self.temp_files.append(file_name)

        # Verify
        # simply check if file exists
        self.assertTrue(os.path.exists(file_name))

    def test_builder_write_build(self):
        '''
        Write out a zBuilder file then immediatly build.
        This could potentially screw up during the build.
        '''

        # Setup
        cmds.file(new=True, f=True)
        build_anatomical_arm_with_no_popup()
        cmds.select('zSolver1')
        z = zva.Ziva()
        z.retrieve_from_scene()

        # Action
        file_name = get_tmp_file_location()
        z.write(file_name)
        self.temp_files.append(file_name)

        clean_scene()
        z.build()

        # Verify
        self.assertSceneHasNodes(['r_bicep_muscle_zTissue'])

    def test_0load_zBuilder_file(self):
        '''
        This test covers VFXACT-955 ticket, a regression in v1.1.0
        The test case name starts with '0' is on purpose,
        to make it run before other cases, 
        otherwise the missing module will load and assert won't trigger.
        '''
        # Setup
        cmds.polySphere()
        tissue_setup = get_test_asset_path('tissue.zBuilder')

        # Action
        load_rig(tissue_setup)

        # Verify
        self.assertSceneHasNodes(['zSolver1'])
