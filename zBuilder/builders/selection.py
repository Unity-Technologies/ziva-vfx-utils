from zBuilder.builder import Builder
import maya.cmds as mc


class Selection(Builder):
    """Storing maya selection.
    """

    def __init__(self):
        Builder.__init__(self)

    @Builder.time_this
    def retrieve_from_scene(self):
        selection = mc.ls(sl=True, l=True)

        for item in selection:
            scene_item = self.node_factory(item)
            self.bundle.extend_scene_items(scene_item)
        self.stats()

    @Builder.time_this
    def build(self, select=True):
        tmp = []
        for node in self.get_scene_items():
            tmp.append(node.get_scene_name())

        if select:
            mc.select(tmp)
        return tmp
