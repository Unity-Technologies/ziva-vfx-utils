from zBuilder.main import Builder
import zBuilder.nodes.base as base
import zBuilder.nodeCollection as nc
import zBuilder.zMaya as mz

import maya.cmds as mc


class AttributesSetup(Builder):
    '''
    Storing maya attributes
    '''

    def __init__(self):
        Builder.__init__(self)

    @Builder.time_this
    def retrieve_from_scene(self):
        selection = mc.ls(sl=True, l=True)

        for sel in selection:
            nodeAttrList = base.build_attr_list(sel)
            nodeAttrs = base.build_attr_key_values(sel, nodeAttrList)

            node = base.BaseNode()
            node.set_name(sel)
            node.set_type(mz.get_type(sel))
            node.set_attrs(nodeAttrs)
            self.add_node(node)

        self.stats()

    @Builder.time_this
    def apply(self):
        nodes = self.get_nodes()
        for node in nodes:
            self.set_maya_attrs_for_builder_node(node)
