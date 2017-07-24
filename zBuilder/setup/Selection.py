from zBuilder.nodes.base import BaseNode
import zBuilder.nodeCollection as nc
import zBuilder.zMaya as mz

import maya.cmds as mc


class SelectionSetup(nc.NodeCollection):
    def __init__(self):
        nc.NodeCollection.__init__(self)

    def retrieve_from_scene(self):
        selection = mc.ls(sl=True, l=True)
        for sel in selection:
            node = BaseNode()
            node.set_name(sel)
            node.set_type(mz.get_type(sel))
            self.add_node(node)

    def return_selection(self):
        tmp = []
        for node in self.get_nodes():
            tmp.append(node.get_name())

        return tmp

    def apply(self):
        mc.select(self.return_selection())
