from maya import cmds
from vfx_test_case import VfxTestCase
from zBuilder.utils.paintable_maps import get_paintable_map, set_paintable_map


def make_weights(num_weights, shift):
    """ Make some interesting non-trivial weights to test with. """
    return [x % 10 + shift for x in range(num_weights)]


class SetWeightsTestCase(VfxTestCase):

    def test_set_paintable_map_on_ziva_vfx_node(self):
        ## SETUP MAYA #############################################################################

        # Test everything all together in one test, for speed :)
        cmds.polyCube(name='Tissue')  # Make a test scene with zTet node and zAttachment node
        cmds.polyCube(name='Tissue2')  # Many tissues, so we have a long array
        cmds.polyCube(name='Tissue3')  # of weights on the embedder node.
        cmds.polyCube(name='Tissue4')  # Letting us test that we handle those arrays well
        # the code in set_paintable_map_by_MFnWeight... is kinda scary.
        cmds.polyCube(name='Tissue5')
        cmds.polyPlane(name='Bone')
        cmds.ziva(s=True)  # makes zSolver1
        cmds.setAttr('zSolver1.enable', False)  # Go faster. We don't need to do sims.
        cmds.ziva('Tissue', t=True)  # makes zTet1
        cmds.ziva('Tissue', f=True)  # makes zFiber1
        cmds.ziva('Bone', b=True)
        cmds.ziva('Tissue', 'Bone', a=True)  # makes zAttachment1
        cmds.ziva('Tissue2', 'Tissue3', 'Tissue4', 'Tissue5', t=True)

        ## SETUP TEST DATA ########################################################################

        tissue_weights = make_weights(cmds.polyEvaluate('Tissue', vertex=True), 0.125)
        tissue_test_cases = []
        tissue_test_cases.append(('zTet1', 'weightList[0].weights', tissue_weights))
        tissue_test_cases.append(('zAttachment1', 'weightList[0].weights', tissue_weights))
        tissue_test_cases.append(('zFiber1', 'endPoints', tissue_weights))
        tissue_test_cases.append(('zEmbedder1', 'weightList[3].weights', tissue_weights))

        bone_weights = make_weights(cmds.polyEvaluate('Bone', vertex=True), 0.25)
        bone_test_cases = []
        bone_test_cases.append(('zAttachment1', 'weightList[1].weights', bone_weights))

        ## ACT & VERIFY ###########################################################################

        self.check_set_paintable_map(tissue_test_cases, 'Tissue')
        self.check_set_paintable_map(bone_test_cases, 'Bone')

    def test_set_paintable_map_bonewarp(self):
        # We need to test zBoneWarp.landmarkList.landmarks because it's an array attribute,
        # but not a deformer weightList. It takes a different code path than deformer weighLists.
        warp_res = 4
        cmds.polyCube(name='BoneWarpSource', sx=warp_res, sy=warp_res, sz=warp_res)
        cmds.polyCube(name='BoneWarpTarget', sx=warp_res, sy=warp_res, sz=warp_res)
        cmds.polyCube(name='BoneWarpThing', sx=warp_res, sy=warp_res, sz=warp_res)
        cmds.zBoneWarp('BoneWarpSource', 'BoneWarpTarget', 'BoneWarpThing')
        warp_weights = make_weights(cmds.polyEvaluate('BoneWarpThing', vertex=True), 0.5)

        test_cases = [('zBoneWarp1', 'landmarkList[0].landmarks', warp_weights)]
        self.check_set_paintable_map(test_cases, None)

    def check_set_paintable_map(self, test_cases, mesh_name):
        # SETUP was done by caller.
        # TODO: Delete mesh_name parameter once Maya 2022 retires or fixes the regression
        for node, attr, weights in test_cases:
            print('node, attr = {}, {}'.format(node, attr))  # so we can tell what failed

            ## ACT ###############
            set_paintable_map(node, attr, weights)
            observed_weights = get_paintable_map(node, attr, mesh_name)

            ## VERIFY #######################
            self.assertAllApproxEqual(weights, observed_weights)
