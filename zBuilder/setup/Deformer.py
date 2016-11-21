
import zBuilder.nodes.base as base
import zBuilder.nodeCollection as nc
import zBuilder.zMaya as mz

import maya.cmds as mc
import maya.mel as mm


class DeformerSetup(nc.NodeCollection):
    def __init__(self):
        nc.NodeCollection.__init__(self)

    def get_stuff(self,selection):
        #clusters = get_scene_cluster(selection)

        for s in selection:
            attrList = mz.get_attrs_list(s)
            attrs = mz.get_attrs(s,attrList)
            associations = get_associated_mesh(s)

            node = base.BaseNode()
            node.set_name(s)
            node.set_association(get_associated_mesh(s))
            node.set_type(mz.get_type(s))
            node.set_attrs(attrs)


            mapList = ['weightList[0].weights']
            if mc.objExists('%s.%s' % (s,mapList[0])):
                maps = mz.get_weights(s,associations,mapList)
                node.set_maps(maps)
                self.add_mesh(associations[0],mz.get_mesh_info(associations[0]))

            self.add_node(node)


    def build_clusters(self):
        nodes = self.get_nodes()

        for node in nodes:
            name = cn.get_name()
            association = cn.get_association()
            if not mc.objExists(name):
                mc.select(association,r=True)
                mc.cluster(name=name)

        mz.set_attrs(clusterNodes)

        # mc.rename(tmp[0],'zGeo_'+muscle)
        # mc.rename(tmp[1],zBone)

  


def get_scene_cluster(selection):
    sel = mc.ls(sl=True)
    hist = mc.listHistory(sel)
    return mc.ls(hist,type='cluster')

def get_associated_mesh(selection):
    mesh = mc.listConnections(selection+'.outputGeometry[0]')
    return mesh