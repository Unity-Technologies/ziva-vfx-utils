import copy
import os
import zBuilder.builders.ziva as zva

from maya import cmds
from vfx_test_case import VfxTestCase, ZivaUpdateTestCase
from tests.utils import build_anatomical_arm_with_no_popup, get_tmp_file_location, build_mirror_sample_geo, load_scene
from zBuilder.utils.mayaUtils import get_short_name
from zBuilder.commands import (ZIVA_CLIPBOARD_ZBUILDER, clean_scene, copy_paste_with_substitution,
                               rename_ziva_nodes, rig_cut, rig_copy, rig_paste, load_rig, save_rig)


class CopyPasteWithArmAssetTestCase(VfxTestCase):

    def setUp(self):
        super(CopyPasteWithArmAssetTestCase, self).setUp()
        build_anatomical_arm_with_no_popup()

    def test_copy_paste(self):

        def copy_paste(*args, **kwargs):
            '''
            A utility wrapper for copying and pasting a tissue
            '''
            sel = cmds.ls(sl=True)
            selection = None
            if args:
                selection = cmds.ls(args[0], l=True)
            else:
                selection = cmds.ls(sl=True, l=True)

            builder = zva.Ziva()
            builder.retrieve_from_scene_selection(selection[0])
            builder.string_replace(get_short_name(selection[0]), get_short_name(selection[1]))
            builder.stats()
            builder.build(**kwargs)
            cmds.select(sel)

        # Setup
        cmds.select(cl=True)
        cmds.duplicate('r_bicep_muscle', name='dupe')
        cmds.polySmooth('dupe')
        cmds.select('r_bicep_muscle', 'dupe')

        # Action
        copy_paste()

        # Verify
        self.assertSceneHasNodes(['dupe_r_radius_bone'])

    def test_rig_copy_paste_clean(self):
        # testing menu command to copy and paste on ziva that has been cleaned
        cmds.select('zSolver1')
        rig_copy()

        clean_scene()

        rig_paste()
        self.assertSceneHasNodes(['zSolver1'])

    def test_rig_cut(self):
        # testing the cut feature, removing ziva setup after copy
        cmds.select('zSolver1')
        rig_cut()

        # there should be no attachments in scene
        self.assertTrue(len(cmds.ls(type='zAttachment')) is 0)

    def test_rig_copy_without_selection_should_raise(self):
        cmds.select(cl=True)
        with self.assertRaises(Exception):
            rig_copy()

    def test_save_rig(self):
        # Setup
        file_name = get_tmp_file_location('.zBuilder')
        cmds.select('zSolver1')

        # Action
        save_rig(file_name)

        # Verify
        # simply check if file exists
        self.assertTrue(os.path.exists(file_name))
        self.assertGreater(os.path.getsize(file_name), 1000)

        os.remove(file_name)

    def test_load_rig(self):
        # Setup
        file_name = get_tmp_file_location('.zBuilder')
        cmds.select('zSolver1')
        save_rig(file_name)
        # clean scene so we just have geo
        clean_scene()

        # Action
        load_rig(file_name)

        # Verify
        self.assertSceneHasNodes(['zSolver1'])

        os.remove(file_name)


class CopyPasteWithMirrorAssetTestCase(VfxTestCase):

    def test_copy_paste_with_substitution(self):
        build_mirror_sample_geo()
        rename_ziva_nodes()

        cmds.select('r_muscle')
        copy_paste_with_substitution('^r', 'l')

        self.assertSceneHasNodes(['l_zMaterial1', 'l_zTissue'])


def _return_copy_buffer():
    """ Helper function that returns a deep copy of the buffer contents simply for comparisons.
    """
    deep = copy.deepcopy(ZIVA_CLIPBOARD_ZBUILDER)
    return deep


class CopyPasteWithMirrorAsset2TestCase(ZivaUpdateTestCase):
    """This Class tests a specific type of "mirroring" so there are some assumptions made

    - geometry has an identifiable qualifier, in this case it is l_ and r_
    - Both sides geometry are in the scene
    - Both sides have Ziva nodes

    """

    def setUp(self):
        super(CopyPasteWithMirrorAsset2TestCase, self).setUp()
        load_scene('copy_paste_bug2.ma')

        self.builder = zva.Ziva()
        self.builder.retrieve_from_scene()

        cmds.select('pSphere2')
        rig_cut()

        self.stored_buffer = _return_copy_buffer()

        cmds.select('pSphere1')
        rig_paste()

    def test_menu_paste(self):

        att_map = self.builder.get_scene_items(type_filter='map',
                                               name_filter='zAttachment1.weightList[0].weights')[0]

        self.builder_new = zva.Ziva()
        self.builder_new.retrieve_from_scene()

        new_att_map = self.builder_new.get_scene_items(
            type_filter='map', name_filter='zAttachment1.weightList[0].weights')[0]

        # the New map has been interpolated on a larger mesh so size of map should
        # be different
        self.assertNotEqual(len(att_map.values), len(new_att_map.values))

        # it has been interpolated and source map just has 1's and 0's.  Being
        # interpolated lets check for values that are not 1 or 0
        non_binary_values = [x for x in new_att_map.values if x != 0.0 and x != 1.0]
        self.assertTrue(non_binary_values)

        # test post paste
        # stiffness on attachment should equal 20
        self.assertEquals(cmds.getAttr("zAttachment1.stiffness"), 20)

        # the map is on a new node now lets check what happens when we change a value
        # on pasted item the paste again.
        cmds.setAttr("zAttachment1.stiffness", 10)

        cmds.select('pSphere3')

        rig_paste()
        # New attachment gets named zAttachment2, this stiffness should equal 20
        self.assertEquals(cmds.getAttr("zAttachment2.stiffness"), 20)
        # make sure att1 is still 20 as well.
        self.assertEquals(cmds.getAttr("zAttachment1.stiffness"), 10)

    def test_copy_buffer(self):
        # it has been pasted in setup.  Now the buffer should remain unchanged
        # get buffer again and compare

        build = zva.Ziva()
        build.retrieve_from_scene()

        # this gets interpolate so scene builder should be different then buffer
        self.assertNotEquals(self.stored_buffer, build)

        current_buffer = _return_copy_buffer()

        # these should be same
        self.assertEquals(self.stored_buffer, current_buffer)


class CopyBufferTestCase(ZivaUpdateTestCase):
    """
    This Class tests a specific type of "mirroring" so there are some assumptions made
    """

    def setUp(self):
        super(CopyBufferTestCase, self).setUp()
        load_scene('copy_paste_bug2.ma')

        self.builder = zva.Ziva()
        self.builder.retrieve_from_scene()

        cmds.select('pSphere2')
        rig_cut()

        self.stored_buffer = _return_copy_buffer()

        cmds.select('pSphere3')
        rig_paste()

    def test_copy_buffer(self):
        # it has been pasted in setup.  Now the buffer should remain unchanged
        # get buffer again and compare

        current_buffer = _return_copy_buffer()

        # these should be same
        self.assertEquals(self.stored_buffer, current_buffer)

        # lets make some changes to scene to make sure it is a deep copy(buffer should not change)
        cmds.setAttr('zAttachment1.weightList[0].weights[0]', 22)
        cmds.setAttr('zAttachment1.stiffness', 10)

        builder = zva.Ziva()
        builder.retrieve_from_scene()

        # not equal to scene
        self.assertNotEquals(self.stored_buffer, builder)
        # equal to existing buffer
        self.assertEquals(self.stored_buffer, _return_copy_buffer())
