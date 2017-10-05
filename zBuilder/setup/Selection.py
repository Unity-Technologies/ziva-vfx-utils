from zBuilder.nodes.base import BaseNode
from zBuilder.builder import Builder
import zBuilder.zMaya as mz

import maya.cmds as mc


class SelectionSetup(Builder):
    def __init__(self):
        Builder.__init__(self)

    def retrieve_from_scene(self):
        selection = mc.ls(sl=True, l=True)
        for sel in selection:
            node = BaseNode()
            node.set_name(sel)
            node.set_type(mz.get_type(sel))
            self.add_node(node)

    def apply(self, select=True):
        tmp = []
        for node in self.get_nodes():
            tmp.append(node.get_name())

        if select:
            mc.select(tmp)
        return tmp
