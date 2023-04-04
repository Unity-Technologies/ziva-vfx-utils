import logging

from maya import cmds
from zBuilder.nodes.deformer import Deformer

logger = logging.getLogger(__name__)


class DeltaMush(Deformer):
    type = 'deltaMush'
    MAP_LIST = ['weightList[0].weights']

    def do_build(self, *args, **kwargs):
        interp_maps = kwargs.get('interp_maps', 'auto')

        if cmds.objExists(self.association[0]):
            if not cmds.objExists(self.name):
                cmds.select(self.nice_association, r=True)
                cmds.deltaMush(name=self.name)

            self.set_maya_attrs()
            self.set_maya_weights(interp_maps=interp_maps)
        else:
            logger.warning('Missing items from scene: check for existence of {}'.format(
                self.association[0]))
