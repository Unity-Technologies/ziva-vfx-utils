import maya.cmds as mc
import maya.mel as mm
import zBuilder.zMaya as mz

from zBuilder.nodes import ZivaBaseNode
import logging

logger = logging.getLogger(__name__)


class AttachmentNode(ZivaBaseNode):
    TYPE = 'zAttachment'
    MAP_LIST = ['weightList[0].weights', 'weightList[1].weights']

    def __init__(self, *args, **kwargs):
        ZivaBaseNode.__init__(self, *args, **kwargs)

