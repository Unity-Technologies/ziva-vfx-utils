import os

from maya import cmds
from maya import mel
from vfx_test_case import VfxTestCase, attr_values_from_scene
from zBuilder.builders.deformers import Deformers
from zBuilder.nodes.base import Base
from zBuilder.nodes.dg_node import DGNode
from zBuilder.builders.serialize import read, write


class BlendshapeBuilderTestCase(VfxTestCase):

    @classmethod
    def setUpClass(cls):
        cls.blendShape_names = ["blendShape1"]
        cls.blendShape_attrs = ["supportNegativeWeights", "origin", "target1", "target2"]

    def setUp(self):
        super(BlendshapeBuilderTestCase, self).setUp()
        obj = cmds.polySphere(ch=False, n="l_skin_mesh")[0]
        obj2 = cmds.polySphere(ch=False, n="target1")[0]
        obj3 = cmds.polySphere(ch=False, n="target2")[0]
        cmds.select(obj3, obj2, obj)
        cmds.blendShape()

        self.builder = Deformers()
        cmds.select("l_skin_mesh")
        self.builder.retrieve_from_scene()

    def tearDown(self):
        if os.path.exists(self.temp_file_path):
            os.remove(self.temp_file_path)
        super(BlendshapeBuilderTestCase, self).tearDown()

    def check_retrieve_blendShape_looks_good(self, builder):
        """Args:
            builder (builders.skinClusters.SkinCluster()): builder object
        """
        self.check_retrieve_looks_good(builder, {}, self.blendShape_names, "blendShape")

    def test_retrieve(self):
        self.check_retrieve_blendShape_looks_good(self.builder)

    def test_build_restores_attr_values(self):
        plug_names = {
            "{}.{}".format(geo, attr)
            for geo in self.blendShape_names for attr in self.blendShape_attrs
        }
        attrs_before = attr_values_from_scene(plug_names)

        # remove all skinCluster nodes from the scene and build them
        cmds.select(cmds.ls(type="blendShape"))
        mel.eval("doDelete;")
        self.builder.build()

        attrs_after = attr_values_from_scene(plug_names)
        self.assertEqual(attrs_before, attrs_after)

    def test_builder_has_same_blendShape_nodes_after_writing_to_disk(self):
        ## ACT
        write(self.temp_file_path, self.builder)

        ## VERIFY
        self.assertTrue(os.path.exists(self.temp_file_path))

        ## ACT
        builder = Deformers()
        read(self.temp_file_path, builder)

        ## VERIFY
        self.check_retrieve_blendShape_looks_good(builder)

    def test_build(self):
        ## SETUP
        cmds.select(cmds.ls(type="blendShape"))
        mel.eval("doDelete;")

        ## ACT
        self.builder.build()
        builder = Deformers()
        cmds.select("l_skin_mesh")
        builder.retrieve_from_scene()

        ## VERIFY
        self.check_retrieve_blendShape_looks_good(builder)

    def test_build_from_file(self):
        ## SETUP
        write(self.temp_file_path, self.builder)
        self.assertTrue(os.path.exists(self.temp_file_path))
        cmds.select(cmds.ls(type="blendShape"))
        mel.eval("doDelete;")

        ## ACT
        builder = Deformers()
        read(self.temp_file_path, builder)
        builder.build()

        ## VERIFY
        builder = Deformers()
        cmds.select("l_skin_mesh")
        builder.retrieve_from_scene()
        self.check_retrieve_blendShape_looks_good(builder)

    def test_string_replace(self):
        ## VERIFY
        # check if an item exists before string_replace
        deltamush = self.builder.get_scene_items(name_filter="blendShape1")
        self.assertEqual(len(deltamush), 1)

        ## ACT
        self.builder.string_replace("blendShape1", "blendShape2")

        ## VERIFY
        deltamush = self.builder.get_scene_items(name_filter="blendShape1")
        self.assertEqual(deltamush, [])
        deltamush = self.builder.get_scene_items(name_filter="blendShape2")
        self.assertEqual(len(deltamush), 1)

    def test_build_changes_attribute_value(self):
        ## SETUP
        cmds.setAttr('blendShape1.target1', 1)

        ## ACT
        self.builder.build()

        ## VERIFY
        self.assertEqual(cmds.getAttr('blendShape1.target1'), 0)

    def test_missing_mesh(self):
        ## SETUP
        cmds.rename("l_skin_mesh", "l_skin_meshOLD")

        ## VERIFY
        try:
            ## ACT
            self.builder.build()
        except ValueError:  # the Exception you receive before
            assert False, "This is not a warning!"

    def test_blendShape_search_exclude_inheriting(self):
        # searching through every scene item
        # Check if inherited from Base.
        # Check if ALL Base.SEARCH_EXCLUDE items are in item.SEARCH_EXCLUDE
        # This broke previously when the inheritence was overridding instead of extending
        # Any new nodes that do not inherit proprely will break here
        for item in self.builder.get_scene_items(type_filter='blendShape'):
            if isinstance(item, Base):
                # This will assert if any scene item does not contain Base.SEARCH_EXCLUDE items
                self.assertTrue(all(x in item.SEARCH_EXCLUDE for x in Base.SEARCH_EXCLUDE))
            if isinstance(item, DGNode):
                # This will assert if any scene item does not contain DGNode.SEARCH_EXCLUDE items
                self.assertTrue(all(x in item.SEARCH_EXCLUDE for x in DGNode.SEARCH_EXCLUDE))


class BlendshapeAliasAttrTestCase(VfxTestCase):

    def setUp(self):
        super(BlendshapeAliasAttrTestCase, self).setUp()
        obj = cmds.polySphere(ch=False, n="l_skin_mesh")[0]
        obj2 = cmds.polySphere(ch=False, n="l_target1")[0]
        obj3 = cmds.polySphere(ch=False, n="l_target2")[0]
        cmds.select(obj3, obj2, obj)
        cmds.blendShape()

        self.builder = Deformers()
        cmds.select("l_skin_mesh")
        self.builder.retrieve_from_scene()

    def test_string_replace_on_attribute(self):
        ## ACT
        self.builder.string_replace('^l_', 'r_')

        bs = self.builder.get_scene_items(type_filter='blendShape')[0]

        ## VERIFY
        # check if attrs dict has been updated
        # before string replace they would have been 'l_target1' and 'l_target2'
        self.assertIn('r_target1', bs.attrs)
        self.assertIn('r_target2', bs.attrs)

    def test_retrieve_build_on_aliased_attributes(self):
        ## SETUP
        # change alias attributes
        cmds.setAttr("blendShape1.l_target1", 3)
        cmds.setAttr("blendShape1.l_target2", 3)

        ## ACT
        # store values
        cmds.select('l_skin_mesh')
        builder = Deformers()
        builder.retrieve_from_scene()

        # change values and re-build
        cmds.setAttr("blendShape1.l_target1", 10)
        cmds.setAttr("blendShape1.l_target2", 10)
        builder.build()

        ## VERIFY

        self.assertEqual(cmds.getAttr("blendShape1.l_target1"), 3)
        self.assertEqual(cmds.getAttr("blendShape1.l_target2"), 3)
