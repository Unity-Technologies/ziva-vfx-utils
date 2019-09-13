import maya.cmds as mc
import maya.mel as mm

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

        solver_name = self.get_scene_name()

        if not mc.objExists(solver_name):
            results = mm.eval('ziva -s')

            # we need to rename the transform before the shape or maya may
            # rename shape after.
            solverTransform = mc.ls(results, type='zSolverTransform')[0]
            st = self.builder.bundle.get_scene_items(type_filter='zSolverTransform')[0]
            mc.rename(solverTransform, st.name)
            solverTransform_child = mc.listRelatives(st.name, c=True)[0]
            mc.rename(solverTransform_child, solver_name.split('|')[-1])
            self.mobject = solver_name.split('|')[-1]

            st.mobject = st.name
        else:
            new_name = mc.rename(solver_name, self.name)
            self.mobject = new_name

        self.set_maya_attrs(attr_filter=attr_filter)
