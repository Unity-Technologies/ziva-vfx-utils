from zBuilder.builder import Builder
import maya.cmds as mc


class AttributesSetup(Builder):
    """
    Storing maya attributes
    """

    def __init__(self):
        Builder.__init__(self)

    @Builder.time_this
    def retrieve_from_scene(self):
        selection = mc.ls(sl=True, l=True)

        for item in selection:
            b_node = self.node_factory(item)
            self.add_node(b_node)
        self.stats()

    @Builder.time_this
    def build(self):
        b_nodes = self.get_nodes()
        for b_node in b_nodes:
            b_node.set_maya_attrs()
