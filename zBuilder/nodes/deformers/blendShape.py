from maya import cmds
from zBuilder.mayaUtils import get_short_name, build_attr_key_values
from ..deformer import Deformer


class BlendShape(Deformer):
    type = 'blendShape'
    MAP_LIST = ['inputTarget[*].inputTargetGroup[*].targetWeights', 'inputTarget[*].baseWeights']
    EXTEND_ATTR_LIST = ['origin']

    def __init__(self, parent=None, builder=None):
        super(BlendShape, self).__init__(parent=parent, builder=builder)
        self._target = None

    def get_map_meshes(self):
        """ This is the mesh associated with each map in obj.MAP_LIST.
        Typically it seems to coincide with mesh store in get_association.
        Sometimes it deviates, so you can override this method 
        to define your own list of meshes against the map list.

        For blendShapes we don't know how many maps,
        so we are generating this list based on length of maps.

        Returns:
            list(): of long mesh names.
        """
        return [self.association[0]] * len(self.construct_map_names())

    def build(self, *args, **kwargs):
        interp_maps = kwargs.get('interp_maps', 'auto')
        attr_filter = kwargs.get('attr_filter', None)
        if not cmds.objExists(self.name):
            cmds.select(self.target, r=True)
            cmds.select(self.association, add=True)
            cmds.blendShape(name=self.name)

        self.set_maya_attrs(attr_filter=attr_filter)
        self.set_maya_weights(interp_maps=interp_maps)

    def populate(self, maya_node=None):
        super(BlendShape, self).populate(maya_node=maya_node)
        self.target = cmds.blendShape(self.name, q=True, t=True)
        num_weights = cmds.blendShape(self.name, q=True, wc=True)
        attr_list = ['weight[' + str(i) + ']' for i in range(0, num_weights)]
        attrs = build_attr_key_values(self.name, attr_list)
        self.attrs.update(attrs)

    @property
    def target(self):
        return get_short_name(self._target)

    @target.setter
    def target(self, target_mesh):
        self._target = cmds.ls(target_mesh, long=True)[0]

    @property
    def long_target(self):
        return self._target
