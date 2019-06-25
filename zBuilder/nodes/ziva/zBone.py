import maya.cmds as mc
import maya.mel as mm
import zBuilder.zMaya as mz

from zBuilder.nodes import Ziva
import logging

logger = logging.getLogger(__name__)


class BoneNode(Ziva):
    """ This node for storing information related to zBones.
    """
    type = 'zBone'
    """ The type of node. """

    def __init__(self, *args, **kwargs):
        Ziva.__init__(self, *args, **kwargs)

    def build(self, *args, **kwargs):
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

        parameters = self.builder.bundle.get_scene_items(type_filter='zBone',
                                                         name_filter=name_filter)

        # checking if the node is the first one in list.  If it is I get
        # all the zBones and build them together for speed reasons.
        # This feels kinda sloppy to me.

        if self == parameters[0]:
            build_multiple(parameters, attr_filter=attr_filter, permissive=permissive)


def build_multiple(parameters, attr_filter=None, permissive=False):
    """ Each node can deal with it's own building.  Though, with zBones it is much
    faster to build them all at once with one command instead of looping
    through them.  This function builds all the zBones at once.

    Args:
        permissive (bool):
        parameters:
        attr_filter (obj):

    Returns:

    """
    sel = mc.ls(sl=True)
    # cull none buildable------------------------------------------------------
    culled = mz.cull_creation_nodes(parameters)

    # build bones all at once--------------------------------------------------
    results = None
    if culled['meshes']:
        Ziva.check_meshes(culled['meshes'])
        mc.select(culled['meshes'], r=True)
        results = mm.eval('ziva -b')

    # rename zBones------------------------------------------------------------
    if results:
        results = mc.ls(results, type='zBone')
        for new, name, parameter in zip(results, culled['names'], culled['parameters']):
            parameter.mobject = new
            mc.rename(new, name)

    # set the attributes
    for parameter in parameters:
        parameter.set_maya_attrs(attr_filter=attr_filter)

    mc.select(sel)
