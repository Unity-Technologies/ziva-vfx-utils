from maya import cmds
from maya.api import OpenMaya as om2
from maya.api import OpenMayaAnim as oma2
from zBuilder.utils.mayaUtils import get_mobject
from ..dg_node import DGNode


class SkinCluster(DGNode):
    """ The base node for the node functionality of all nodes
    """
    type = 'skinCluster'
    TYPES = []

    # List of attributes to exclude with a string_replace
    SEARCH_EXCLUDE = ['_class', 'attrs', '_builder_type', 'type', 'weights']

    # List of maya attributes to add to attribute list when capturing
    EXTEND_ATTR_LIST = list()

    def __init__(self, parent=None, builder=None):
        super(SkinCluster, self).__init__(parent=parent, builder=builder)
        self.influences = list()
        self.weights = dict()

    def populate(self, maya_node=None):
        """ This extends ZivaBase.populate().
        Adds parent and child storage.

        Args:
            maya_node: Maya node to populate with.
        """
        super(SkinCluster, self).populate(maya_node=maya_node)
        self.weights = get_weights(self.name)
        self.influences = get_influences(self.name)
        self.association = get_associations(self.name)

    def build(self, *args, **kwargs):
        attr_filter = kwargs.get('attr_filter', None)

        name = self.name
        if not cmds.objExists(name):
            cmds.select(self.influences, self.association, r=True)
            skin_cluster = cmds.skinCluster(tsb=True, n=name)

        self.set_maya_attrs(attr_filter=attr_filter)
        apply_weights(self.name, self.association, self.influences, self.weights)


def get_associations(skin_cluster):
    return cmds.skinCluster(skin_cluster, g=True, q=True)


def get_influences(skin_cluster):
    return cmds.skinCluster(skin_cluster, q=True, influence=True)


def apply_weights(skin_cluster, mesh, influences, weights):
    # unlock influences used by skincluster
    for inf in influences:
        cmds.setAttr('%s.liw' % inf, 0)

    # normalize needs turned off for the prune to work
    skinNorm = cmds.getAttr('%s.normalizeWeights' % skin_cluster)
    if skinNorm != 0:
        cmds.setAttr('%s.normalizeWeights' % skin_cluster, 0)
    cmds.skinPercent(skin_cluster, mesh, nrm=False, prw=100)

    # restore normalize setting
    if skinNorm != 0:
        cmds.setAttr('%s.normalizeWeights' % skin_cluster, skinNorm)

    # set the weights
    for attr, vals in weights.items():
        for idx, val in vals.items():
            # print cluster,attr,idx,val
            cmds.setAttr('%s.%s[%s]' % (skin_cluster, attr, str(idx)), val)


def get_weights(skin_cluster):
    # get the MDagPath for all influence
    clusterNode = get_mobject(skin_cluster)
    skinFn = oma2.MFnSkinCluster(clusterNode)
    dag_path_array = skinFn.influenceObjects()

    # create a dictionary whose key is the MPlug indice id and
    # whose value is the influence list id
    infIds = {}
    infs = []
    for idx, cur_path in enumerate(dag_path_array):
        infId = int(skinFn.indexForInfluenceObject(cur_path))
        infIds[infId] = idx
        infs.append(cur_path.fullPathName())

    # get the MPlug for the weightList and weights attributes
    wlPlug = skinFn.findPlug('weightList', False)
    wPlug = skinFn.findPlug('weights', False)
    wlAttr = wlPlug.attribute()
    wAttr = wPlug.attribute()

    # the weights are stored in dictionary, the key is the vertId,
    # the value is another dictionary whose key is the influence id and
    # value is the weight for that influence
    weights = {}
    for vId in range(wlPlug.numElements()):
        vWeights = {}
        # tell the weights attribute which vertex id it represents
        wPlug.selectAncestorLogicalIndex(vId, wlAttr)

        # get the indice of all non-zero weights for this vert
        wInfIds = wPlug.getExistingArrayAttributeIndices()

        # create a copy of the current wPlug
        infPlug = om2.MPlug(wPlug)
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
