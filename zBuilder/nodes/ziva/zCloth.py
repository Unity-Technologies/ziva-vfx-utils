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

    def __init__(self, *args, **kwargs):
        Ziva.__init__(self, *args, **kwargs)

    def build(self, *args, **kwargs):
        """ Builds the zCloth in maya scene.

        Args:
            attr_filter (dict):  Attribute filter on what attributes to get.
                dictionary is key value where key is node type and value is
                list of attributes to use.

                tmp = {'zSolver':['substeps']}
        """
        attr_filter = kwargs.get('attr_filter', list())

        name = self.name

        if not mc.objExists(name):

            Ziva.check_meshes(self.association)

            mc.select(self.association)
            results = mm.eval('ziva -c')
            cloth = mc.ls(results, type='zCloth')[0]
            mc.rename(cloth, name)
            self.mobject = name
        else:
            new_name = mc.rename(self.get_scene_name(), self.name)
            self.mobject = new_name

        self.set_maya_attrs(attr_filter=attr_filter)
