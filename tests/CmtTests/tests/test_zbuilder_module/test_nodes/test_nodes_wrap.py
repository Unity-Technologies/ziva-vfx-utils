import os

from maya import cmds
from maya import mel
from vfx_test_case import VfxTestCase, attr_values_from_scene
from zBuilder.builders.deformers import Deformers
from zBuilder.nodes.base import Base
from zBuilder.nodes.dg_node import DGNode
from zBuilder.builders.serialize import read, write


class WrapBuilderTestCase(VfxTestCase):

    @classmethod
    def setUpClass(cls):
        cls.blendShape_names = ["wrap1"]
        cls.blendShape_attrs = ["maxDistance", "autoWeightThreshold", "exclusiveBind"]

    def setUp(self):
        super(WrapBuilderTestCase, self).setUp()
        obj = cmds.polySphere(ch=False, n="l_skin_mesh")[0]
        obj2 = cmds.polySphere(ch=False, n="target")[0]
        cmds.select(obj, obj2)
        mel.eval('doWrapArgList "7" { "1","0","1", "2", "0", "1", "0", "0" }')

        self.builder = Deformers()
        cmds.select("l_skin_mesh")
        self.builder.retrieve_from_scene()

    def tearDown(self):
        if os.path.exists(self.temp_file_path):
            os.remove(self.temp_file_path)
        super(WrapBuilderTestCase, self).tearDown()

    def check_retrieve_wrap_looks_good(self, builder):
        """Args:
            builder (builders.skinClusters.SkinCluster()): builder object
        """
        self.check_retrieve_looks_good(builder, {}, self.blendShape_names, "wrap")

    def test_retrieve(self):
        self.check_retrieve_wrap_looks_good(self.builder)

    def test_build_restores_attr_values(self):
        plug_names = {
            "{}.{}".format(geo, attr)
            for geo in self.blendShape_names for attr in self.blendShape_attrs
        }
        attrs_before = attr_values_from_scene(plug_names)

        # remove all skinCluster nodes from the scene and build them
        cmds.select(cmds.ls(type="wrap"))
        mel.eval("doDelete;")
        self.builder.build()

        attrs_after = attr_values_from_scene(plug_names)
        self.assertEqual(attrs_before, attrs_after)

    def test_builder_has_same_wrap_nodes_after_writing_to_disk_and_reading(self):
        ## ACT
        write(self.temp_file_path, self.builder)

        ## VERIFY
        self.assertTrue(os.path.exists(self.temp_file_path))

        ## ACT
        builder = Deformers()
        read(self.temp_file_path, builder)

        ## VERIFY
        self.check_retrieve_wrap_looks_good(builder)

    def test_build(self):
        ## SETUP
        cmds.select(cmds.ls(type="wrap"))
        mel.eval("doDelete;")

        ## ACT
        self.builder.build()
        builder = Deformers()
        cmds.select("l_skin_mesh")
        builder.retrieve_from_scene()

        ## VERIFY
        self.check_retrieve_wrap_looks_good(builder)

    def test_build_from_file(self):
        ## SETUP
        write(self.temp_file_path, self.builder)
        self.assertTrue(os.path.exists(self.temp_file_path))
        cmds.select(cmds.ls(type="wrap"))
        mel.eval("doDelete;")

        ## ACT
        builder = Deformers()
        read(self.temp_file_path, builder)
        builder.build()

        ## VERIFY
        builder = Deformers()
        cmds.select("l_skin_mesh")
        builder.retrieve_from_scene()
        self.check_retrieve_wrap_looks_good(builder)

    def test_string_replace(self):
        ## VERIFY
        # check if an item exists before string_replace
        wrap = self.builder.get_scene_items(name_filter="wrap1")
        self.assertEqual(len(wrap), 1)

        ## ACT
        self.builder.string_replace("wrap1", "wrap2")

        ## VERIFY
        deltamush = self.builder.get_scene_items(name_filter="wrap1")
        self.assertEqual(deltamush, [])
        deltamush = self.builder.get_scene_items(name_filter="wrap2")
        self.assertEqual(len(deltamush), 1)

    def test_build_changes_attribute_value(self):
        ## SETUP
        cmds.setAttr('wrap1.maxDistance', .5)

        ## ACT
        self.builder.build()

        ## VERIFY
        self.assertEqual(cmds.getAttr('wrap1.maxDistance'), 1)

    def test_missing_mesh(self):
        ## SETUP
        cmds.rename("l_skin_mesh", "l_skin_meshOLD")

        ## VERIFY
        try:
            ## ACT
            self.builder.build()
        except ValueError:  # the Exception you receive before
            assert False, "This is not a warning!"

    def test_wrap_search_exclude_inheriting(self):
        # searching through every scene item
        # Check if inherited from Base.
        # Check if ALL Base.SEARCH_EXCLUDE items are in item.SEARCH_EXCLUDE
        # This broke previously when the inheritence was overridding instead of extending
        # Any new nodes that do not inherit proprely will break here
        for item in self.builder.get_scene_items(type_filter='wrap'):
            if isinstance(item, Base):
                # This will assert if any scene item does not contain Base.SEARCH_EXCLUDE items
                self.assertTrue(all(x in item.SEARCH_EXCLUDE for x in Base.SEARCH_EXCLUDE))
            if isinstance(item, DGNode):
                # This will assert if any scene item does not contain DGNode.SEARCH_EXCLUDE items
                self.assertTrue(all(x in item.SEARCH_EXCLUDE for x in DGNode.SEARCH_EXCLUDE))