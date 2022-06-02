import zBuilder.builders.ziva as zva

from maya import cmds
from vfx_test_case import VfxTestCase
from tests.utils import load_scene, get_tmp_file_location
from zBuilder.builders.serialize import read, write


class BaseNodeTestCase(VfxTestCase):

    def test_node_compares(self):
        """ Getting the generic scene and writing out a zBuilder file.
        This will allow us to retrieve file and copmpare it against scene.
        We are going to compare builder from this setUp and a builder retrieved from the file.
        """
        load_scene('generic.ma')
        file_name = get_tmp_file_location()

        cmds.select('zSolver1')
        builder_orig = zva.Ziva()
        builder_orig.retrieve_from_scene()
        write(file_name, builder_orig)
        # compare against this one
        cmds.select('zSolver1')
        builder_from_file = zva.Ziva()
        read(file_name, builder_from_file)

        # get item from eachbuilder
        item1 = builder_orig.get_scene_items(type_filter='zMaterial')[0]
        item2 = builder_from_file.get_scene_items(type_filter='zMaterial')[0]

        # should be same
        self.assertEqual(item1, item2)

        # change a value in one and compare
        item1.attrs['massDensity']['value'] = 70.0
        self.assertNotEqual(item1, item2)
