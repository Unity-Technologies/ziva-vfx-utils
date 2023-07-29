from maya import cmds
from vfx_test_case import VfxTestCase
from tests.utils import load_scene
from zBuilder.utils.mayaUtils import build_attr_list
import zBuilder.commands as com


class MirrorCommand(VfxTestCase):

    def setUp(self):
        super(MirrorCommand, self).setUp()
        load_scene('mirror_command.ma')
        self.interpolated_map = (
            0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
            0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
            0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
            0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
            0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
            0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
            0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
            0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
            0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
            0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
            0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
            0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
            0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
            0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
            0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
            0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
            0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
            0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
            0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
            0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
            0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
            0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
            0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
            0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
            0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
            1.0, 1.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 1.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0,
            1.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 1.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 1.0,
            1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 1.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 1.0, 1.0,
            0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 1.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 1.0, 1.0, 0.0,
            0.0, 0.0, 0.0, 1.1920928955078125e-07, 1.0, 1.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 1.0,
            1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 1.0, 1.0, 0.0, 0.0, 0.0, 0.0, 1.628234258532757e-08,
            1.0, 1.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 1.0, 1.0, 0.0, 0.0, 0.0, 0.0,
            2.87645889329724e-08, 1.0, 1.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 1.0, 1.0, 0.0, 0.0,
            0.0, 0.0, 0.0, 1.0, 1.0, 1.0, 0.0, 0.0, 0.0, 0.0, 3.5762786865234375e-07, 1.0, 1.0, 1.0,
            0.0, 0.0, 0.0, 0.0, 1.7881393432617188e-06, 1.0, 1.0, 1.0, 0.0, 0.0, 0.0, 0.0,
            2.384185791015625e-07, 1.0, 1.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
            4.76837158203125e-07, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 3.7071640690555796e-07, 0.0, 0.0,
            0.0, 0.0, 0.0, 0.0, 1.632042767596431e-07, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
            1.8112041288986802e-07, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 3.625791578087956e-08, 0.0, 0.0,
            0.0, 0.0, 0.0, 0.0, 1.4901161193847656e-06, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
            1.2516975402832031e-06, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.1324882507324219e-06, 0.0, 0.0,
            0.0, 0.0, 0.0, 0.0, 5.960464477539062e-07, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
            4.76837158203125e-07, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 2.980232238769531e-07, 0.0, 0.0,
            0.0, 0.0, 0.0, 0.0, 1.7881393432617188e-07, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
            2.980232238769531e-07, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 2.384185791015625e-07, 0.0, 0.0,
            0.0, 0.0, 0.0, 0.0, 2.980232238769531e-07, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
            4.172325134277344e-07, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 2.980232238769531e-07, 0.0, 0.0,
            0.0, 0.0, 0.0, 0.0, 3.5762786865234375e-07, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
            5.364418029785156e-07, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 4.76837158203125e-07)
        self.non_interpolated_map = (0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
                                     0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
                                     0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
                                     0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
                                     0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
                                     0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
                                     0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
                                     0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
                                     0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
                                     0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
                                     0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
                                     1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
                                     0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0,
                                     0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
                                     0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
                                     0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
                                     1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
                                     0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0,
                                     0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
                                     0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
                                     0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
                                     1.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
                                     0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0,
                                     0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
                                     0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
                                     0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
                                     0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
                                     0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
                                     0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
                                     0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
                                     0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
                                     0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
                                     0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
                                     0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
                                     0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
                                     0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
                                     0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
                                     0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
                                     0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
                                     0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
                                     0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
                                     0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
                                     0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
                                     0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
                                     0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
                                     0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
                                     0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
                                     0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
                                     0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
                                     0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
                                     0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
                                     0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
                                     0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
                                     0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
                                     0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
                                     0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
                                     0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
                                     0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
                                     0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0,
                                     0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0)

    def check_node_symmetrical(self, nodeA, nodeB):
        # check they exist
        self.assertTrue(cmds.objExists(nodeA))
        self.assertTrue(cmds.objExists(nodeB))

        # get attributes to compare
        attrs_to_compare = build_attr_list(nodeA)
        # collisions sets will be different so need to remove from this list
        if 'collisionSets' in attrs_to_compare:
            attrs_to_compare.remove('collisionSets')

        # compare attributes
        for attr in attrs_to_compare:
            self.assertEqual(cmds.getAttr(nodeA + '.' + attr), cmds.getAttr(nodeB + '.' + attr))

    def test_mirror_whole_solver_basic(self):
        ## SETUP
        cmds.select('zSolver1')
        # change some attributes from default so we see if change propagated
        # to new muscle
        cmds.setAttr("l_arm_zMaterial.youngsModulusExp", 3)
        cmds.setAttr("l_arm_zMaterial.pressure", 200)
        cmds.setAttr("zBone3.collisions", 0)
        cmds.setAttr("zBone3.collisionVolume", 0)
        cmds.setAttr("zFiber2.strengthExp", 2)
        cmds.setAttr("zFiber2.excitation", 1)
        cmds.setAttr("l_zRestShape.surfacePenaltyExp", 1)

        ## ACT
        com.mirror(source_prefix='^l_', target_prefix='r_', center_prefix='c_')

        ## VERIFY
        # materials
        self.check_node_symmetrical('r_hard_zMaterial', 'l_hard_zMaterial')
        self.check_node_symmetrical('r_soft_zMaterial', 'l_soft_zMaterial')
        self.check_node_symmetrical('r_arm_zMaterial', 'l_arm_zMaterial')
        # attachments
        self.check_node_symmetrical('r_zAChestTsToChestBn_end', 'l_zAChestTsToChestBn_end')
        self.check_node_symmetrical('r_zAChestTsToArmTs', 'l_zAChestTsToArmTs')
        self.check_node_symmetrical('r_zAChestTsToChestBn_mid', 'l_zAChestTsToChestBn_mid')
        self.check_node_symmetrical('r_zAArmTsToArmBn', 'l_zAArmTsToArmBn')
        self.check_node_symmetrical('r_zAPelvisTsToLegBn', 'l_zAPelvisTsToLegBn')
        # fibers
        self.check_node_symmetrical('r_arm_zFiber', 'l_arm_zFiber')
        self.check_node_symmetrical('zFiber2', 'zFiber3')
        self.check_node_symmetrical('r_chestB_zFiber', 'l_chestB_zFiber')
        self.check_node_symmetrical('r_chestA_zFiber', 'l_chestA_zFiber')
        # tissue
        self.check_node_symmetrical('r_arm_zTissue', 'l_arm_zTissue')
        self.assertTrue(cmds.zQuery('r_tissue', st=True), 'r_subtissue')
        # tet
        self.check_node_symmetrical('r_arm_zTet', 'l_arm_zTet')
        # zbone
        self.check_node_symmetrical('zBone3', 'zBone7')
        # zCloth
        self.check_node_symmetrical('zCloth1', 'zCloth2')
        # zRestShape
        self.check_node_symmetrical('l_zRestShape', 'r_zRestShape')
        # zRivet
        self.check_node_symmetrical('l_rivet_loc1', 'r_rivet_loc1')
        self.check_node_symmetrical('l_zRivetToBone1', 'r_zRivetToBone1')
        self.check_node_symmetrical('l_zLineOfAction1', 'r_zLineOfAction1')

    def test_mirror_selection_basic(self):
        ## SETUP
        cmds.select('c_chest_ts')
        # change some attributes from default so we see if change propagated
        # to new muscle
        cmds.setAttr("l_hard_zMaterial.youngsModulusExp", 3)
        cmds.setAttr("l_hard_zMaterial.pressure", 200)
        cmds.setAttr("l_chestB_zFiber.strengthExp", 2)
        cmds.setAttr("l_chestB_zFiber.excitation", 1)

        ## ACT
        com.mirror(source_prefix='^l_', target_prefix='r_', center_prefix='c_')

        ## VERIFY
        self.check_node_symmetrical('r_zAChestTsToChestBn_end', 'l_zAChestTsToChestBn_end')
        self.check_node_symmetrical('r_zAChestTsToChestBn_mid', 'l_zAChestTsToChestBn_mid')
        self.check_node_symmetrical('r_chestB_zFiber', 'l_chestB_zFiber')
        self.check_node_symmetrical('r_chestA_zFiber', 'l_chestA_zFiber')
        self.check_node_symmetrical('r_hard_zMaterial', 'l_hard_zMaterial')
        self.check_node_symmetrical('r_soft_zMaterial', 'l_soft_zMaterial')

        # make sure center mesh attachment interpolates properly
        self.assertAllApproxEqual(
            cmds.getAttr('r_zAChestTsToChestBn_mid.weightList[0].weights')[0],
            self.interpolated_map)

        # make sure non sided attachment did not interpolate
        self.assertAllApproxEqual(
            cmds.getAttr('zAttachment1.weightList[0].weights')[0], self.non_interpolated_map)

    def test_material_creation_bug(self):
        """
        VFXACT-1796 is a fix for a bug dealing with material creation.  If you are in mirror workflow and you have
        multiple materials on a non-center mesh it would cuase issues and create the wrong material node.  This test
        confirms the fix.
        """
        ## SETUP
        cmds.select('l_arm_ts')

        ## ACT
        com.mirror(source_prefix='^l_', target_prefix='r_', center_prefix='c_')

        ## VERIFY
        self.check_node_symmetrical('r_arm_zMaterial', 'l_arm_zMaterial')
        self.check_node_symmetrical('r_arm_zMaterial_soft', 'l_arm_zMaterial_soft')

    def test_attachment_interpolate_bug(self):
        """
        VFXACT-1796 is a bug that incorrectly identifies if an attachment needs to be interpolated (duplicated and
        flipped).  This covers that case
        """
        ## SETUP
        cmds.select('zSolver1')

        ## ACT
        com.mirror(source_prefix='^l_', target_prefix='r_', center_prefix='c_')

        ## VERIFY
        self.check_node_symmetrical('c_sourceMesh__r_targetMesh_zAttachment1', 'c_sourceMesh__l_targetMesh_zAttachment1')

    def test_material_creation_bug(self):
        """
        VFXACT-1796 is a fix for a bug dealing with material creation.  If you are in mirror workflow and you have
        multiple materials on a non-center mesh it would cuase issues and create the wrong material node.  This test
        confirms the fix.
        """
        ## SETUP
        cmds.select('l_arm_ts')

        ## ACT
        com.mirror(source_prefix='^l_', target_prefix='r_', center_prefix='c_')

        ## VERIFY
        self.check_node_symmetrical('r_arm_zMaterial', 'l_arm_zMaterial')
        self.check_node_symmetrical('r_arm_zMaterial_soft', 'l_arm_zMaterial_soft')