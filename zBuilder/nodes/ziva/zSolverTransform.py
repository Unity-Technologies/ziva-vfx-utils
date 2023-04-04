from maya import cmds
from .zivaBase import Ziva


class SolverTransformNode(Ziva):
    """ This node for storing information related to zSolverTransform.
    """
    type = 'zSolverTransform'

    def do_build(self, *args, **kwargs):
        """ Builds the zSolverTransform in maya scene.

        Args:
            permissive (bool): Pass on errors. Defaults to ``True``
        """
        permissive = kwargs.get('permissive', True)

        if not cmds.objExists(self.name):
            if not permissive:
                raise Exception('zSolverTransform not in scene.  please check.')

        self.set_maya_attrs()
