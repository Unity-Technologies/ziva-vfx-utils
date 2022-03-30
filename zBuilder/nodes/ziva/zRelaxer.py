from maya import cmds
from zBuilder.mayaUtils import safe_rename
from ..deformer import Deformer


class ZRelaxerNode(Deformer):
    type = 'zRelaxer'
    MAP_LIST = ['weightList[0].weights']

    def build(self, *args, **kwargs):
        interp_maps = kwargs.get('interp_maps', 'auto')
        attr_filter = kwargs.get('attr_filter', None)

        if not cmds.objExists(self.name):
            cmds.select(self.association, r=True)
            results = cmds.zRelaxer()
            safe_rename(results[0], self.name)

        self.check_parameter_name()

        self.set_maya_attrs(attr_filter=attr_filter)
        self.set_maya_weights(interp_maps=interp_maps)
