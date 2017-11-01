import zBuilder.parameters.base as base
import zBuilder.parameters.skinCluster as sc
# import zBuilder.nodeCollection as nc
import zBuilder.zMaya as mz

from zBuilder.builder import Builder

import maya.OpenMaya as OpenMaya
import maya.OpenMayaAnim as OpenMayaAnim
import maya.cmds as mc

weightsList = ['weightList[0].weights']


class SkinClusterSetup(Builder):
    def __init__(self):
        nc.NodeCollection.__init__(self)

    @Builder.time_this
    def retrieve_from_scene(self):

        selection = mc.ls(sl=True, l=True)

        for sel in selection:
            history = mc.listHistory(sel)
            skinCluster = mc.ls(history, type='skinCluster')
            if skinCluster:
                skinCluster = skinCluster[0]
                influences = mc.skinCluster(skinCluster, q=True, influence=True)
                nodeAttrList = base.build_attr_list(skinCluster)
                nodeAttrs = base.build_attr_key_values(skinCluster, nodeAttrList)

                mesh = mc.skinCluster(skinCluster, g=True, q=True)[0]

                # size = mc.getAttr(sel+'.weightList',s=True)
                # ifs = str(len(influences)-1)

                # tmp = {}
                # for i in range(0,size):
                #     attr = 'weightList['+str(i)+'].weights'
                #     tmp[attr] = {}
                #     tmp[attr]['value'] = mc.getAttr(sel+'.'+attr+'[0:'+ifs+']')
                #     tmp[attr]['mesh'] = mesh

                weights = get_weights(skinCluster)
                node = sc.SkinClusterNode()
                node.set_name(skinCluster)
                node.set_type(mz.get_type(skinCluster))
                node.set_attrs(nodeAttrs)
                node.set_influences(influences)
                node.set_maps(weights)
                node.set_association([mesh])
                self.add_node(node)
                # self.add_data('mesh',mesh)

        self.stats()

    @Builder.time_this
    def apply(self, interp_maps=False):
        nodes = self.get_nodes()

        for n in nodes:
            name = n.get_name()
            _type = n.get_type()
            mesh = n.get_association()
            influences = n.get_influences()

            # print name,_type,mesh


            if not mc.listConnections(mesh, type='skinCluster'):
                mc.select(influences, mesh, r=True)
                mc.skinCluster(tsb=True, n=name)

            maps = n.get_maps()
            apply_weights(name, mesh, influences, maps)
            # print maps

        # msh.set_weights(nodes,self.get_data_by_key('mesh'),interp_maps=interp_maps)
        base.set_attrs(nodes)


def apply_weights(cluster, mesh, influences, weights):
    # unlock influences used by skincluster
    for inf in influences:
        mc.setAttr('%s.liw' % inf, 0)

    # normalize needs turned off for the prune to work
    skinNorm = mc.getAttr('%s.normalizeWeights' % cluster)
    if skinNorm != 0:
        mc.setAttr('%s.normalizeWeights' % cluster, 0)
    mc.skinPercent(cluster, mesh, nrm=False, prw=100)

    # restore normalize setting
    if skinNorm != 0:
        mc.setAttr('%s.normalizeWeights' % cluster, skinNorm)

    # set the weights
    for attr, vals in weights.items():
        for idx, val in vals.items():
            # print cluster,attr,idx,val
            mc.setAttr('%s.%s[%s]' % (cluster, attr, str(idx)), val)


def get_weights(skinCluster):
    # get the MFnSkinCluster for skinCluster
    selList = OpenMaya.MSelectionList()
    selList.add(skinCluster)
    clusterNode = OpenMaya.MObject()
    selList.getDependNode(0, clusterNode)
    skinFn = OpenMayaAnim.MFnSkinCluster(clusterNode)

    # get the MDagPath for all influence
    infDags = OpenMaya.MDagPathArray()
    skinFn.influenceObjects(infDags)

    # create a dictionary whose key is the MPlug indice id and 
    # whose value is the influence list id
    infIds = {}
    infs = []
    for x in xrange(infDags.length()):
        infPath = infDags[x].fullPathName()
        infId = int(skinFn.indexForInfluenceObject(infDags[x]))
        infIds[infId] = x
        infs.append(infPath)

    # get the MPlug for the weightList and weights attributes
    wlPlug = skinFn.findPlug('weightList')
    wPlug = skinFn.findPlug('weights')
    wlAttr = wlPlug.attribute()
    wAttr = wPlug.attribute()
    wInfIds = OpenMaya.MIntArray()

    # the weights are stored in dictionary, the key is the vertId, 
    # the value is another dictionary whose key is the influence id and 
    # value is the weight for that influence
    weights = {}
    for vId in xrange(wlPlug.numElements()):
        vWeights = {}
        # tell the weights attribute which vertex id it represents
        wPlug.selectAncestorLogicalIndex(vId, wlAttr)

        # get the indice of all non-zero weights for this vert
        wPlug.getExistingArrayAttributeIndices(wInfIds)

        # create a copy of the current wPlug
        infPlug = OpenMaya.MPlug(wPlug)
        for infId in wInfIds:
            # tell the infPlug it represents the current influence id
            infPlug.selectAncestorLogicalIndex(infId, wAttr)

            # add this influence and its weight to this verts weights
            try:
                vWeights[infIds[infId]] = infPlug.asDouble()
            except KeyError:
                # assumes a removed influence
                pass
        weights['weightList[' + str(vId) + '].weights'] = vWeights

    return weights


'''



'''
