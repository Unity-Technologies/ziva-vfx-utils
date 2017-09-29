import logging
import maya.cmds as mc
import maya.mel as mm

from zBuilder.nodes.deformerBase import DeformerBaseNode

logger = logging.getLogger(__name__)


class ZWrapNode(DeformerBaseNode):
    TYPE = 'zWrap'

    def __init__(self, *args, **kwargs):
        self._cage = None

        DeformerBaseNode.__init__(self, *args, **kwargs)

    def apply(self, *args, **kwargs):
        interp_maps = kwargs.get('interp_maps', 'auto')
        attr_filter = kwargs.get('attr_filter', None)

        name = self.get_scene_name()
        if not mc.objExists(name):
            mc.select(self.cage, r=True)
            mc.select(self.association, add=True)
            results = mm.eval('zWrap')[0]
            tmp = mc.rename(results, name)
            self.mobject = tmp
        else:
            self.mobject = name

        self.set_maya_attrs(attr_filter=attr_filter)
        self.set_maya_weights(interp_maps=interp_maps)

    def populate(self, *args, **kwargs):
        super(ZWrapNode, self).populate(*args, **kwargs)

        cage_mesh = get_cage(self.name)
        self.cage = cage_mesh

    @property
    def cage(self):
        return self._cage.split('|')[-1]

    @cage.setter
    def cage(self, cage_mesh):
        self._cage = mc.ls(cage_mesh, long=True)[0]

    @property
    def long_cage(self):
        return self._cage


def get_cage(wrap_node):
    cage = mc.listConnections('{}.influenceMesh'.format(wrap_node))[0]
    return cage
