from maya import cmds
from maya import mel

from zBuilder.nodes import Ziva
import logging

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
        permissive = kwargs.get('permissive', True)

        solver_name = self.get_scene_name(long_name=True)
        if not cmds.objExists(solver_name):
            solver_name = self.get_scene_name()

        if not cmds.objExists(solver_name):
            results = mel.eval('ziva -s')

            # we need to rename the transform before the shape or maya may
            # rename shape after.
            solverTransform = cmds.ls(results, type='zSolverTransform')[0]
            st = self.builder.bundle.get_scene_items(type_filter='zSolverTransform')[0]
            cmds.rename(solverTransform, st.name)
            solverTransform_child = cmds.listRelatives(st.name, c=True)[0]
            cmds.rename(solverTransform_child, solver_name.split('|')[-1])
        else:
            cmds.rename(solver_name, self.name)

        self.set_maya_attrs(attr_filter=attr_filter)
