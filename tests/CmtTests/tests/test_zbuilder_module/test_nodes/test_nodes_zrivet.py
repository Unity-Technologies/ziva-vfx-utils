import zBuilder.builders.ziva as zva

from maya import cmds
from maya import mel
from vfx_test_case import VfxTestCase
from tests.utils import build_anatomical_arm_with_no_popup
from zBuilder.commands import clean_scene, remove_solver


class ZivaRivetTestCase(VfxTestCase):

    def setUp(self):
        super(ZivaRivetTestCase, self).setUp()

        # This builds the Zivas anatomical arm demo with no pop up dialog.
        build_anatomical_arm_with_no_popup()

        # create l
        cmds.select('r_tricepsLong_muscle')
        crv = mel.eval('zLineOfActionUtil')[0]
        cmds.select(crv + '.cv[0]', 'r_humerus_bone')
        self.riv1 = mel.eval('zRivetToBone')
        cmds.select(crv + '.cv[1]', 'r_scapula_bone')
        self.riv2 = mel.eval('zRivetToBone')
        cmds.select('r_tricepsLong_muscle', crv)
        mel.eval('ziva -loa;')

    def test_retrieve_rivet_scene(self):
        # use builder to retrieve from scene-----------------------------------
        cmds.select(cl=True)
        z = zva.Ziva()
        z.retrieve_from_scene()

        # check that 2 rivets are in zBuilder
        rivets = z.get_scene_items(type_filter='zRivetToBone')
        self.assertEqual(len(rivets), 2)

    def test_retrieve_rivet_selection(self):
        # use builder to retrieve from scene-----------------------------------
        cmds.select('r_tricepsLong_muscle')
        z = zva.Ziva()
        z.retrieve_from_scene_selection()

        # check that 2 rivets are in zBuilder
        rivets = z.get_scene_items(type_filter='zRivetToBone')
        self.assertEqual(len(rivets), 2)

    def test_retrieve_rivet_selection_none(self):
        # use builder to retrieve from scene-----------------------------------
        cmds.select('r_bicep_muscle')
        z = zva.Ziva()
        z.retrieve_from_scene_selection()

        # check that there are 0 rivets in scene (based on selection)
        rivets = z.get_scene_items(type_filter='zRivetToBone')
        self.assertEqual(len(rivets), 0)

    def test_build_rivet(self):
        # use builder to retrieve from scene-----------------------------------
        cmds.select('r_tricepsLong_muscle')
        z = zva.Ziva()
        z.retrieve_from_scene()

        clean_scene()

        z.build()

        # should be 2 in scene
        self.assertEqual(len(cmds.ls(type='zRivetToBone')), 2)

    def test_retrieve_rivet_scene_multiple_cvs(self):
        # create a rivetToBone driving 2 cv's
        cmds.select('r_bicep_muscle')
        crv = mel.eval('zLineOfActionUtil')[0]
        cmds.select(crv + '.cv[0]', crv + '.cv[1]', 'r_humerus_bone')
        riv2 = mel.eval('zRivetToBone')
        cmds.select('r_bicep_muscle', crv)
        mel.eval('ziva -loa;')

        cmds.select(cl=True)
        z = zva.Ziva()
        z.retrieve_from_scene()

        # check that 3 rivets are in zBuilder
        rivets = z.get_scene_items(type_filter='zRivetToBone')
        self.assertEqual(len(rivets), 3)

    def test_build_rivet_multiple_cvs(self):
        # create a rivetToBone driving 2 cv's
        cmds.select('r_bicep_muscle')
        crv = mel.eval('zLineOfActionUtil')[0]
        cmds.select(crv + '.cv[0]', crv + '.cv[1]', 'r_humerus_bone')
        riv2 = mel.eval('zRivetToBone')
        cmds.select('r_bicep_muscle', crv)
        mel.eval('ziva -loa;')

        # use builder to retrieve from scene-----------------------------------
        cmds.select(cl=True)
        z = zva.Ziva()
        z.retrieve_from_scene()

        clean_scene()

        z.build()

        # should be 2 in scene
        self.assertEqual(len(cmds.ls(type='zRivetToBone')), 3)

    def test_retrieve_connections_rivet(self):
        # this tests if retrieve_connections works if a rivet is selected
        cmds.select(self.riv1)
        builder = zva.Ziva()
        builder.retrieve_connections()

        # should not be empty
        self.assertTrue(len(builder.get_scene_items()) > 0)

    def test_retrieve_connections_rivet_check(self):
        # this tests if retrieve_connections works if a rivet is selected
        cmds.select(self.riv1)
        builder = zva.Ziva()
        builder.retrieve_connections()

        # this should have grabbed the specific loa
        result = builder.get_scene_items(name_filter=self.riv1)

        # result will have named loa
        self.assertEqual(len(result), 1)

    def test_delete_solver_with_rivet(self):
        cmds.select('zSolver1')
        remove_solver()

        self.assertEquals(cmds.ls(type=['zSolver', 'zRivetToBone', 'zRivetToBoneLocator']), [])
