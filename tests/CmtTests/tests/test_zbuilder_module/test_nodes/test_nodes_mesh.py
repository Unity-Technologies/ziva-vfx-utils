import zBuilder.builders.ziva as zva

from maya import cmds
from vfx_test_case import VfxTestCase


class ZivaMeshTestCase(VfxTestCase):

    def setUp(self):
        super(ZivaMeshTestCase, self).setUp()
        cmds.polyCube(n='cube')
        cmds.move(1, 1, -1, 'cube')
        cmds.ziva(t=True)
        self.builder = zva.Ziva()
        self.builder.retrieve_from_scene()

    def test_mesh_mirror_assert(self):
        ball = self.builder.get_scene_items(name_filter='cube')[0]

        with self.assertRaises(Exception):
            ball.mirror(mirror_axis='DD')

    def test_mesh_mirror_axist(self):
        ball = self.builder.get_scene_items(name_filter='cube')[0]

        base_position = cmds.xform('cube.vtx[0]', q=True, ws=True, t=True)

        ball.mirror(mirror_axis='X')
        mesh = ball.build_mesh()
        new_position = cmds.xform(mesh + '.vtx[0]', q=True, ws=True, t=True)
        self.assertApproxEqual(base_position[0], -new_position[0])
        cmds.delete(mesh)

        ball.mirror(mirror_axis='Y')
        mesh = ball.build_mesh()
        new_position = cmds.xform(mesh + '.vtx[0]', q=True, ws=True, t=True)
        self.assertApproxEqual(base_position[1], -new_position[1])
        cmds.delete(mesh)

        ball.mirror(mirror_axis='Z')
        mesh = ball.build_mesh()
        new_position = cmds.xform(mesh + '.vtx[0]', q=True, ws=True, t=True)
        self.assertApproxEqual(base_position[2], -new_position[2])
        cmds.delete(mesh)