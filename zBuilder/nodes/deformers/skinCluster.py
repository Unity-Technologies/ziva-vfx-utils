from zBuilder.nodes.dg_node import DGNode
import maya.cmds as mc
import maya.OpenMaya as OpenMaya
import maya.OpenMayaAnim as OpenMayaAnim


class SkinCluster(DGNode):
    """ The base node for the node functionality of all nodes
    """
    type = 'skinCluster'
    TYPES = []
    """ The type of node. """

    SEARCH_EXCLUDE = ['_class', 'attrs', '_builder_type', 'type', 'weights']
    """ List of attributes to exclude with a string_replace"""
    EXTEND_ATTR_LIST = list()
    """ List of maya attributes to add to attribute list when capturing."""

    def __init__(self, *args, **kwargs):
        DGNode.__init__(self, *args, **kwargs)
        self.influences = list()
        self.weights = dict()

    def populate(self, maya_node=None):
        """ This extends ZivaBase.populate()

        Adds parent and child storage.

        Args:
            maya_node: Maya node to populate with.
        """
        super(SkinCluster, self).populate(maya_node=maya_node)

        self.weights = get_weights(self.name)
        self.influences = get_influences(self.name)
        self.association = get_associations(self.name)

    def build(self, *args, **kwargs):
        interp_maps = kwargs.get('interp_maps', 'auto')
        attr_filter = kwargs.get('attr_filter', None)

        name = self.name
        if not mc.objExists(name):
            mc.select(self.influences, self.association, r=True)
            skin_cluster = mc.skinCluster(tsb=True, n=name)
            self.mobject = skin_cluster[0]
        else:
            self.mobject = name

        self.set_maya_attrs(attr_filter=attr_filter)
        apply_weights(self.name, self.association, self.influences, self.weights)


def get_associations(skin_cluster):
    return mc.skinCluster(skin_cluster, g=True, q=True)


def get_influences(skin_cluster):
    return mc.skinCluster(skin_cluster, q=True, influence=True)


def apply_weights(skin_cluster, mesh, influences, weights):
    # unlock influences used by skincluster
    for inf in influences:
        mc.setAttr('%s.liw' % inf, 0)

    # normalize needs turned off for the prune to work
    skinNorm = mc.getAttr('%s.normalizeWeights' % skin_cluster)
    if skinNorm != 0:
        mc.setAttr('%s.normalizeWeights' % skin_cluster, 0)
    mc.skinPercent(skin_cluster, mesh, nrm=False, prw=100)

    # restore normalize setting
    if skinNorm != 0:
        mc.setAttr('%s.normalizeWeights' % skin_cluster, skinNorm)

    # set the weights
    for attr, vals in weights.items():
        for idx, val in vals.items():
            # print cluster,attr,idx,val
            mc.setAttr('%s.%s[%s]' % (skin_cluster, attr, str(idx)), val)


def get_weights(skin_cluster):
    # get the MFnSkinCluster for skinCluster
    selList = OpenMaya.MSelectionList()
    selList.add(skin_cluster)
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
