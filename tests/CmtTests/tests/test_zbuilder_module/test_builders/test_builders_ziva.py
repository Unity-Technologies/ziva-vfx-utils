import zBuilder.builders.ziva as zva

from maya import cmds
from maya import mel
from vfx_test_case import VfxTestCase
from tests.utils import (build_mirror_sample_geo, build_anatomical_arm_with_no_popup, load_scene,
                         retrieve_builder_from_scene)
from zBuilder.commands import clean_scene
from zBuilder.utils.solverDisabler import SolverDisabler
from zBuilder.nodes.base import Base
from zBuilder.nodes.dg_node import DGNode

class ZivaBuilderSearchExclude(VfxTestCase):

    def setUp(self):
        super(ZivaBuilderSearchExclude, self).setUp()

        # build 1 cube and make it a tissue
        cube = cmds.polyCube()
        cmds.select(cube)
        cmds.ziva(t=True)

        cmds.select(cl=True)

        # use builder to retrieve from scene
        self.z = zva.Ziva()
        self.z.retrieve_from_scene()

    def test_map_class_search_exclude_maps(self):
        # This is testing a fix specific to VFXACT-1328
        # in short, map_type and interp_method were not placed in SEARCH_EXCLUDE so string
        # replacing could change them, breaking features.

        # given that this is a single cube tissue, we should have 2 barycentric maps here. a zTet and zMaterial
        barycentric_maps_pre = []
        for item in self.z.get_scene_items(type_filter='map'):
            if item.interp_method == 'barycentric':
                barycentric_maps_pre.append(item)
        self.assertTrue(len(barycentric_maps_pre) == 2)

        # add a prefix to all seriliazed data
        self.z.string_replace('^','oooooo')

        # now lets check and make sure the values of interp_method method are as they should be.  
        # There are no fibers in this test scene so lets check to make sure value of interp_method has not changed
        # searching through scene_items to find the specific value I am looking for.
        
        # If interp_methd is not part of SEARCH_EXCLUDE, we would not find any barycentric maps
        barycentric_maps_post = []
        for item in self.z.get_scene_items(type_filter='map'):
            if item.interp_method == 'barycentric':
                barycentric_maps_post.append(item)

        # compare pre and post
        self.assertEqual(barycentric_maps_post, barycentric_maps_pre)

    
    def test_search_exclude_inheriting(self):
        # searching through every scene item
        # Check if inherited from Base.
        # Check if ALL Base.SEARCH_EXCLUDE items are in item.SEARCH_EXCLUDE
        # This broke previously when the inheritence was overridding instead of extending
        # Any new nodes that do not inherit proprely will break here
        for item in self.z.get_scene_items():
            if isinstance(item,Base):
                # This will assert if any scene item does not contain Base.SEARCH_EXCLUDE items
                self.assertTrue(all(x in item.SEARCH_EXCLUDE for x in Base.SEARCH_EXCLUDE))
            if isinstance(item,DGNode):
                # This will assert if any scene item does not contain DGNode.SEARCH_EXCLUDE items
                self.assertTrue(all(x in item.SEARCH_EXCLUDE for x in DGNode.SEARCH_EXCLUDE))


class ZivaBuilderMirrorTestCase(VfxTestCase):

    def setUp(self):
        super(ZivaBuilderMirrorTestCase, self).setUp()
        # Build a basic setup
        build_mirror_sample_geo()
        cmds.select(cl=True)

        # use builder to retrieve from scene
        self.z = zva.Ziva()
        self.z.retrieve_from_scene()

        # string replace
        self.z.string_replace('^r_', 'l_')

    def test_mirror_existing_scene(self):
        # # build it on live scene
        self.z.build()

        # check if left muscle is connected to zGeo
        self.assertTrue(len(cmds.listConnections('l_muscle', type='zGeo')))


class ZivaBuilderTestCase(VfxTestCase):

    def setUp(self):
        super(ZivaBuilderTestCase, self).setUp()

        # This builds the Zivas anatomical arm demo with no pop up dialog.
        build_anatomical_arm_with_no_popup()

        # clear selection.  It should retrieve whole scene
        cmds.select(cl=True)

        # use builder to retrieve from scene-----------------------------------
        self.builder = zva.Ziva()
        self.builder.retrieve_from_scene()

    def test_retrieve_selected(self):
        # This builds the Zivas anatomical arm demo with no pop up dialog.
        build_anatomical_arm_with_no_popup()

        # select a muscle geo
        cmds.select('r_bicep_muscle')

        # use builder to retrieve from scene-----------------------------------
        z = zva.Ziva()
        z.retrieve_from_scene_selection()

        # build
        z.build()

        # check amount of zTissue and zTet.  Should be 1 of each
        items = z.get_scene_items(type_filter=['zTet', 'zTissue'])

        self.assertEqual(len(items), 2)

    def test_retrieve_from_scene(self):
        zAttachments = cmds.ls(type='zAttachment')
        # remove ziva nodes from scene so all we have left is geo
        clean_scene()

        # build
        self.builder.build()
        self.assertTrue(len(zAttachments) == len(cmds.ls(type='zAttachment')))

    def test_string_replace(self):
        # remove ziva nodes from scene so all we have left is geo
        clean_scene()

        cmds.rename('r_bicep_muscle', 'r_biceps_muscle')
        self.builder.string_replace('r_bicep_muscle', 'r_biceps_muscle')

        # build
        self.builder.build()

        # after its build check scene for the proper named zTissue
        self.assertSceneHasNodes(['r_biceps_muscle_zTissue'])

    def test_build_permissive_false(self):
        # remove ziva nodes from scene so all we have left is geo
        clean_scene()

        # now lets delete bicep to see how build handles it
        cmds.delete('r_bicep_muscle')

        with self.assertRaises(Exception):
            self.builder.build(permissive=False)

    def test_bad_mesh_error(self):
        # make sure we get an error if mesh fails a check
        clean_scene()

        # now lets scale muscle to make it invalid
        cmds.setAttr('r_bicep_muscle.scaleX', l=False)
        cmds.setAttr('r_bicep_muscle.scaleY', l=False)
        cmds.setAttr('r_bicep_muscle.scaleX', 0)
        cmds.setAttr('r_bicep_muscle.scaleY', 0)

        with self.assertRaises(Exception):
            self.builder.build()

    def test_tissue_attrs_not_updating(self):
        # this tests an issue of zTissues not updating attributes if the
        # tissue is not created.  In that case it would skip over the attr
        # changing.  As seen in VFXACT-89

        # to test this lets change an attribute on a tissue
        cmds.setAttr("r_bicep_muscle_zTissue.inertialDamping", .5)

        # now build from the zBuilder
        self.builder.build()

        # if the attribute is 0 we know it worked
        self.assertTrue(cmds.getAttr("r_bicep_muscle_zTissue.inertialDamping") == 0)

    def test_retrieve_connections_single(self):
        # this tests retrieve_connections on a a full setup where you have 1 tissue
        # selected with no attachments.  This was a bug fix.  The expected result
        # is there should be 1 tissue in object.  What was happening is it was
        # getting whole scene.

        # the arm is built in scene so all we need to do is create sphere and retrieve
        sph = cmds.polySphere()
        mel.eval('ziva -t')
        cmds.select(sph)

        z = zva.Ziva()
        z.retrieve_connections()

        self.assertEqual(1, len(z.get_scene_items(type_filter='zTissue')))


class RetrieveConnectionsOrderTestCase(VfxTestCase):

    def test_order_retrieved(self):
        desired_type_order = zva.ZNODES
        load_scene("generic_tissue.ma")
        builder = zva.Ziva()
        builder.retrieve_connections()
        retrieved = builder.get_scene_items(type_filter=['map', 'mesh'], invert_match=True)
        retrieved_type_order = [x.type for x in retrieved]
        # remove duplicates from retrieved_type_order.
        seen = set()
        seen_add = seen.add
        retrieved_type_order = [
            str(x) for x in retrieved_type_order if not (x in seen or seen_add(x))
        ]
        # remove items from desired that are not represented in retrieved_by_type
        new_desired_type_order = []
        for item in desired_type_order:
            if item in retrieved_type_order:
                new_desired_type_order.append(item)
        # the retrieved_type_order is going to have a few extra node types at end of list.
        # the items NOT in ZNODES needs to be at the end, this is up for refactor
        # when this ticket is done then this can do a complete equal
        self.assertEqual(new_desired_type_order,
                         retrieved_type_order[0:len(new_desired_type_order)])


class ZivaSolverDisableTestCase(VfxTestCase):

    def test_enable_connected(self):
        # build scene and connect the enable to something
        load_scene('generic.ma')
        loc = cmds.spaceLocator()[0]
        cmds.connectAttr('{}.translateX'.format(loc), 'zSolver1.enable')

        retrieved_builder = retrieve_builder_from_scene()

        retrieved_builder.build()

        current_connection = cmds.listConnections('zSolver1.enable', plugs=True)[0]
        self.assertEqual(current_connection, '{}.translateX'.format(loc))

    def test_SolverDisabler_class_connected(self):
        mel.eval('ziva -s')
        loc = cmds.spaceLocator()[0]
        cmds.setAttr('{}.translateX'.format(loc), 1)  # So that enable will start off being True!
        cmds.connectAttr('{}.translateX'.format(loc), 'zSolver1.enable')

        self.assertTrue(cmds.getAttr('zSolver1.enable'))
        self.assertTrue(cmds.listConnections('zSolver1.enable'))

        with SolverDisabler('zSolver1'):
            self.assertFalse(cmds.getAttr('zSolver1.enable'))
            self.assertFalse(cmds.listConnections('zSolver1.enable'))

        self.assertTrue(cmds.getAttr('zSolver1.enable'))
        self.assertTrue(cmds.listConnections('zSolver1.enable'))

    def test_SolverDisabler_class_not_connected(self):
        mel.eval('ziva -s')
        self.assertTrue(cmds.getAttr('zSolver1.enable'))
        with SolverDisabler('zSolver1'):
            self.assertFalse(cmds.getAttr('zSolver1.enable'))
        self.assertTrue(cmds.getAttr('zSolver1.enable'))

    def test_SolverDisabler_does_not_enable_a_disabled_solver(self):
        mel.eval('ziva -s')
        cmds.setAttr('zSolver1.enable', False)
        with SolverDisabler('zSolver1'):
            self.assertFalse(cmds.getAttr('zSolver1.enable'))
        self.assertFalse(cmds.getAttr('zSolver1.enable'))