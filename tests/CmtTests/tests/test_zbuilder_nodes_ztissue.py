import os
import zBuilder.builders.ziva as zva
import tests.utils as test_utils
import zBuilder.zMaya as mz
import maya.OpenMaya as om

from vfx_test_case import VfxTestCase, attr_values_from_scene, attr_values_from_zbuilder_nodes

class ZivaTissueGenericTestCase(VfxTestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp_file_path = test_utils.get_tmp_file_location()
        cls.tissue_geo_names = ["l_tissue_1",
                                "r_tissue_2",
                                "c_tissue_3",
                                "r_subtissue_1"]
        cls.tissue_attrs = ["inertialDamping",
                            "pressureEnvelope",
                            "collisions"]

    def setUp(self):
        super(ZivaTissueGenericTestCase, self).setUp()
        test_utils.build_generic_scene()
        self.builder = zva.Ziva()
        self.builder.retrieve_from_scene()

    def tearDown(self):
        super(ZivaTissueGenericTestCase, self).tearDown()
        if os.path.exists(self.temp_file_path):
            os.remove(self.temp_file_path)

    def check_retrieve_ztissue_looks_good(self, builder, expected_plugs):
        """Args:
            builder (builders.ziva.Ziva()): builder object
            attrs (dict): A dict of expected attribute/value pairs.
                          {'zTissue1.collisions':True, ...}.
                          If None/empty/False, then attributes are taken from zBuilder
                          and values are taken from the scene.
                          Test fails if zBuilder is missing any of the keys
                          or has any keys with different values.
        """        
        tissue_nodes = builder.get_scene_items(type_filter="zTissue")
            
        self.assertEqual(len(tissue_nodes), len(self.tissue_geo_names))

        for node in tissue_nodes:
            geo_name = node.name.replace("_zTissue", "")
            self.assertIn(geo_name, self.tissue_geo_names)
            self.assertEqual(node.type, "zTissue")
            self.assertIsInstance(node.mobject, om.MObject)

        zbuilder_plugs = attr_values_from_zbuilder_nodes(tissue_nodes)
        expected_plugs = expected_plugs or attr_values_from_scene(zbuilder_plugs.keys())
        self.assertGreaterEqual(zbuilder_plugs, expected_plugs)

    def test_retrieve(self):
        self.check_retrieve_ztissue_looks_good(self.builder, {})

    def check_ztissue_looks_good(self, builder):
        tissue_nodes = builder.get_scene_items(type_filter="zTissue")
        self.assertEqual(len(tissue_nodes), 4)

        for node in tissue_nodes:
            geo_name = node.name.replace("_zTissue", "")
            self.assertIn(geo_name, self.tissue_geo_names)
            self.assertEqual(node.type, "zTissue")

    def test_builder_has_same_tissue_node_after_roundtrip_to_disk(self):
        self.builder.write(self.temp_file_path)
        self.assertTrue(os.path.exists(self.temp_file_path))

        retrieved_builder = zva.Ziva()
        retrieved_builder.retrieve_from_file(self.temp_file_path)
        self.check_ztissue_looks_good(retrieved_builder)

    def test_build(self):
        plug_names = {'{}_zTissue.{}'.format(geo, attr) for geo in self.tissue_geo_names 
                                                        for attr in self.tissue_attrs}
        tissue_attrs_dict = attr_values_from_scene(plug_names)

        # remove all Ziva nodes from the scene and build them
        mz.clean_scene()
        self.builder.build()

        self.check_retrieve_ztissue_looks_good(self.builder, tissue_attrs_dict)

    def test_build_from_file(self):
        self.builder.write(self.temp_file_path)

        retrieved_builder = zva.Ziva()
        retrieved_builder.retrieve_from_file(self.temp_file_path)
        mz.clean_scene()
        retrieved_builder.build()
        # update zBuilder values from the scene
        retrieved_builder = zva.Ziva()
        retrieved_builder.retrieve_from_scene()
        self.check_retrieve_ztissue_looks_good(retrieved_builder, {})
