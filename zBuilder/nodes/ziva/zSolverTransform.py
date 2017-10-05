import maya.cmds as mc
import maya.cmds as mc
import maya.mel as mm

from zBuilder.nodes import ZivaBaseNode
import logging

logger = logging.getLogger(__name__)


class SolverTransformNode(ZivaBaseNode):
    """ This node for storing information related to zSolverTransform.
    """
    type = 'zSolverTransform'
    """ The type of node. """

    def __init__(self, *args, **kwargs):
        ZivaBaseNode.__init__(self, *args, **kwargs)

    def apply(self, *args, **kwargs):
        """ Builds the zSolverTransform in maya scene.

        Args:
            attr_filter (dict):  Attribute filter on what attributes to get.
                dictionary is key value where key is node type and value is
                list of attributes to use.

                tmp = {'zSolver':['substeps']}
            permissive (bool): Pass on errors. Defaults to ``True``
        """
        attr_filter = kwargs.get('attr_filter', list())
        permissive = kwargs.get('permissive', True)

        solver_name = self.get_scene_name()

        if not mc.objExists(solver_name):
            results = mm.eval('ziva -s')
            solver = mc.ls(results, type='zSolverTransform')[0]
            mc.rename(solver, solver_name)
            self.mobject = solver_name

        else:
            new_name = mc.rename(self.get_scene_name(), self.name)
            self.mobject = new_name

        self.set_maya_attrs(attr_filter=attr_filter)

        # ----------------------------------------------------------------------
        # turn off solver to speed up build
        mc.setAttr(solver_name + '.enable', 0)
