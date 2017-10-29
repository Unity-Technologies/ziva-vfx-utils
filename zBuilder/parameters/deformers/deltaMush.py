import logging
import maya.cmds as mc
from zBuilder.parameters.deformer import Deformer

logger = logging.getLogger(__name__)


class DeltaMushNode(Deformer):
    type = 'deltaMush'
    MAP_LIST = ['weightList[0].weights']

    def build(self, *args, **kwargs):
        interp_maps = kwargs.get('interp_maps', 'auto')
        attr_filter = kwargs.get('attr_filter', None)

        name = self.get_scene_name()
        if not mc.objExists(name):
            mc.select(self.association, r=True)
            delta_mush = mc.deltaMush(name=name)
            self.mobject = delta_mush[0]
        else:
            self.mobject = name

        self.set_maya_attrs(attr_filter=attr_filter)
        self.set_maya_weights(interp_maps=interp_maps)
