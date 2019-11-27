import maya.cmds as mc
import zBuilder.builders.skinClusters as skn

from vfx_test_case import VfxTestCase


class ZivaSkinClusterTestCase(VfxTestCase):
    def setUp(self):
        super(ZivaSkinClusterTestCase, self).setUp()

        # Building a simple skinCluster scene to test.
        mc.select(cl=True)
        mc.joint(name='jnt')
        mc.polySphere(name='sph')

        mc.skinCluster('jnt', 'sph')

        mc.select(cl=True)
        mc.joint(name='warped_jnt')
        mc.polySphere(name='warped_sph')

        # clear selection.
        mc.select(cl=True)

    def test_string_replace_add_prefix(self):
        # select the sphere with skinCluster
        mc.select('sph')

        # transfer it by prefix (as trasnfer menu does)

        builder = skn.SkinCluster()
        builder.retrieve_from_scene()
        builder.string_replace('^', 'warped_')

        cls = builder.get_scene_items()[0]
        attribute = cls.weights.keys()[0]

        self.assertTrue('warped_' not in attribute)

    def test_retrieve_and_build_clean(self):
        # select the sphere with skinCluster
        mc.select('sph')

        builder = skn.SkinCluster()
        builder.retrieve_from_scene()

        mc.delete('skinCluster1')

        builder.build()

        self.assertSceneHasNodes(['skinCluster1'])

    def test_retrieve_and_build_changed(self):
        # select the sphere with skinCluster
        mc.select('sph')

        builder = skn.SkinCluster()
        builder.retrieve_from_scene()

        # change a value
        mc.setAttr('skinCluster1.useComponents', 1)

        builder.build()

        # if built properly value should be False
        self.assertFalse(mc.getAttr('skinCluster1.useComponents'))
