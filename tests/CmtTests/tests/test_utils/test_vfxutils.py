from maya import cmds
from vfx_test_case import VfxTestCase
from tests.utils import build_anatomical_arm_with_no_popup
from zBuilder.utils.vfxUtils import get_zBones


class VfxUtilsTestCase(VfxTestCase):

    def test_get_zbones_case1(self):
        # Setup
        build_anatomical_arm_with_no_popup()
        # For this test lets add a bone without an attachment.
        # Previously it was not able to pick this case up.
        cmds.select('hand_bone')
        cmds.ziva(b=True)

        # Action
        cmds.select('bone_grp', hi=True)
        bones = get_zBones(cmds.ls(sl=True))

        # Verify
        self.assertEqual(len(bones), 5)

    def test_get_zbones_case2(self):
        # Setup
        build_anatomical_arm_with_no_popup()

        # Action
        cmds.select('r_humerus_bone', 'r_radius_bone', 'hand_bone')
        bones = get_zBones(cmds.ls(sl=True))

        # Verify: we should have 2 as the hand bone is not a zBone in this case
        self.assertEqual(len(bones), 2)
