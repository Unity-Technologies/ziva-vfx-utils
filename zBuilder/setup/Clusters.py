
import nodes.base as base
import zMaya as mz
import maya.cmds as mc
import maya.mel as mm

import nodeCollection as nc


class Test(nc.NodeCollection):
    def __init__(self):
        nc.NodeCollection.__init__(self)

    def get_cluster(self,selection):
        clusters = get_scene_cluster(selection)

        for cluster in clusters:
            node = base.BaseNode()
            node.set_name(cluster)
            node.set_association(get_cluster_mesh(cluster))
            node.set_type('cluster')
            node.set_attrs(mz.get_attrs(cluster))
            self.add_node(node)


    def build_clusters(self):
        clusterNodes = self.get_nodes(_type='cluster')

        for cn in clusterNodes:
            print cn
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

def get_cluster_mesh(cluster):
    mesh = mc.listConnections(cluster+'.outputGeometry[0]')[0]
    return mesh