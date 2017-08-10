import maya.cmds as mc
import maya.mel as mm
import zBuilder.zMaya as mz

from zBuilder.nodes.base import BaseNode
# import zBuilder.nodes.base as base
import logging

logger = logging.getLogger(__name__)


class BoneNode(BaseNode):
    def __init__(self, *args, **kwargs):
        BaseNode.__init__(self, *args, **kwargs)

    # TODO consistency with data classes.  use create() instead of retrieve()??
    def retrieve_from_scene(self, *args, **kwargs):
        """

        Returns:
            object:
        """
        logger.info('retrieving {}'.format(args))
        selection = mz.parse_args_for_selection(args)

        self.set_name(selection[0])
        self.set_type(mz.get_type(selection[0]))
        self.set_attr_list(mz.build_attr_list(selection[0]))
        self.populate_attrs(selection[0])
        self.set_mobject(selection[0])

        mesh = mz.get_association(selection[0])
        self.set_association(mesh)


    def apply(self, *args, **kwargs):
        """

        Args:
            *args:
            **kwargs:

        Returns:

        """
        attr_filter = kwargs.get('attr_filter', None)

        bone_name = self.get_scene_name()

        if not mc.objExists(solver_name):
            # print 'building solver: ',solverName
            results = mm.eval('ziva -s')
            solver = mc.ls(results, type='zSolver')[0]
            mc.rename(solver, solver_name)
            self.set_mobject(solver_name)

        else:
            new_name = mc.rename(self.get_scene_name(), self.get_name())
            self.set_mobject(new_name)

        self.set_maya_attrs(attr_filter=attr_filter)


def apply_multiple(b_nodes, attr_filter=None):
    """
    Each node can deal with it's own building.  Though, with zBones it is much
    faster to build them all at once with one command instead of looping
    through them.  This function builds all the zBones at once.

    Args:
        attr_filter (obj):

    Returns:

    """
    sel = mc.ls(sl=True)
    # cull none buildable-------------------------------------------------------
    culled = mz.cull_creation_nodes(b_nodes)

    # check mesh quality--------------------------------------------------------
    mz.check_mesh_quality(culled['meshes'])

    # build bones all at once---------------------------------------------------
    results = None
    if culled['meshes']:
        mc.select(culled['meshes'], r=True)
        results = mm.eval('ziva -b')

    # rename zBones-------------------------------------------------------------
    if results:
        results = mc.ls(results, type='zBone')
        for new, name, b_node in zip(results[1::2], culled['names'], culled['b_nodes']):
            b_node.set_mobject(new)
            mc.rename(new, name)

    # set the attributes
    for b_node in b_nodes:
        b_node.set_maya_attrs(attr_filter=attr_filter)

    mc.select(sel)