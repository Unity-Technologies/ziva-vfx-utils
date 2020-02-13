import os
import zBuilder.builders.ziva as zva
import tests.utils as test_utils
import zBuilder.utils as utils
import zBuilder.zMaya as mz
from maya import cmds

from vfx_test_case import VfxTestCase


class ZivaReferenceGenericTestCase(VfxTestCase):
    def setUp(self):
        super(ZivaReferenceGenericTestCase, self).setUp()
        test_utils.reference_scene(scene_name="generic.ma")
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
            for attr, v in item.attrs.iteritems():

                # TODO oLength is on zLineOfAction and it is not settable.  So skipping over here:
                # We should maybe not aquire non-settable attributes OR define them as non-settable
                # and automatically deal with them in set_maya_attrs
                if attr != 'oLength':
                    self.assertEquals(v['value'], cmds.getAttr('{}.{}'.format(item.name, attr)))

    def test_write_and_read_build(self):
        builder = self.get_builder_after_writing_and_reading_from_disk(self.builder)

        # reference geo only
        test_utils.reference_scene(scene_name="generic_geo.ma")

        builder.build()

        self.check_builder_nodes_built_in_scene(builder)
        self.check_builder_nodes_setattr_in_scene(builder)
