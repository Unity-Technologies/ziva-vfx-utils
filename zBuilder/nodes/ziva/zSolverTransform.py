from maya import cmds
from maya import mel

import zBuilder.zMaya as mz
from zBuilder.nodes import Ziva
import logging

logger = logging.getLogger(__name__)


class SolverTransformNode(Ziva):
    """ This node for storing information related to zSolverTransform.
    """
    type = 'zSolverTransform'
    """ The type of node. """

    def build(self, *args, **kwargs):
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

        if not cmds.objExists(solver_name):
            if not permissive:
                raise Exception('zSolverTransform not in scene.  please check.')

        else:
            mz.safe_rename(solver_name, self.name)

        self.set_maya_attrs(attr_filter=attr_filter)
