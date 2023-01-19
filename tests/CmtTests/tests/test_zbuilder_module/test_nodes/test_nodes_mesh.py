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
        cube = self.builder.get_scene_items(name_filter='cube')[0]

        with self.assertRaises(AssertionError):
            cube.mirror(mirror_axis='DD')

    def test_mesh_mirror_axist(self):
        cube = self.builder.get_scene_items(name_filter='cube')[0]

        base_position = cmds.xform('cube.vtx[0]', q=True, ws=True, t=True)

        cube.mirror(mirror_axis='X')
        mesh = cube.build_mesh()
        new_position = cmds.xform(mesh + '.vtx[0]', q=True, ws=True, t=True)
        self.assertApproxEqual(base_position[0], -new_position[0])
        cmds.delete(mesh)

        cube.mirror(mirror_axis='Y')
        mesh = cube.build_mesh()
        new_position = cmds.xform(mesh + '.vtx[0]', q=True, ws=True, t=True)
        self.assertApproxEqual(base_position[1], -new_position[1])
        cmds.delete(mesh)

        cube.mirror(mirror_axis='Z')
        mesh = cube.build_mesh()
        new_position = cmds.xform(mesh + '.vtx[0]', q=True, ws=True, t=True)
        self.assertApproxEqual(base_position[2], -new_position[2])
        cmds.delete(mesh)