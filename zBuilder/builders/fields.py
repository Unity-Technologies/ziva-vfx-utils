from zBuilder.builder import Builder
from zBuilder.mayaUtils import parse_maya_node_for_selection, FIELD_TYPES
from zBuilder.commonUtils import time_this
from maya import cmds


class Fields(Builder):
    """ Storing maya fields.
    """
    @time_this
    def retrieve_from_scene(self, *args, **kwargs):
        selection = parse_maya_node_for_selection(args)

        history = cmds.listHistory(selection)
        fields = cmds.ls(history, type=FIELD_TYPES)
        for field in fields:
            scene_items = self.node_factory(field)
            self.bundle.extend_scene_items(scene_items)
        self.stats()

    @time_this
    def build(self):
        for scene_item in self.get_scene_items():
            scene_item.build()
