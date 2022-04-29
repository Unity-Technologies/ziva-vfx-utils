import unittest
import zBuilder.builders.ziva as zva

from maya import cmds
from vfx_test_case import VfxTestCase
from tests.utils import reference_scene
from zBuilder.commands import clean_scene


class ReferenceTestCase(VfxTestCase):

    def setUp(self):
        super(ReferenceTestCase, self).setUp()
        reference_scene('mirror_example.ma', namespace="TEMP")
        self.builder = zva.Ziva()
        self.builder.retrieve_from_scene()

    def check_builder_nodes_built_in_scene(self, builder):
        # goes every node in a builder and checks by name if they are in the scene.
        # useful for checking after a build if everything built.
        items = builder.get_scene_items(type_filter=['map', 'mesh'], invert_match=True)

        for item in items:
            self.assertTrue(cmds.objExists(item.name))

    def check_builder_nodes_setattr_in_scene(self, builder):
        # goes through every attribute in builder and checks if the same nodes in scene have same
        # value.  Useful for checking if a build worked on attribute changes.
        items = builder.get_scene_items(type_filter=['map', 'mesh'], invert_match=True)

        for item in items:
            for attr, v in item.attrs.items():
                self.assertEquals(v['value'], cmds.getAttr('{}.{}'.format(item.name, attr)))

    def test_write_and_read_build_on_referenced_full_setup(self):
        builder = self.get_builder_after_writing_and_reading_from_disk(self.builder)

        # Change an attribute in builder and check that came through
        for item in builder.get_scene_items(type_filter='zTissue'):
            item.attrs['surfaceTensionEnvelope']['value'] = 0.52
            self.assertEquals(0.52, item.attrs['surfaceTensionEnvelope']['value'])

        # reference full ziva setup
        reference_scene('mirror_example.ma', namespace="TEMP")

        builder.build()

        # this will have new value of tet
        self.check_builder_nodes_built_in_scene(builder)
        self.check_builder_nodes_setattr_in_scene(builder)

    def test_write_and_read_build_on_referenced_geo_only(self):
        builder = self.get_builder_after_writing_and_reading_from_disk(self.builder)

        # Change an attribute in builder and check that came through
        for item in builder.get_scene_items(type_filter='zTissue'):
            item.attrs['surfaceTensionEnvelope']['value'] = 0.52
            self.assertEquals(0.52, item.attrs['surfaceTensionEnvelope']['value'])

        # reference geo only
        reference_scene('mirror_example-geo.ma', namespace="TEMP")

        builder.build()

        # this will have new value of tet
        self.check_builder_nodes_built_in_scene(builder)
        self.check_builder_nodes_setattr_in_scene(builder)

    def test_write_and_read_build_and_mirror_on_referenced_geo_only(self):
        # half is ziva setup half is empty.  So we doing a string replace on refrerenced and
        # building the other side.
        builder = self.get_builder_after_writing_and_reading_from_disk(self.builder)

        # Change an attribute in builder and check that came through
        for item in builder.get_scene_items(type_filter='zTissue'):
            item.attrs['surfaceTensionEnvelope']['value'] = 0.52
            self.assertEquals(0.52, item.attrs['surfaceTensionEnvelope']['value'])

        # reference geo only
        reference_scene('mirror_example-geo.ma', namespace="TEMP")

        builder.string_replace('TEMP:l_', 'TEMP:r_')
        builder.build()

        # this will have new value of tet
        self.check_builder_nodes_built_in_scene(builder)
        self.check_builder_nodes_setattr_in_scene(builder)

    @unittest.expectedFailure
    def test_clean_scene_on_referenced_scene(self):

        clean_scene()

        tissues_in_scene = cmds.ls(type='zTissue')
        self.assertEquals(0, len(tissues_in_scene))


class ReferenceMirrorTestCase(VfxTestCase):
    """This Class tests a specific type of "mirroring" so there are some assumptions made

    - geometry has an identifiable qualifier, in this case it is l_ and r_
    - Both sides geometry are in the scene
    - One side has Ziva VFX nodes and other side does not, in this case l_ has Ziva nodes

    """

    def setUp(self):
        super(ReferenceMirrorTestCase, self).setUp()
        reference_scene('mirror_example.ma')
        self.builder = zva.Ziva()
        self.builder.retrieve_from_scene()

        # gather info
        self.types = [
            'zTissue',
            'zTet',
            'zAttachment',
            'zRivetToBone',
            'zRestShape',
            'zMaterial',
            'zLineOfAction',
            'zFiber',
            'zBone',
        ]
        self.scene_items_retrieved = self.builder.get_scene_items(type_filter=self.types)
        self.l_item_geo = [
            x for x in self.scene_items_retrieved if x.association[0].startswith('l_')
        ]

    def check_retrieve_ztissue_looks_good(self, builder, expected_plugs):
        """Args:
            builder (builders.ziva.Ziva()): builder object
            expected_plugs (dict): A dict of expected attribute/value pairs.
                                   {'zTissue1.collisions':True, ...}.
                                   If None/empty/False, then attributes are taken from zBuilder
                                   and values are taken from the scene.
                                   Test fails if zBuilder is missing any of the keys
                                   or has any keys with different values.
        """
        item_names = [x.name for x in self.scene_items_retrieved]
        for type_ in self.types:
            self.check_retrieve_looks_good(builder, expected_plugs, item_names, type_)

    def test_builder_change_with_string_replace(self):
        ## VERIFY

        # find left and right tissue items regardless of name, by looking at mesh they
        # are tied to
        r_item_geo = [x for x in self.scene_items_retrieved if x.association[0].startswith('r_')]
        self.assertEqual(len(self.l_item_geo), 0)  # Left geo should have been all renamerd to r_
        self.assertEqual(r_item_geo, [])  # Make sure no r_ geo is in original scene

        ## ACT
        self.builder.string_replace("^l_", "r_")

        ## VERIFY
        new_left_geo = [x for x in self.scene_items_retrieved if x.association[0].startswith('l_')]
        r_item_geo = [x for x in self.scene_items_retrieved if x.association[0].startswith('r_')]
        self.assertEqual(len(self.l_item_geo),
                         len(r_item_geo))  # number of right geos equal original left
        self.assertEqual(new_left_geo, [])  # after replace left geo should have been renamed

    def test_builder_build_with_string_replace(self):
        # ACT
        self.builder.string_replace("^l_", "r_")
        self.builder.build()

        # VERIFY
        item_names_in_builder = [x.name for x in self.scene_items_retrieved]
        # Original Ziva nodes should still be in scene
        self.assertSceneHasNodes(item_names_in_builder)

        # comparing attribute values between builder and scene
        for scene_item in self.scene_items_retrieved:
            scene_name = scene_item.name
            for attr in scene_item.attrs.keys():
                scene_value = cmds.getAttr('{}.{}'.format(scene_name, attr))
                self.assertTrue(scene_value == scene_item.attrs[attr]['value'])
