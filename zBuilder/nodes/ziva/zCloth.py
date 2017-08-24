import maya.cmds as mc
import maya.mel as mm
import zBuilder.zMaya as mz

from zBuilder.nodes import ZivaBaseNode
import logging

logger = logging.getLogger(__name__)


class ClothNode(ZivaBaseNode):
    TYPE = 'zCloth'

    def __init__(self, *args, **kwargs):
        ZivaBaseNode.__init__(self, *args, **kwargs)

    def apply(self, *args, **kwargs):
        """

        Args:
            *args:
            **kwargs:

        Returns:

        """
        attr_filter = kwargs.get('attr_filter', None)

        name = self.get_scene_name()

        if not mc.objExists(name):
            mc.select(self.get_association())
            results = mm.eval('ziva -c')
            cloth = mc.ls(results, type='zCloth')[0]
            mc.rename(cloth, name)
            self.set_mobject(name)
        else:
            new_name = mc.rename(self.get_scene_name(), self.get_name())
            self.set_mobject(new_name)

        self.set_maya_attrs(attr_filter=attr_filter)
