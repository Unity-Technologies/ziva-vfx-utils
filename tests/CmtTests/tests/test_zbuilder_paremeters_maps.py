import zBuilder.builders.ziva as zva

from maya import cmds
from vfx_test_case import VfxTestCase
from zBuilder.nodes.parameters.maps import invert_weights


class ZivaMapTestCase(VfxTestCase):

    def test_invert_map_command(self):
        # Setup
        weight_list = [0, .4, .6, .5, 1]
        expected = [1, .6, .4, .5, 0]
        # Action
        result = invert_weights(weight_list)
        # Verify
        self.assertEqual(result, expected)

    def test_invert_map_through_zBuilder(self):
        ''' Tests the zBuilder interface for inverting maps.
        This is grabbing a zTet map to test against.
        '''
        # Setup
        sphere = cmds.polySphere()
        cmds.ziva(sphere[0], t=True)
        cmds.select(sphere[0])
        builder = zva.Ziva()
        builder.retrieve_from_scene()
        mp = builder.get_scene_items(type_filter='map')[0]
        expected_values = invert_weights(mp.values)

        # Action
        mp.invert()

        # Verify
        self.assertEqual(mp.values, expected_values)

    def test_apply_map(self):
        ''' Tests the zBuilder interface for applying a map to maya scene.
        This is grabbing a zTet map to test against.
        '''
        # Setup
        sphere = cmds.polySphere()
        results = cmds.ziva(sphere[0], t=True)
        tet_name = results[5]
        cmds.select(sphere[0])
        builder = zva.Ziva()
        builder.retrieve_from_scene()
        tet_node = builder.get_scene_items(name_filter=tet_name)[0]
        tet_map = tet_node.parameters['map'][0]
        expected_values = [.2 for x in tet_map.values]

        # Action
        tet_map.values = expected_values
        tet_map.apply_weights()

        # Verify
        scene_weights = cmds.getAttr('{}[0:{}]'.format(tet_map.name, len(tet_map.values) - 1))
        self.assertAllApproxEqual(scene_weights, expected_values)
