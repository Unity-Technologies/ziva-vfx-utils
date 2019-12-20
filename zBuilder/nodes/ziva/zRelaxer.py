import logging
import maya.cmds as mc
import maya.mel as mm

from zBuilder.nodes.deformer import Deformer

logger = logging.getLogger(__name__)


class ZRelaxerNode(Deformer):
    type = 'zRelaxer'
    MAP_LIST = ['weightList[0].weights']

    def build(self, *args, **kwargs):
        interp_maps = kwargs.get('interp_maps', 'auto')
        attr_filter = kwargs.get('attr_filter', None)

        name = self.get_scene_name()
        if not mc.objExists(name):
            mc.select(self.association, r=True)
            results = mm.eval('zRelaxer')
            mc.rename(results[0], self.name)

        self.set_maya_attrs(attr_filter=attr_filter)
        self.set_maya_weights(interp_maps=interp_maps)
