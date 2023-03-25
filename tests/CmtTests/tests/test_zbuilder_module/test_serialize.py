import os
import glob
import zBuilder.builders.ziva as zva
import zBuilder.builders.skinClusters as skn

from maya import cmds
from vfx_test_case import VfxTestCase
from tests.utils import (build_mirror_sample_geo, get_tmp_file_location,
                         build_anatomical_arm_with_no_popup, get_test_asset_path, load_scene)
from zBuilder.commands import clean_scene, load_rig
from zBuilder.builders.serialize import read, write


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

    def test_roundtrip_serialize(self):
        # Setup
        build_mirror_sample_geo()
        cmds.select(cl=True)
        # use builder to retrieve from scene
        self.z = zva.Ziva()
        self.z.retrieve_from_scene()
        old_names = [item.name for item in self.z.get_scene_items()]

        # Action
        file_name = get_tmp_file_location()
        write(file_name, self.z)
        self.temp_files.append(file_name)

        new_builder = zva.Ziva()
        read(file_name, new_builder)
        new_names = [item.name for item in new_builder.get_scene_items()]

        # Verify
        # simply check if file exists
        self.assertTrue(os.path.exists(file_name))

        # check the read back data matches with the one we wrote
        self.assertEqual(old_names, new_names)

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
        write(file_name, z)
        self.temp_files.append(file_name)

        clean_scene()
        z.build()

        # Verify
        self.assertSceneHasNodes(['r_bicep_muscle_zTissue'])
        # verify build_connections worked
        self.assertTrue(cmds.isConnected('remapValue1.outValue',
                                         'r_bicep_muscle_zFiber.excitation'))

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

    def test_read_write_backward_compatibility(self):
        # Setup
        builder = zva.Ziva()
        builder.retrieve_from_scene()
        file_name = get_tmp_file_location()

        # Act
        builder.write(file_name)
        old_names = [item.name for item in builder.get_scene_items()]

        new_builder = zva.Ziva()
        new_builder.retrieve_from_file(file_name)
        new_names = [item.name for item in new_builder.get_scene_items()]

        # Verify
        self.assertEqual(old_names, new_names)

    def test_build_1_7(self):
        builders_1_7 = glob.glob(get_test_asset_path('*1_7.zBuilder'))
        # Act
        for item in builders_1_7:
            # find corresponding maya file
            basename = os.path.basename(item)
            maya_file = basename.replace('_1_7.zBuilder', '.ma')

            # open it and clean scene so we have just geo
            load_scene(maya_file)
            clean_scene()

            builder = zva.Ziva()
            read(item, builder)

            builder.build()

            self.compare_builder_nodes_with_scene_nodes(builder)
            self.compare_builder_attrs_with_scene_attrs(builder)
            self.compare_builder_maps_with_scene_maps(builder)

    def test_skincluster_build_pre_version_2_2_0(self):
        """ This is added to test a backwards compatibility issue illustrated here:
        VFXACT-1687

        This is error message
        Error: AttributeError: file C:\git\ziva-vfx-utils-internal\zBuilder\nodes\deformers\skinCluster.py line 54: 'SkinCluster' object has no attribute 'parameters' # 
        """
        builders_2_1_0 = glob.glob(get_test_asset_path('*2_1_0.zBuilder'))
        # Act
        for item in builders_2_1_0:
            # find corresponding maya file
            basename = os.path.basename(item)
            maya_file = basename.replace('_2_1_0.zBuilder', '.ma')

            # open it and clean scene so we have just geo
            load_scene(maya_file)
            clean_scene()

            builder = skn.SkinCluster()
            read(item, builder)

            builder.build()

            self.compare_builder_nodes_with_scene_nodes(builder)
            self.compare_builder_attrs_with_scene_attrs(builder)
            self.compare_builder_maps_with_scene_maps(builder)