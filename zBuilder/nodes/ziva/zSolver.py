import logging

from maya import cmds
from maya import mel
from zBuilder.mayaUtils import get_short_name
from zBuilder.nodes import Ziva
import zBuilder.zMaya as mz

logger = logging.getLogger(__name__)


class SolverNode(Ziva):
    """ This node is for storing information related to zSolver.
    """
    type = 'zSolver'
    """ The type of node. """
    def build(self, *args, **kwargs):
        """ Builds the zSolver in maya scene.

        Args:
            attr_filter (dict):  Attribute filter on what attributes to get.
                dictionary is key value where key is node type and value is
                list of attributes to use.

                tmp = {'zSolver':['substeps']}
            permissive (bool): Pass on errors. Defaults to ``True``
        """
        attr_filter = kwargs.get('attr_filter', list())

        solver_name = self.name

        if not cmds.objExists(solver_name):
            results = mel.eval('ziva -s')

            # we need to rename the transform before the shape or maya may
            # rename shape after.
            solverTransform = cmds.ls(results, type='zSolverTransform')[0]
            st = self.builder.get_scene_items(type_filter='zSolverTransform')[0]
            new_name = mz.safe_rename(solverTransform, st.name)
            st.name = new_name
            solverTransform_child = cmds.listRelatives(st.name, c=True, fullPath=True)[0]
            mz.safe_rename(solverTransform_child, get_short_name(solver_name))
        else:
            new_name = mz.safe_rename(solver_name, self.name)

        cmds.ziva(new_name, defaultSolver=True)

        self.set_maya_attrs(attr_filter=attr_filter)
