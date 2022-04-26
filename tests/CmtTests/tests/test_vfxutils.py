import tests.utils as test_utils

from maya import cmds
from vfx_test_case import VfxTestCase
from zBuilder.vfxUtils import get_zBones


class VfxUtilsTestCase(VfxTestCase):

    def test_get_zbones_case1(self):
        test_utils.build_anatomical_arm_with_no_popup()

        # For this test lets add a bone without an attachment.  Previously
        # it was not able to pick this case up.
        cmds.select('hand_bone')
        cmds.ziva(b=True)

        # testing command
        cmds.select('bone_grp', hi=True)
        bones = get_zBones(cmds.ls(sl=True))

        self.assertEqual(len(bones), 5)

    def test_get_zbones_case2(self):
        test_utils.build_anatomical_arm_with_no_popup()

        # testing command
        cmds.select('r_humerus_bone', 'r_radius_bone', 'hand_bone')
        bones = get_zBones(cmds.ls(sl=True))

        # we should have 2 as the hand bone is not a zBone in this case
        self.assertEqual(len(bones), 2)
