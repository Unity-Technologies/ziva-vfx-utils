import maya.cmds as mc
import maya.mel as mm
from utility.set_weights import set_weights
import vfx_test_case


def make_weights(num_weights, shift):
    """ Make some interesting non-trivial weights to test with. """
    return [x % 10 + shift for x in xrange(num_weights)]


def get_weights(map_name, vert_count):
    try:
        value = mc.getAttr('{}[0:{}]'.format(map_name, vert_count - 1))
    except ValueError:
        value = mc.getAttr(map_name)
    return value


class SetWeightsTestCase(vfx_test_case.VfxTestCase):
    def test_set_weights_on_ziva_vfx_node(self):
        ## SETUP MAYA #############################################################################

        # Test everything all together in one test, for speed :)
        mc.polyCube(name='Tissue')  # Make a test scene with zTet node and zAttachment node
        mc.polyCube(name='Tissue2')  # Many tissues, so we have a long array
        mc.polyCube(name='Tissue3')  # of weights on the embedder node.
        mc.polyCube(name='Tissue4')  # Letting us test that we handle those arrays well --
        mc.polyCube(name='Tissue5')  # the code in set_weights_by_MFnWeight... is kinda scary.
        mc.polyPlane(name='Bone')
        mm.eval('ziva -s')  # makes zSolver1
        mc.setAttr('zSolver1.enable', False)  # Go faster. We don't need to do sims.
        mm.eval('ziva -t Tissue')  # makes zTet1
        mm.eval('ziva -f Tissue')  # makes zFiber1
        mm.eval('ziva -b Bone')
        mm.eval('ziva -a Tissue Bone')  # makes zAttachment1
        mm.eval('ziva -t Tissue2 Tissue3 Tissue4 Tissue5')

        ## SETUP TEST DATA ########################################################################

        tissue_weights = make_weights(mc.polyEvaluate('Tissue', vertex=True), 0.125)
        bone_weights = make_weights(mc.polyEvaluate('Bone', vertex=True), 0.25)

        test_cases = []
        test_cases.append(('zTet1', 'weightList[0].weights', tissue_weights))
        test_cases.append(('zAttachment1', 'weightList[0].weights', tissue_weights))
        test_cases.append(('zAttachment1', 'weightList[1].weights', bone_weights))
        test_cases.append(('zFiber1', 'endPoints', tissue_weights))
        test_cases.append(('zEmbedder1', 'weightList[3].weights', tissue_weights))

        ## ACT & VERIFY ###########################################################################

        self.check_set_weights(test_cases)

    def test_set_weights_bonewarp(self):
        # We need to test zBoneWarp.landmarkList.landmarks because it's an array attribute,
        # but not a deformer weightList. It takes a different code path than deformer weighLists.
        warp_res = 4
        mc.polyCube(name='BoneWarpSource', sx=warp_res, sy=warp_res, sz=warp_res)
        mc.polyCube(name='BoneWarpTarget', sx=warp_res, sy=warp_res, sz=warp_res)
        mc.polyCube(name='BoneWarpThing', sx=warp_res, sy=warp_res, sz=warp_res)
        mm.eval('zBoneWarp BoneWarpSource BoneWarpTarget BoneWarpThing')
        warp_weights = make_weights(mc.polyEvaluate('BoneWarpThing', vertex=True), 0.5)

        test_cases = [('zBoneWarp1', 'landmarkList[0].landmarks', warp_weights)]
        self.check_set_weights(test_cases)

    def check_set_weights(self, test_cases):
        ## SETUP was done by caller.
        for node, attr, weights in test_cases:
            print('node, attr = {}, {}'.format(node, attr))  # so we can tell what failed
            set_weights(node, attr, weights)  ## ACT ##############################################
            observed_weights = get_weights(node + '.' + attr, len(weights))
            self.assertAllApproxEqual(weights, observed_weights)  ## VERIFY #######################
