import zBuilder.nodes.base as base
import zBuilder.nodeCollection as nc
import zBuilder.zMaya as mz


import maya.cmds as mc


TYPES = ['parentConstraint','orientConstraint']


class ConstraintsSetup(nc.NodeCollection):
    def __init__(self):
        super(ConstraintsSetup,self).__init__()

    def retrieve_from_scene(self):
        sel = mc.ls(sl=True,l=True)

        for type_ in TYPES:
            constraints = mc.listConnections(sel,type=type_,s=True,d=False)
            con = []
            if constraints:
                con = list(set(constraints))

            for c in con:

                nodeAttrList = base.build_attr_list(c)
                nodeAttrs = base.build_attr_key_values(c,nodeAttrList)

                node = base.BaseNode()
                node.set_name(c)
                node.set_type(mz.get_type(c))
                node.set_attrs(nodeAttrs)
                node.set_association([self.get_target(c),self.get_source(c)])
                self.add_node(node)

        self.stats()
        mc.select(sel)

    def get_target(self,node):
        _type = mz.get_type(node)
        if _type == 'parentConstraint':
            return mc.listConnections(node+'.target[0].targetScale')[0]
        if _type == 'orientConstraint':
            return mc.listConnections(node+'.target[0].targetRotate')[0]

    def get_source(self,node):
        return mc.listConnections(node+'.constraintRotateX')[0]

    def apply(self):
        nodes = self.get_nodes()
        
        for n in nodes:
            name = n.get_name()
            _type = n.get_type()
            if not mc.objExists(name):
                if _type == 'parentConstraint':
                    ass = n.get_association()
                    if mc.objExists(ass[0]) and mc.objExists(ass[1]):
                        mc.parentConstraint(ass[0],ass[1],mo=True)
                if _type == 'orientConstraint':
                    ass = n.get_association()
                    if mc.objExists(ass[0]) and mc.objExists(ass[1]):
                        mc.orientConstraint(ass[0],ass[1],mo=True)

        base.set_attrs(nodes)