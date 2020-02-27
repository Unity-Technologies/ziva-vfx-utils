import logging
from maya import cmds
from maya import mel

import zBuilder.zMaya as mz
from zBuilder.nodes.deformer import Deformer

logger = logging.getLogger(__name__)


class ZRelaxerNode(Deformer):
    type = 'zRelaxer'
    MAP_LIST = ['weightList[0].weights']

    def build(self, *args, **kwargs):
        interp_maps = kwargs.get('interp_maps', 'auto')
        attr_filter = kwargs.get('attr_filter', None)

        name = self.get_scene_name()
        if not cmds.objExists(name):
            cmds.select(self.association, r=True)
            results = mel.eval('zRelaxer')
            mz.safe_rename(results[0], self.name)

        self.set_maya_attrs(attr_filter=attr_filter)
        self.set_maya_weights(interp_maps=interp_maps)
