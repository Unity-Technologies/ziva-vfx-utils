from maya import cmds
from .zivaBase import Ziva


class SolverTransformNode(Ziva):
    """ This node for storing information related to zSolverTransform.
    """
    type = 'zSolverTransform'

    def do_build(self, *args, **kwargs):
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

        if not cmds.objExists(self.name):
            if not permissive:
                raise Exception('zSolverTransform not in scene.  please check.')

        self.set_maya_attrs(attr_filter=attr_filter)
