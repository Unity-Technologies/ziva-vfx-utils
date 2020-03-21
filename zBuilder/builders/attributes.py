from zBuilder.builder import Builder
from maya import cmds


class Attributes(Builder):
    """Storing maya attributes
    """

    @Builder.time_this
    def retrieve_from_scene(self):
        selection = cmds.ls(sl=True, l=True)

        for item in selection:
            scene_items = self.node_factory(item, get_parameters=False)
            self.bundle.extend_scene_items(scene_items)
        self.stats()

    @Builder.time_this
    def build(self):
        scene_items = self.get_scene_items()
        for item in scene_items:
            item.set_maya_attrs()
