from maya import cmds
from ..deformer import Deformer


class DeltaMush(Deformer):
    type = 'deltaMush'
    MAP_LIST = ['weightList[0].weights']

    def build(self, *args, **kwargs):
        interp_maps = kwargs.get('interp_maps', 'auto')
        attr_filter = kwargs.get('attr_filter', None)

        if not cmds.objExists(self.name):
            cmds.select(self.nice_association, r=True)
            cmds.deltaMush(name=self.name)

        self.set_maya_attrs(attr_filter=attr_filter)
        self.set_maya_weights(interp_maps=interp_maps)
