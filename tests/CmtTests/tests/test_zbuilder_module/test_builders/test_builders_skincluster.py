import os

from maya import cmds
from maya import mel
from vfx_test_case import VfxTestCase, attr_values_from_scene
from zBuilder.builders.skinClusters import SkinCluster
from zBuilder.nodes.base import Base
from zBuilder.nodes.dg_node import DGNode
from zBuilder.builders.serialize import read, write
from zBuilder.nodes.base import Base
from zBuilder.nodes.dg_node import DGNode


class SkinClusterBuilderTestCase(VfxTestCase):

    @classmethod
    def setUpClass(cls):
        cls.skincluster_names = ["skinCluster1"]
        cls.skincluster_attrs = ["skinningMethod", "useComponents", "normalizeWeights"]

    def setUp(self):
        super(SkinClusterBuilderTestCase, self).setUp()
        # Setup simple scene with 2 spheres and 2 joints
        obj = cmds.polySphere(ch=False, n="l_skin_mesh")[0]
        cmds.select(cl=True)
        jt = cmds.joint(n="l_skin_mesh_joint")
        cmds.move(-2, [obj, jt], x=True)
        cmds.select([obj, jt])
        cmds.SmoothBindSkin()
        obj = cmds.polySphere(ch=False, n="r_skin_mesh")[0]
        cmds.select(cl=True)
        jt = cmds.joint(n="r_skin_mesh_joint")
        cmds.move(2, [obj, jt], x=True)
        self.builder = SkinCluster()
        cmds.select("l_skin_mesh")
        self.builder.retrieve_from_scene()

    def tearDown(self):
        if os.path.exists(self.temp_file_path):
            os.remove(self.temp_file_path)
        super(SkinClusterBuilderTestCase, self).tearDown()

    def check_retrieve_skincluster_looks_good(self, builder):
        """Args:
            builder (builders.skinClusters.SkinCluster()): builder object
        """
        self.check_retrieve_looks_good(builder, {}, self.skincluster_names, "skinCluster")

    def test_retrieve(self):
        self.check_retrieve_skincluster_looks_good(self.builder)

    def test_build_restores_attr_values(self):
        plug_names = {
            "{}.{}".format(geo, attr)
            for geo in self.skincluster_names for attr in self.skincluster_attrs
        }
        attrs_before = attr_values_from_scene(plug_names)

        # remove all skinCluster nodes from the scene and build them
        cmds.select(cmds.ls(type="skinCluster"))
        mel.eval("doDelete;")
        self.builder.build()

        attrs_after = attr_values_from_scene(plug_names)
        self.assertEqual(attrs_before, attrs_after)

    def test_builder_has_same_skincluster_nodes_after_writing_to_disk(self):
        ## ACT
        write(self.temp_file_path, self.builder)

        ## VERIFY
        self.assertTrue(os.path.exists(self.temp_file_path))

        ## ACT
        builder = SkinCluster()
        read(self.temp_file_path, builder)

        ## VERIFY
        self.check_retrieve_skincluster_looks_good(builder)

    def test_build(self):
        ## SETUP
        cmds.select(cmds.ls(type="skinCluster"))
        mel.eval("doDelete;")

        ## ACT
        self.builder.build()
        builder = SkinCluster()
        cmds.select("l_skin_mesh")
        builder.retrieve_from_scene()

        ## VERIFY
        self.check_retrieve_skincluster_looks_good(builder)

    def test_build_from_file(self):
        ## SETUP
        write(self.temp_file_path, self.builder)
        self.assertTrue(os.path.exists(self.temp_file_path))
        cmds.select(cmds.ls(type="skinCluster"))
        mel.eval("doDelete;")

        ## ACT
        builder = SkinCluster()
        read(self.temp_file_path, builder)
        builder.build()

        builder = SkinCluster()
        cmds.select("l_skin_mesh")
        builder.retrieve_from_scene()
        self.check_retrieve_skincluster_looks_good(builder)

    def test_string_replace(self):
        ## VERIFY
        # check if an item exists before string_replace
        skin_cluster = self.builder.get_scene_items(name_filter="skinCluster1")
        self.assertGreaterEqual(len(skin_cluster), 1)

        ## ACT
        self.builder.string_replace("skinCluster1", "skinCluster2")

        ## VERIFY
        skin_cluster = self.builder.get_scene_items(name_filter="skinCluster1")
        self.assertEqual(skin_cluster, [])
        skin_cluster = self.builder.get_scene_items(name_filter="skinCluster2")
        self.assertEqual(len(skin_cluster), 1)

    def test_build_changes_attribute_value(self):
        ## SETUP
        cmds.setAttr('skinCluster1.useComponents', 1)

        ## ACT
        self.builder.build()

        ## VERIFY
        # if built properly value should be False
        self.assertEqual(cmds.getAttr('skinCluster1.useComponents'), 0)

    def test_skinCluster_search_exclude_inheriting(self):
        # searching through every scene item
        # Check if inherited from Base.
        # Check if ALL Base.SEARCH_EXCLUDE items are in item.SEARCH_EXCLUDE
        # This broke previously when the inheritence was overridding instead of extending
        # Any new nodes that do not inherit proprely will break here
        for item in self.builder.get_scene_items(type_filter='skinCluster'):
            if isinstance(item, Base):
                # This will assert if any scene item does not contain Base.SEARCH_EXCLUDE items
                self.assertTrue(all(x in item.SEARCH_EXCLUDE for x in Base.SEARCH_EXCLUDE))
            if isinstance(item, DGNode):
                # This will assert if any scene item does not contain DGNode.SEARCH_EXCLUDE items
                self.assertTrue(all(x in item.SEARCH_EXCLUDE for x in DGNode.SEARCH_EXCLUDE))

    def test_skinCluster_copySkinWeights(self):

        ## SETUP
        cmds.delete('l_skin_mesh', constructionHistory=True)
        cmds.polySmooth('l_skin_mesh')

        ## ACT
        self.builder.build()

        ## VERIFY
        # I picked a vert outside of the original (the sphere originally had 382 verts so 392 will be at 0,0,0)
        val = cmds.xform('l_skin_mesh.vtx[392]', query=True, translation=True, worldSpace=True)

        # we are going to test to make sure copySkinWeights is doing what it needs to during a build.
        # Mainly it should effectively interpolate the weights if the topology changes.
        # If you apply a wrong size map to a skinCluster maya throws every extra vert at 0,0,0
        # we can use this to determine if it worked or not.
        # x is at -2 due to the transformation applied to sphere transform
        fail_value = [-2.0, 0.0, 0.0]
        self.assertNotEqual(val, fail_value)

    def test_missing_mesh(self):
        ## SETUP
        cmds.rename("l_skin_mesh", "l_skin_meshOLD")

        ## VERIFY
        try:
            ## ACT
            self.builder.build()
        except ValueError:  # the Exception you receive before
            assert False, "This is not a warning!"