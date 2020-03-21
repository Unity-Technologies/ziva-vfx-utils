import logging
from maya import cmds
from zBuilder.nodes.deformer import Deformer

logger = logging.getLogger(__name__)


class DeltaMush(Deformer):
    type = 'deltaMush'
    MAP_LIST = ['weightList[0].weights']

    def build(self, *args, **kwargs):
        interp_maps = kwargs.get('interp_maps', 'auto')
        attr_filter = kwargs.get('attr_filter', None)

        name = self.get_scene_name()
        if not cmds.objExists(name):
            cmds.select(self.nice_association, r=True)
            delta_mush = cmds.deltaMush(name=name)

        self.set_maya_attrs(attr_filter=attr_filter)
        self.set_maya_weights(interp_maps=interp_maps)
