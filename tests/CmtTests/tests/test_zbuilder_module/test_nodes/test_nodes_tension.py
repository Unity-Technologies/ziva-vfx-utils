import os

from maya import cmds
from vfx_test_case import VfxTestCase, attr_values_from_scene
from zBuilder.builders.deformers import Deformers
from zBuilder.nodes.base import Base
from zBuilder.nodes.dg_node import DGNode
from zBuilder.builders.serialize import read, write


class TensionBuilderTestCase(VfxTestCase):

    tension_names = ["tension1"]
    tension_attrs = ["smoothingIterations", "smoothingStep", "inwardConstraint"]

    def setUp(self):
        super(TensionBuilderTestCase, self).setUp()
        obj = cmds.polySphere(ch=False, n="l_skin_mesh")[0]
        cmds.select(obj)
        cmds.Tension()

        self.builder = Deformers()
        cmds.select("l_skin_mesh")
        self.builder.retrieve_from_scene()

    def tearDown(self):
        if os.path.exists(self.temp_file_path):
            os.remove(self.temp_file_path)
        super(TensionBuilderTestCase, self).tearDown()

    def check_retrieve_tension_looks_good(self, builder):
        """Args:
            builder (builders.skinClusters.SkinCluster()): builder object
        """
        self.check_retrieve_looks_good(builder, {}, TensionBuilderTestCase.tension_names, "tension")

    def test_retrieve(self):
        self.check_retrieve_tension_looks_good(self.builder)

    def test_build_restores_attr_values(self):
        plug_names = [
            "{}.{}".format(geo, attr)
            for geo in TensionBuilderTestCase.tension_names for attr in TensionBuilderTestCase.tension_attrs
        ]
        attrs_before = attr_values_from_scene(plug_names)

        # remove all tension nodes from the scene and build them
        cmds.select(cmds.ls(type="tension"))
        cmds.delete()
        self.builder.build()

        attrs_after = attr_values_from_scene(plug_names)
        self.assertEqual(attrs_before, attrs_after)

    def test_builder_has_same_tension_nodes_after_writing_to_disk(self):
        ## ACT
        write(self.temp_file_path, self.builder)

        ## VERIFY
        self.assertTrue(os.path.exists(self.temp_file_path))

        ## ACT
        builder = Deformers()
        read(self.temp_file_path, builder)

        ## VERIFY
        self.check_retrieve_tension_looks_good(builder)

    def test_build(self):
        ## SETUP
        cmds.select(cmds.ls(type="tension"))
        cmds.delete()

        ## ACT
        self.builder.build()
        builder = Deformers()
        cmds.select("l_skin_mesh")
        builder.retrieve_from_scene()

        ## VERIFY
        self.check_retrieve_tension_looks_good(builder)

    def test_build_from_file(self):
        ## SETUP
        write(self.temp_file_path, self.builder)
        self.assertTrue(os.path.exists(self.temp_file_path))
        cmds.select(cmds.ls(type="tension"))
        cmds.delete()

        ## ACT
        builder = Deformers()
        read(self.temp_file_path, builder)
        builder.build()

        builder = Deformers()
        cmds.select("l_skin_mesh")
        builder.retrieve_from_scene()
        self.check_retrieve_tension_looks_good(builder)

    def test_string_replace(self):
        ## VERIFY
        # check if an item exists before string_replace
        tension = self.builder.get_scene_items(name_filter="tension1")
        self.assertEqual(len(tension), 1)

        ## ACT
        self.builder.string_replace("tension1", "tension2")

        ## VERIFY
        tension = self.builder.get_scene_items(name_filter="tension1")
        self.assertEqual(tension, [])
        tension = self.builder.get_scene_items(name_filter="tension2")
        self.assertEqual(len(tension), 1)

    def test_build_changes_attribute_value(self):
        ## SETUP
        cmds.setAttr('tension1.smoothingIterations', 2)

        ## ACT
        self.builder.build()

        ## VERIFY
        self.assertEqual(cmds.getAttr('tension1.smoothingIterations'), 10)

    def test_tension_search_exclude_inheriting(self):
        # searching through every scene item
        # Check if inherited from Base.
        # Check if ALL Base.SEARCH_EXCLUDE items are in item.SEARCH_EXCLUDE
        # This broke previously when the inheritence was overridding instead of extending
        # Any new nodes that do not inherit proprely will break here
        for item in self.builder.get_scene_items(type_filter='tension'):
            if isinstance(item, Base):
                # This will assert if any scene item does not contain Base.SEARCH_EXCLUDE items
                self.assertTrue(all(x in item.SEARCH_EXCLUDE for x in Base.SEARCH_EXCLUDE))
            if isinstance(item, DGNode):
                # This will assert if any scene item does not contain DGNode.SEARCH_EXCLUDE items
                self.assertTrue(all(x in item.SEARCH_EXCLUDE for x in DGNode.SEARCH_EXCLUDE))