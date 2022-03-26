import os
import tests.utils as test_utils
import zBuilder.builders.ziva as zva

from maya import cmds
from vfx_test_case import VfxTestCase
from zBuilder.utils import clean_scene, load_rig


class IOTestCase(VfxTestCase):

    def setUp(self):
        super(IOTestCase, self).setUp()
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
        super(IOTestCase, self).tearDown()

    def test_builder_write(self):
        # Setup
        test_utils.build_mirror_sample_geo()
        test_utils.ziva_mirror_sample_geo()
        cmds.select(cl=True)
        # use builder to retrieve from scene
        self.z = zva.Ziva()
        self.z.retrieve_from_scene()

        # Action
        file_name = test_utils.get_tmp_file_location()
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
        test_utils.build_anatomical_arm_with_no_popup()
        cmds.select('zSolver1')
        z = zva.Ziva()
        z.retrieve_from_scene()

        # Action
        file_name = test_utils.get_tmp_file_location()
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
        tissue_setup = test_utils.get_test_asset_path('tissue.zBuilder')

        # Action
        load_rig(tissue_setup)

        # Verify
        self.assertSceneHasNodes(['zSolver1'])
