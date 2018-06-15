from zBuilder.builder import Builder
import maya.cmds as mc


class Attributes(Builder):
    """Storing maya attributes
    """

    def __init__(self):
        Builder.__init__(self)

    @Builder.time_this
    def retrieve_from_scene(self):
        selection = mc.ls(sl=True, l=True)

        for item in selection:
            parameter = self.node_factory(item)
            self.bundle.extend_scene_items(parameter)
        self.stats()

    @Builder.time_this
    def build(self):
        parameters = self.get_scene_items()
        for parameter in parameters:
            parameter.set_maya_attrs()
