import maya.cmds as mc
import zBuilder.builders.skinClusters as skn

from vfx_test_case import VfxTestCase


class ZivaSkinClusterTestCase(VfxTestCase):
    @classmethod
    def setUpClass(cls):
        pass

    def setUp(self):
        super(ZivaSkinClusterTestCase, self).setUp()

        # This builds the Zivas anatomical arm demo with no pop up dialog.
        mc.select(cl=True)
        mc.joint(name='jnt')
        mc.polySphere(name='sph')

        mc.skinCluster('jnt', 'sph')

        mc.select(cl=True)
        mc.joint(name='warped_jnt')
        mc.polySphere(name='warped_sph')

        # clear selection.  It should retrieve whole scene
        mc.select(cl=True)

    def test_string_replace_add_prefix(self):
        # select the sphere with skinCluster
        mc.select('sph')

        # transfer it by prefix (as trasnfer menu does)

        z = skn.SkinCluster()
        z.retrieve_from_scene()
        z.string_replace('^', 'warped_')

        cls = z.get_scene_items()[0]
        attribute = cls.weights.keys()[0]

        self.assertTrue('warped_' not in attribute)
