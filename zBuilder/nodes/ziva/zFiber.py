from zBuilder.nodes import ZivaBaseNode
import maya.cmds as mc
import maya.mel as mm
import zBuilder.zMaya as mz
import logging

logger = logging.getLogger(__name__)


class FiberNode(ZivaBaseNode):
    TYPE = 'zFiber'
    MAP_LIST = ['weightList[0].weights', 'endPoints']

    def __init__(self, *args, **kwargs):
        ZivaBaseNode.__init__(self, *args, **kwargs)
