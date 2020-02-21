import zBuilder.builders.ziva as zva
import tests.utils as test_utils
import zBuilder.zMaya as mz

from vfx_test_case import VfxTestCase, ZivaMirrorTestCase, ZivaMirrorNiceNameTestCase

NODE_TYPE = 'zSolverTransform'


class ZivaSolverTransformMirrorTestCase(ZivaMirrorTestCase):
    """This Class tests a specific type of "mirroring" so there are some assumptions made

    - geometry has an identifiable qualifier, in this case it is l_ and r_
    - Both sides geometry are in the scene
    - One side has Ziva VFX nodes and other side does not, in this case l_ has Ziva nodes
    - Ziva nodes are named default like so: zSolverTransform1, zSolverTransform2, zSolverTransform3

    """

    def setUp(self):
        super(ZivaSolverTransformMirrorTestCase, self).setUp()

        test_utils.load_scene(scene_name='mirror_example.ma')
        self.builder = zva.Ziva()
        self.builder.retrieve_from_scene()
        # gather info
        self.scene_items_retrieved = self.builder.get_scene_items(type_filter=NODE_TYPE)
        self.l_item_geo = []

    def test_builder_change_with_string_replace(self):
        super(ZivaSolverTransformMirrorTestCase, self).builder_change_with_string_replace()

    def test_builder_build_with_string_replace(self):
        super(ZivaSolverTransformMirrorTestCase, self).builder_build_with_string_replace()


class ZivaSolverTransformMirrorNiceNameTestCase(ZivaMirrorNiceNameTestCase):
    """This Class tests a specific type of "mirroring" so there are some assumptions made

    - geometry has an identifiable qualifier, in this case it is l_ and r_
    - Both sides geometry are in the scene
    - One side has Ziva VFX nodes and other side does not, in this case l_ has Ziva nodes

    """

    def setUp(self):
        super(ZivaSolverTransformMirrorNiceNameTestCase, self).setUp()
        # gather info

        # Bring in scene
        test_utils.load_scene(scene_name='mirror_example.ma')

        # force NICE NAMES
        mz.rename_ziva_nodes()

        self.builder = zva.Ziva()
        self.builder.retrieve_from_scene()

        self.scene_items_retrieved = self.builder.get_scene_items(type_filter=NODE_TYPE)
        self.l_item_geo = []

    def test_builder_change_with_string_replace(self):
        super(ZivaSolverTransformMirrorNiceNameTestCase, self).builder_change_with_string_replace()

    def test_builder_build_with_string_replace(self):
        super(ZivaSolverTransformMirrorNiceNameTestCase, self).builder_build_with_string_replace()
