import maya.cmds as mc

import os
import zBuilder.builders.ziva as zva
import tests.utils as test_utils
import zBuilder.zMaya as mz

import maya.OpenMaya as om

from vfx_test_case import VfxTestCase


class ZivaTissueGenericTestCase(VfxTestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp_file_path = test_utils.get_tmp_file_location()
        cls.tissue_geo_names = ["l_tissue_1",
                                "r_tissue_2",
                                "c_tissue_3",
                                "r_subtissue_1"]
        cls.tissue_attrs = ['inertialDamping',
                            'pressureEnvelope',
                            'collisions']

    def setUp(self):
        super(ZivaTissueGenericTestCase, self).setUp()
        test_utils.build_generic_scene()
        self.builder = zva.Ziva()
        self.builder.retrieve_from_scene()

    def tearDown(self):
        super(ZivaTissueGenericTestCase, self).tearDown()
        if os.path.exists(self.temp_file_path):
            os.remove(self.temp_file_path)

    def check_retrieve_ztissue_looks_good(self, builder, attrs):
        """Args:
            builder (builders.ziva.Ziva()): builder object
            attrs (dict): compares to stored zBuilder values for zTissue
                          if empty - getting values from the scene
                          {tissue_geo_name:[values for self.tissue_attrs]}
        """
        # get tissue from zBuilder
        tissue_nodes = builder.get_scene_items(type_filter='zTissue')

        self.assertEqual(len(tissue_nodes), 4)

        for node in tissue_nodes:
            geo_name = node.name.replace("_zTissue", "")
            self.assertIn(geo_name, self.tissue_geo_names)
            self.assertEqual(node.type, "zTissue")
            self.assertIsInstance(node.mobject, om.MObject)

            for i, attr in enumerate(self.tissue_attrs):
                if attrs:
                    value = attrs[geo_name][i]
                else:
                    value = mc.getAttr("{}.{}".format(node.name, attr))
                self.assertTrue(value == node.attrs[attr]['value'])

    def test_retrieve(self):
        self.check_retrieve_ztissue_looks_good(self.builder, {})

    def check_ztissue_looks_good(self, builder):
        tissue_nodes = builder.get_scene_items(type_filter='zTissue')
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
        tissue_attrs_dict = {}
        for name in self.tissue_geo_names:
            tissue_values = []
            for attr in self.tissue_attrs:
                value = mc.getAttr("{}.{}".format(name + "_zTissue", attr))
                tissue_values.append(value)
            tissue_attrs_dict[name] = tissue_values

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
        retrieved_builder.retrieve_from_scene()
        self.check_retrieve_ztissue_looks_good(retrieved_builder, {})
