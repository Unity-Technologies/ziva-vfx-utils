import os
import zBuilder.builders.ziva as zva

from vfx_test_case import VfxTestCase
from tests.utils import get_1_7_builder_files, load_scene
from zBuilder.commands import clean_scene


class Builder1_7_to_1_9TestCase(VfxTestCase):

    def setUp(self):
        super(Builder1_7_to_1_9TestCase, self).setUp()
        self.builders_1_7 = get_1_7_builder_files()

    def test_build_1_7(self):
        # Act
        for item in self.builders_1_7:
            # find corresponding maya file
            basename = os.path.basename(item)
            maya_file = basename.replace('_1_7.zBuilder', '.ma')

            # open it and clean scene so we have just geo
            load_scene(maya_file)
            clean_scene()

            builder = zva.Ziva()
            builder.retrieve_from_file(item)

            builder.build()

            self.compare_builder_nodes_with_scene_nodes(builder)
            self.compare_builder_attrs_with_scene_attrs(builder)
            self.compare_builder_maps_with_scene_maps(builder)
