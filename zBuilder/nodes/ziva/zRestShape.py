from zBuilder.nodes import Ziva
import maya.cmds as mc
import maya.mel as mm
import zBuilder.zMaya as mz
import logging

logger = logging.getLogger(__name__)


class RestShapeNode(Ziva):
    """ This node for storing information related to zFibers.
    """
    type = 'zRestShape'
    """ The type of node. """

    def __init__(self, *args, **kwargs):
        self.targets = None
        Ziva.__init__(self, *args, **kwargs)

    def populate(self, maya_node=None):
        """ This populates the node given a selection.

        Args:
            maya_node: Maya node to populate with.
        """
        super(RestShapeNode, self).populate(maya_node=maya_node)

        self.targets = mc.listConnections(self.name + '.target')
        self.targets = mc.ls(self.targets, long=True)  # find long names
        self.tissue_name = get_rest_shape_tissue(self.name)

    def build(self, *args, **kwargs):
        """ Builds the node in maya.  mean to be overwritten.
        """
        pass


def get_rest_shape_tissue(rest_shape):
    tet = mc.listConnections('{}.iGeo'.format(rest_shape))[0]
    tissue = mm.eval('zQuery -type "zTissue" {}'.format(tet))
    return tissue[0]
