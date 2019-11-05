import os
import copy
import zBuilder.builders.ziva as zva
import tests.utils as test_utils
import zBuilder.zMaya as mz
import maya.OpenMaya as om

from vfx_test_case import VfxTestCase, attr_values_from_scene, attr_values_from_zbuilder_nodes

class ZivaTissueGenericTestCase(VfxTestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp_file_path = test_utils.get_tmp_file_location()
        cls.tissue_names = ["l_tissue_1_zTissue",
                            "r_tissue_2_zTissue",
                            "c_tissue_3_zTissue",
                            "r_subtissue_1_zTissue"]
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
            
        self.assertItemsEqual(self.tissue_names, [x.name for x in tissue_nodes])

        for node in tissue_nodes:
            self.assertEqual(node.type, "zTissue")
            self.assertIsInstance(node.mobject, om.MObject)

        zbuilder_plugs = attr_values_from_zbuilder_nodes(tissue_nodes)
        expected_plugs = expected_plugs or attr_values_from_scene(zbuilder_plugs.keys())
        self.assertGreaterEqual(zbuilder_plugs, expected_plugs)

    def test_retrieve(self):
        self.check_retrieve_ztissue_looks_good(self.builder, {})

    def test_builder_is_unchanged_by_roundtrip_to_disk(self):
        self.builder.write(self.temp_file_path)
        self.assertTrue(os.path.exists(self.temp_file_path))

        retrieved_builder = zva.Ziva()
        retrieved_builder.retrieve_from_file(self.temp_file_path)
        self.assertEqual(self.builder, retrieved_builder)

    def test_build_restores_attr_values(self):
        plug_names = {'{}.{}'.format(geo, attr) for geo in self.tissue_names 
                                                for attr in self.tissue_attrs}
        attrs_before = attr_values_from_scene(plug_names)

        # remove all Ziva nodes from the scene and build them
        mz.clean_scene()
        self.builder.build()

        attrs_after = attr_values_from_scene(plug_names)
        self.assertEqual(attrs_before, attrs_after)
