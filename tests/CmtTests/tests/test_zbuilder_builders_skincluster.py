import os
import zBuilder.builders.skinClusters as skn
from maya import cmds
from maya import mel

from vfx_test_case import VfxTestCase, attr_values_from_scene


class ZivaSkinClusterGenericTestCase(VfxTestCase):
    @classmethod
    def setUpClass(cls):
        cls.skincluster_names = ["skinCluster1"]
        cls.skincluster_attrs = ["skinningMethod", "useComponents", "normalizeWeights"]

    def setUp(self):
        super(ZivaSkinClusterGenericTestCase, self).setUp()
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
        self.builder = skn.SkinCluster()
        cmds.select("l_skin_mesh")
        self.builder.retrieve_from_scene()

    def tearDown(self):
        if os.path.exists(self.temp_file_path):
            os.remove(self.temp_file_path)
        super(ZivaSkinClusterGenericTestCase, self).tearDown()

    def check_retrieve_skincluster_looks_good(self, builder):
        """Args:
            builder (builders.skinClusters.SkinCluster()): builder object
        """
        self.check_retrieve_looks_good(builder, {}, self.skincluster_names, "skinCluster")

    def test_retrieve(self):
        self.check_retrieve_skincluster_looks_good(self.builder)

    def test_build_restores_attr_values(self):
        plug_names = {
            '{}.{}'.format(geo, attr)
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
        self.builder.write(self.temp_file_path)

        ## VERIFY
        self.assertTrue(os.path.exists(self.temp_file_path))

        ## ACT
        builder = skn.SkinCluster()
        builder.retrieve_from_file(self.temp_file_path)

        ## VERIFY
        self.check_retrieve_skincluster_looks_good(builder)

    def test_build(self):
        ## SETUP
        cmds.select(cmds.ls(type="skinCluster"))
        mel.eval("doDelete;")

        ## ACT
        self.builder.build()
        builder = skn.SkinCluster()
        cmds.select("l_skin_mesh")
        builder.retrieve_from_scene()

        ## VERIFY
        self.check_retrieve_skincluster_looks_good(builder)

    def test_build_from_file(self):
        ## SETUP
        self.builder.write(self.temp_file_path)
        self.assertTrue(os.path.exists(self.temp_file_path))
        cmds.select(cmds.ls(type="skinCluster"))
        mel.eval("doDelete;")

        ## ACT
        builder = skn.SkinCluster()
        builder.retrieve_from_file(self.temp_file_path)
        builder.build()

        builder = skn.SkinCluster()
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


class ZivaSkinClusterTestCase(VfxTestCase):
    def setUp(self):
        super(ZivaSkinClusterTestCase, self).setUp()

        # Building a simple skinCluster scene to test.
        cmds.select(cl=True)
        cmds.joint(name='jnt')
        cmds.polySphere(name='sph')

        cmds.skinCluster('jnt', 'sph')

        cmds.select(cl=True)
        cmds.joint(name='warped_jnt')
        cmds.polySphere(name='warped_sph')

        # clear selection.
        cmds.select(cl=True)

    def test_string_replace_add_prefix(self):
        # select the sphere with skinCluster
        cmds.select('sph')

        # transfer it by prefix (as trasnfer menu does)

        builder = skn.SkinCluster()
        builder.retrieve_from_scene()
        builder.string_replace('^', 'warped_')

        cls = builder.get_scene_items()[0]
        attribute = cls.weights.keys()[0]

        self.assertTrue('warped_' not in attribute)

    def test_retrieve_and_build_clean(self):
        # select the sphere with skinCluster
        cmds.select('sph')

        builder = skn.SkinCluster()
        builder.retrieve_from_scene()

        cmds.delete('skinCluster1')

        builder.build()

        self.assertSceneHasNodes(['skinCluster1'])

    def test_retrieve_and_build_changed(self):
        # select the sphere with skinCluster
        cmds.select('sph')

        builder = skn.SkinCluster()
        builder.retrieve_from_scene()

        # change a value
        cmds.setAttr('skinCluster1.useComponents', 1)

        builder.build()

        # if built properly value should be False
        self.assertFalse(cmds.getAttr('skinCluster1.useComponents'))
