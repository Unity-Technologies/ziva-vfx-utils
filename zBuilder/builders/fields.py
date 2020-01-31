from zBuilder.builder import Builder
from maya import cmds
import zBuilder.zMaya as mz


class Fields(Builder):
    """Storing maya fields.
    """

    MAYA_FIELD_TYPE = ('airField', 'dragField', 'gravityField', 'newtonField', 'radialField',
                       'turbulenceField', 'uniformField', 'vortexField')

    @Builder.time_this
    def retrieve_from_scene(self, *args, **kwargs):
        selection = mz.parse_maya_node_for_selection(args)

        history = cmds.listHistory(selection)
        fields = cmds.ls(history, type=self.MAYA_FIELD_TYPE)
        for field in fields:
            scene_items = self.node_factory(field)
            self.bundle.extend_scene_items(scene_items)
        self.stats()

    @Builder.time_this
    def build(self):
        for scene_item in self.get_scene_items():
            scene_item.build()
