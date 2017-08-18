import maya.cmds as mc
import maya.mel as mm
import zBuilder.zMaya as mz

from zBuilder.nodes import ZivaBaseNode
import logging

logger = logging.getLogger(__name__)


class BoneNode(ZivaBaseNode):
    TYPE = 'zBone'

    def __init__(self, *args, **kwargs):
        ZivaBaseNode.__init__(self, *args, **kwargs)


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
        for new, name, b_node in zip(results, culled['names'], culled['b_nodes']):
            b_node.set_mobject(new)
            mc.rename(new, name)

    # set the attributes
    for b_node in b_nodes:
        b_node.set_maya_attrs(attr_filter=attr_filter)

    mc.select(sel)
