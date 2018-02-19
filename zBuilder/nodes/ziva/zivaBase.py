import zBuilder.zMaya as mz
import maya.cmds as mc
import maya.mel as mm

from zBuilder.nodes.deformer import Deformer
import logging

logger = logging.getLogger(__name__)


class Ziva(Deformer):
    """Base node for Ziva type nodes.

    extended from base to deal with maps and meshes and storing the solver.
    """
    EXTEND_ATTR_LIST = list()

    try:
        mc.loadPlugin('ziva', qt=True)
    except RuntimeError:
        pass

    def __init__(self,  parent=None, maya_node=None, builder=None, deserialize=None):
        self.solver = None
        Deformer.__init__(self, maya_node=maya_node,
                          builder=builder,
                          deserialize=deserialize,
                          parent=parent)

    def populate(self, maya_node=None):
        """

        Args:
            *args:
            **kwargs:

        Raises:
            NotImplementedError: if not implemented

        """
        raise NotImplementedError

    def populate(self, maya_node=None):
        """ This populates the node given a selection.

        Args:
            maya_node: Maya node to populate with.
        """

        maya_node = mz.check_maya_node(maya_node)

        self.name = maya_node
        self.type = mc.objectType(maya_node)
        attr_list = mz.build_attr_list(maya_node)
        if self.EXTEND_ATTR_LIST:
            attr_list.extend(self.EXTEND_ATTR_LIST)
        attrs = mz.build_attr_key_values(maya_node, attr_list)
        self.attrs = attrs
        self.mobject = maya_node

        mesh = mz.get_association(maya_node)
        self.association = mesh

        solver = mm.eval('zQuery -t zSolver {}'.format(self.name))
        if solver:
            self.solver = solver[0]




