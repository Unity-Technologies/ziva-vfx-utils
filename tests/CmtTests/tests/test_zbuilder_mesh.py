import os
import zBuilder.builders.ziva as zva
import tests.utils as test_utils
from zBuilder.nodes.dg_node import DGNode

from vfx_test_case import VfxTestCase


class ZivaMeshTestCase(VfxTestCase):
    @classmethod
    def setUpClass(cls):
        cls.mesh_names = ['c_cloth_1',
                          'l_tissue_1',
                          'c_tissue_3',
                          'l_bone_1',
                          'r_subtissue_1',
                          'c_bone_1',
                          'c_bone_2',
                          'r_tissue_2']
        cls.mesh_attrs = []

    def setUp(self):
        super(ZivaMeshTestCase, self).setUp()
        test_utils.build_generic_scene()
        self.builder = zva.Ziva()
        self.builder.retrieve_from_scene()

    def tearDown(self):
        if os.path.exists(self.temp_file_path):
            os.remove(self.temp_file_path)
        super(ZivaMeshTestCase, self).tearDown()

    def check_retrieve_mesh_looks_good(self, builder):
        """Args:
            builder (builders.ziva.Ziva()): builder object
        """
        nodes = builder.geo
        for node in nodes.values():
            self.assertTrue(hasattr(node, 'depends_on'))
            self.assertIsInstance(node, DGNode)
        self.assertItemsEqual(self.mesh_names, [x.name for x in nodes.values()])

    def test_retrieve(self):
        self.check_retrieve_mesh_looks_good(self.builder)

    def test_retrieve_connections(self):
        builder = zva.Ziva()
        builder.retrieve_connections()
        self.check_retrieve_mesh_looks_good(builder)
