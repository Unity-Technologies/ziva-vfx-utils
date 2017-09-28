import logging
import maya.cmds as mc
import maya.mel as mm

from zBuilder.nodes.deformerBase import DeformerBaseNode

logger = logging.getLogger(__name__)


class ZRelaxerNode(DeformerBaseNode):
    TYPE = 'zRelaxer'
    MAP_LIST = ['weightList[0].weights']

    def apply(self, *args, **kwargs):
        interp_maps = kwargs.get('interp_maps', 'auto')
        attr_filter = kwargs.get('attr_filter', None)

        name = self.name
        if not mc.objExists(name):
            mc.select(self.association, r=True)
            mm.eval('zRelaxer -name {}'.format(name))

        self.set_maya_attrs(attr_filter=attr_filter)
        self.set_maya_weights(interp_maps=interp_maps)

