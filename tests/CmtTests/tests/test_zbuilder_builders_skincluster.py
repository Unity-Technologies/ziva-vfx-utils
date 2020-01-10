from maya import cmds
import zBuilder.builders.skinClusters as skn

from vfx_test_case import VfxTestCase


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
