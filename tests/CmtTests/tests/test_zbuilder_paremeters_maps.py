from vfx_test_case import VfxTestCase

import maya.cmds as mc
import maya.mel as mm

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

        sphere = mc.polySphere()

        mm.eval('ziva -t {}'.format(sphere[0]))

        mc.select(sphere[0])
        builder = zva.Ziva()
        builder.retrieve_from_scene()

        mp = builder.get_scene_items(type_filter='map')[0]

        expected_values = maps.invert_weights(mp.values)

        mp.invert()

        # compare the result to expected
        self.assertEqual(mp.values, expected_values)
