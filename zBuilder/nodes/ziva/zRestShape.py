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
        Ziva.__init__(self, *args, **kwargs)

    def build(self, *args, **kwargs):
        """ Builds the node in maya.  mean to be overwritten.
        """
        pass
