import logging
import maya.cmds as mc
from zBuilder.nodes import DeformerBaseNode

logger = logging.getLogger(__name__)


class DeltaMushNode(DeformerBaseNode):
    TYPE = 'deltaMush'
    MAP_LIST = ['weightList[0].weights']

    def apply(self, *args, **kwargs):
        interp_maps = kwargs.get('interp_maps', 'auto')
        attr_filter = kwargs.get('attr_filter', None)

        name = self.get_name()
        if not mc.objExists(name):
            mc.select(self.get_association(), r=True)
            mc.deltaMush(name=name)

        self.set_maya_attrs(attr_filter=attr_filter)
        self.set_maya_weights(interp_maps=interp_maps)

