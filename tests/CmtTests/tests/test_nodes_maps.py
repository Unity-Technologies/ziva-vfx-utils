import zBuilder.builders.ziva as zva

from maya import cmds
from vfx_test_case import VfxTestCase, get_mesh_vertex_positions
from zBuilder.commands import clean_scene
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

    def test_apply_map_to_subdivided_mesh(self):
        ''' Regression test for VFXACT-1288.
        When retrieving then applying map to subdivided softbody mesh,
        zBuilder interpolates the map value.
        This test check the position of subdivided mesh's lowest center vertex.
        Before the fix, the vertex is locked by the attachment, due to wrong building result;
        After the fix, the vertex becomes free and be able to deform.
        '''
        # Setup: cube tissue's top face hangs under a cube bone
        cmds.polyCube(n='bone_cube')
        cmds.move(0, 5, 0)
        cmds.ziva(b=True)
        cmds.polyCube(n='tissue_cube', depth=5, height=5, width=5)
        cmds.ziva(t=True)
        # Select top face
        cmds.select("tissue_cube.vtx[2:5]", r=True)
        cmds.select("bone_cube", add=True)
        cmds.ziva(a=True)
        cmds.select(clear=True)
        cmds.setAttr("zMaterial1.youngsModulusExp", 0)  # Make tissue soft to deform
        builder = zva.Ziva()
        builder.retrieve_from_scene()

        # Action: subdivided the tissue mesh and rebuild
        clean_scene()
        cmds.polySmooth("tissue_cube")
        builder.build()

        # Verify: compare the the lowest vertex y position
        sub_mesh_vtx_y_pos_before_sim = get_mesh_vertex_positions("tissue_cube", 23)[1]
        cmds.currentTime(1)
        cmds.currentTime(2)
        sub_mesh_vtx_y_pos_after_sim = get_mesh_vertex_positions("tissue_cube", 23)[1]
        sub_mesh_vtx_y_pos_abs_diff = abs(sub_mesh_vtx_y_pos_after_sim -
                                          sub_mesh_vtx_y_pos_before_sim)
        # Before the fix, the vertex pos diff is nearly 0 because it is locked by attachment;
        # After the fix, it's not included by the attachment so it can deform freely.
        self.assertGreater(sub_mesh_vtx_y_pos_abs_diff, 1)