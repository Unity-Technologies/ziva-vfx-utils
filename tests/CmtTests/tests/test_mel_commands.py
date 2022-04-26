import maya.mel as mel
from vfx_test_case import VfxTestCase


class MelCommandTestCase(VfxTestCase):

    def setUp(self):
        super(MelCommandTestCase, self).setUp()

    def tearDown(self):
        super(MelCommandTestCase, self).tearDown()

    def test_ziva_universal_commands_accessible(self):
        '''
        Verify if ziva universal commands are accessible
        from where MAYA_MODULE_PATH or MAYA_SCRIPT_PATH is specified
        '''
        # Maya should not crash nor report error like,
        # Cannot find procedure "ZivaToggleEnabled"
        mel.eval('ZivaToggleEnabled()')
