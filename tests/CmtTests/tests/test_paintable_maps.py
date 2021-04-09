from maya import cmds
from maya import mel
from utility.paintable_maps import get_paintable_map, set_paintable_map
import vfx_test_case


def make_weights(num_weights, shift):
    """ Make some interesting non-trivial weights to test with. """
    return [x % 10 + shift for x in range(num_weights)]


class SetWeightsTestCase(vfx_test_case.VfxTestCase):
    def test_set_paintable_map_on_ziva_vfx_node(self):
        ## SETUP MAYA #############################################################################

        # Test everything all together in one test, for speed :)
        cmds.polyCube(name='Tissue')  # Make a test scene with zTet node and zAttachment node
        cmds.polyCube(name='Tissue2')  # Many tissues, so we have a long array
        cmds.polyCube(name='Tissue3')  # of weights on the embedder node.
        cmds.polyCube(name='Tissue4')  # Letting us test that we handle those arrays well --
        cmds.polyCube(
            name='Tissue5')  # the code in set_paintable_map_by_MFnWeight... is kinda scary.
        cmds.polyPlane(name='Bone')
        mel.eval('ziva -s')  # makes zSolver1
        cmds.setAttr('zSolver1.enable', False)  # Go faster. We don't need to do sims.
        mel.eval('ziva -t Tissue')  # makes zTet1
        mel.eval('ziva -f Tissue')  # makes zFiber1
        mel.eval('ziva -b Bone')
        mel.eval('ziva -a Tissue Bone')  # makes zAttachment1
        mel.eval('ziva -t Tissue2 Tissue3 Tissue4 Tissue5')

        ## SETUP TEST DATA ########################################################################

        tissue_weights = make_weights(cmds.polyEvaluate('Tissue', vertex=True), 0.125)
        bone_weights = make_weights(cmds.polyEvaluate('Bone', vertex=True), 0.25)

        test_cases = []
        test_cases.append(('zTet1', 'weightList[0].weights', tissue_weights))
        test_cases.append(('zAttachment1', 'weightList[0].weights', tissue_weights))
        test_cases.append(('zAttachment1', 'weightList[1].weights', bone_weights))
        test_cases.append(('zFiber1', 'endPoints', tissue_weights))
        test_cases.append(('zEmbedder1', 'weightList[3].weights', tissue_weights))

        ## ACT & VERIFY ###########################################################################

        self.check_set_paintable_map(test_cases)

    def test_set_paintable_map_bonewarp(self):
        # We need to test zBoneWarp.landmarkList.landmarks because it's an array attribute,
        # but not a deformer weightList. It takes a different code path than deformer weighLists.
        warp_res = 4
        cmds.polyCube(name='BoneWarpSource', sx=warp_res, sy=warp_res, sz=warp_res)
        cmds.polyCube(name='BoneWarpTarget', sx=warp_res, sy=warp_res, sz=warp_res)
        cmds.polyCube(name='BoneWarpThing', sx=warp_res, sy=warp_res, sz=warp_res)
        mel.eval('zBoneWarp BoneWarpSource BoneWarpTarget BoneWarpThing')
        warp_weights = make_weights(cmds.polyEvaluate('BoneWarpThing', vertex=True), 0.5)

        test_cases = [('zBoneWarp1', 'landmarkList[0].landmarks', warp_weights)]
        self.check_set_paintable_map(test_cases)

    def check_set_paintable_map(self, test_cases):
        ## SETUP was done by caller.
        for node, attr, weights in test_cases:
            print('node, attr = {}, {}'.format(node, attr))  # so we can tell what failed
            set_paintable_map(node, attr, weights)
            ## ACT ###############
            observed_weights = get_paintable_map(node, attr)
            ## VERIFY #######################
            self.assertAllApproxEqual(weights, observed_weights)
