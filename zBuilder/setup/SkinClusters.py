import zBuilder.nodes.base as base
import zBuilder.nodeCollection as nc
import zBuilder.zMaya as mz


import maya.cmds as mc

weightsList = ['weightList[0].weights']

class SkinClusterSetup(nc.NodeCollection):
    def __init__(self):
        nc.NodeCollection.__init__(self)

    def get_skinClusters(self,selection):
    
        for sel in selection:
            sc = mc.listConnections(sel+'Shape',type='skinCluster')
            if sc:
                sc=sc[0]
                influences = mc.skinCluster(sc,q=True,influence=True)
                nodeAttrList = mz.get_attrs_list(sc)
                nodeAttrs = mz.get_attrs(sc,nodeAttrList)

                maps = mz.get_weights(sc,[sel],weightsList)



                node = base.BaseNode()
                node.set_name(sc)
                node.set_type(mz.get_type(sc))
                node.set_attrs(nodeAttrs)
                node.set_association(influences)
                #node.set_maps(maps)
                self.add_node(node)


                # for _type in _types:
                #     constraints = mc.listConnections(sel,type=_type)
                #     con = []
                #     if constraints:
                #         con = list(set(constraints))

                #     for c in con:

                #         nodeAttrList = mz.get_attrs_list(c)
                #         nodeAttrs = mz.get_attrs(c,nodeAttrList)

                #         node = base.BaseNode()
                #         node.set_name(c)
                #         node.set_type(mz.get_type(c))
                #         node.set_attrs(nodeAttrs)
                #         node.set_association([self.get_target(c),sel])
                #         self.add_node(node)

        self.stats()


    def build_constraints(self):
        nodes = self.get_nodes()
        
        for n in nodes:
            name = n.get_name()
            _type = n.get_type()
            if not mc.objExists(name):
                if _type == 'parentConstraint':
                    ass = n.get_association()
                    mc.parentConstraint(ass[0],ass[1],mo=True)

