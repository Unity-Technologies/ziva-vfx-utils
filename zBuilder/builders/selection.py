from .builder import Builder
from zBuilder.commonUtils import time_this
from maya import cmds


class Selection(Builder):
    """Storing maya selection.
    """

    @time_this
    def retrieve_from_scene(self):
        selection = cmds.ls(sl=True, l=True)

        for item in selection:
            scene_item = self.node_factory(item)
            self.bundle.extend_scene_items(scene_item)
        self.stats()

    @time_this
    def build(self, select=True):
        tmp = []
        for node in self.get_scene_items():
            tmp.append(node.name)

        if select:
            cmds.select(tmp)
        return tmp
