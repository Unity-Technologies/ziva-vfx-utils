from vfx_test_case import VfxTestCase

from maya import cmds
from maya import mel

import zBuilder.parameters.maps as maps
import zBuilder.builders.ziva as zva


class ZivaMapTestCase(VfxTestCase):
    def test_invert_map_command(self):
        # this tests command for inverting maps
        weight_list = [0, .4, .6, .5, 1]
        expected = [1, .6, .4, .5, 0]

        result = maps.invert_weights(weight_list)

        self.assertEqual(result, expected)

    def test_invert_map_through_zBuilder(self):
        # this tests the zBuilder interface for inverting maps
        # This is grabbing a zTet map to test against.

        sphere = cmds.polySphere()

        mel.eval('ziva -t {}'.format(sphere[0]))

        cmds.select(sphere[0])
        builder = zva.Ziva()
        builder.retrieve_from_scene()

        mp = builder.get_scene_items(type_filter='map')[0]

        expected_values = maps.invert_weights(mp.values)

        mp.invert()

        # compare the result to expected
        self.assertEqual(mp.values, expected_values)

    def test_apply_map(self):
        # this tests the zBuilder interface for applying a map to maya scene
        # This is grabbing a zTet map to test against.
        sphere = cmds.polySphere()

        mel.eval('ziva -t {}'.format(sphere[0]))

        cmds.select(sphere[0])
        builder = zva.Ziva()
        builder.retrieve_from_scene()

        tet_map = builder.get_scene_items(type_filter='map')[1]

        expected_values = [.2 for x in tet_map.values]

        # update node with expected
        tet_map.values = expected_values
        tet_map.apply_weights()

        # get from scene and compare
        scene_weights = cmds.getAttr('{}[0:{}]'.format(tet_map.name, len(tet_map.values) - 1))
        self.assertAllApproxEqual(scene_weights, expected_values)
