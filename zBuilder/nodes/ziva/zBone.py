import maya.cmds as mc
import maya.mel as mm
import zBuilder.zMaya as mz

from zBuilder.nodes import ZivaBaseNode
import logging

logger = logging.getLogger(__name__)


class BoneNode(ZivaBaseNode):
    """ This node for storing information related to zBones.
    """
    TYPE = 'zBone'
    """ The type of node. """

    def __init__(self, *args, **kwargs):
        ZivaBaseNode.__init__(self, *args, **kwargs)

    def apply(self, *args, **kwargs):
        """ Builds the zBones in maya scene.

        Args:
            attr_filter (dict):  Attribute filter on what attributes to get.
                dictionary is key value where key is node type and value is
                list of attributes to use.

                tmp = {'zSolver':['substeps']}
            permissive (bool): Pass on errors. Defaults to ``True``

        """
        attr_filter = kwargs.get('attr_filter', list())
        name_filter = kwargs.get('name_filter', list())
        permissive = kwargs.get('permissive', True)
        check_meshes = kwargs.get('check_meshes', True)

        b_nodes = self._setup.get_nodes(type_filter='zBone',
                                        name_filter=name_filter)

        # checking if the node is the first one in list.  If it is I get
        # all the zBones and build them together for speed reasons.
        # This feels kinda sloppy to me.

        if self == b_nodes[0]:
            apply_multiple(b_nodes, attr_filter=attr_filter,
                           permissive=permissive, check_meshes=check_meshes)


def apply_multiple(b_nodes, attr_filter=None, permissive=False, check_meshes=True):
    """ Each node can deal with it's own building.  Though, with zBones it is much
    faster to build them all at once with one command instead of looping
    through them.  This function builds all the zBones at once.

    Args:
        permissive (bool):
        b_nodes:
        attr_filter (obj):

    Returns:

    """
    sel = mc.ls(sl=True)
    # cull none buildable-------------------------------------------------------
    culled = mz.cull_creation_nodes(b_nodes)

    # check mesh quality--------------------------------------------------------
    if check_meshes:
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
            b_node.mobject = new
            mc.rename(new, name)

    # set the attributes
    for b_node in b_nodes:
        b_node.set_maya_attrs(attr_filter=attr_filter)

    mc.select(sel)
