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

    def apply(self, *args, **kwargs):
        """

        Args:
            *args:
            **kwargs:

        Returns:

        """
        attr_filter = kwargs.get('attr_filter', None)

        bone_name = self.get_scene_name()

        if not mc.objExists(solver_name):
            # print 'building solver: ',solverName
            results = mm.eval('ziva -s')
            solver = mc.ls(results, type='zSolver')[0]
            mc.rename(solver, solver_name)
            self.set_mobject(solver_name)

        else:
            new_name = mc.rename(self.get_scene_name(), self.get_name())
            self.set_mobject(new_name)

        self.set_maya_attrs(attr_filter=attr_filter)
