from maya import cmds
from zBuilder.utils.mayaUtils import get_short_name, safe_rename
from .zivaBase import Ziva


class SolverNode(Ziva):
    """ This node is for storing information related to zSolver.
    """
    type = 'zSolver'

    def do_build(self, *args, **kwargs):
        """ Builds the zSolver in maya scene.

        Args:
            permissive (bool): Pass on errors. Defaults to ``True``
        """
        solver_name = self.name
        if not cmds.objExists(solver_name):
            results = cmds.ziva(s=True)

            # we need to rename the transform before the shape or maya may
            # rename shape after.
            solverTransform = cmds.ls(results, type='zSolverTransform')[0]
            st = self.builder.get_scene_items(type_filter='zSolverTransform')[0]
            new_name = safe_rename(solverTransform, st.name)
            st.name = new_name
            solverTransform_child = cmds.listRelatives(st.name, c=True, fullPath=True)[0]
            safe_rename(solverTransform_child, get_short_name(solver_name))
        else:
            new_name = safe_rename(solver_name, self.name)

        cmds.ziva(new_name, defaultSolver=True)
        self.set_maya_attrs()
