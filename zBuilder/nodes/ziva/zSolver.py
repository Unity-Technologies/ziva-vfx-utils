import maya.cmds as mc
import maya.mel as mm

from zBuilder.nodes import ZivaBaseNode
import logging

logger = logging.getLogger(__name__)


class SolverNode(ZivaBaseNode):
    TYPE = 'zSolver'

    def __init__(self, *args, **kwargs):
        ZivaBaseNode.__init__(self, *args, **kwargs)

    def apply(self, *args, **kwargs):
        """

        Args:
            *args:
            **kwargs:

        Returns:

        """
        attr_filter = kwargs.get('attr_filter', list())
        permissive = kwargs.get('permissive', True)

        solver_name = self.get_scene_name()

        if not mc.objExists(solver_name):
            results = mm.eval('ziva -s')
            solver = mc.ls(results, type='zSolver')[0]
            mc.rename(solver, solver_name.split('|')[-1])
            self.mobject = solver_name

        else:
            new_name = mc.rename(self.get_scene_name(), self.name)
            self.mobject = new_name

        self.set_maya_attrs(attr_filter=attr_filter)
