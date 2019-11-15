import maya.cmds as mc
import maya.mel as mm
import zBuilder.zMaya as mz

from zBuilder.nodes import Ziva
import logging

logger = logging.getLogger(__name__)


class ClothNode(Ziva):
    """ This node for storing information related to zCloth.
    """
    type = 'zCloth'
    """ The type of node. """

    def build(self, *args, **kwargs):
        """ Builds the zCloth in maya scene.

        Args:
            attr_filter (dict):  Attribute filter on what attributes to get.
                dictionary is key value where key is node type and value is
                list of attributes to use.

                tmp = {'zSolver':['substeps']}
            name_filter (string OR list): name of zCloth objects to work with.  Defaults to all avaliable
            
        """
        attr_filter = kwargs.get('attr_filter', list())
        name_filter = kwargs.get('name_filter', list())

        scene_items = self.builder.bundle.get_scene_items(type_filter='zCloth',
                                                          name_filter=name_filter)

        # checking if the node is the first one in list.  If it is I get
        # all the zCloth and build them together for speed reasons.
        # This feels kinda sloppy to me.

        if self is scene_items[0]:
            build_multiple(scene_items, attr_filter=attr_filter)

            # set the attributes.  This needs to run even if there are no zCloth to build. This case happens during during a copy paste.
            # any time you 'build' when the zCloth is in scene.
            for item in scene_items:
                item.set_maya_attrs(attr_filter=attr_filter)


def build_multiple(scene_items, attr_filter=None):
    """ Each node can deal with it's own building.  Though, with zCLoth it is much
    faster to build them all at once with one command instead of looping
    through them.  This function builds all the zCloth at once.

    Args:
        scene_items (list of obj): List of zBuilder objects to work with.
        attr_filter (dict):  Attribute filter on what attributes to get.
            dictionary is key value where key is node type and value is
            list of attributes to use.

            tmp = {'zSolver':['substeps']}
    """
    sel = mc.ls(sl=True)
    # cull none buildable------------------------------------------------------
    culled = mz.cull_creation_nodes(scene_items)

    # build all cloth at once--------------------------------------------------
    results = None
    if culled['meshes']:
        Ziva.check_meshes(culled['meshes'])
        mc.select(culled['meshes'], r=True)
        results = mm.eval('ziva -c')

    # rename zCloth------------------------------------------------------------
    if results:
        results = mc.ls(results, type='zCloth')
        for new, name, item in zip(results, culled['names'], culled['scene_items']):
            item.mobject = new
            mc.rename(new, name)

    mc.select(sel)
