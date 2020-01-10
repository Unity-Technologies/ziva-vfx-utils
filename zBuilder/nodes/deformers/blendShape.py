import logging
from maya import cmds
import zBuilder.zMaya as mz

from zBuilder.nodes.deformer import Deformer

logger = logging.getLogger(__name__)


class BlendShape(Deformer):
    type = 'blendShape'
    MAP_LIST = ['inputTarget[*].inputTargetGroup[*].targetWeights', 'inputTarget[*].baseWeights']
    EXTEND_ATTR_LIST = ['origin']

    def __init__(self, parent=None, builder=None):
        super(BlendShape, self).__init__(parent=parent, builder=builder)
        self._target = None

    def get_map_meshes(self):
        """
        This is the mesh associated with each map in obj.MAP_LIST.  Typically
        it seems to coincide with mesh store in get_association.  Sometimes
        it deviates, so you can override this method to define your own
        list of meshes against the map list.

        For blendShapes we don't know how many maps so we are generating this
        list based on length of maps.

        Returns:
            list(): of long mesh names.
        """
        return [self.association[0] for i in range(len(self.get_map_names()))]

    def build(self, *args, **kwargs):
        interp_maps = kwargs.get('interp_maps', 'auto')
        attr_filter = kwargs.get('attr_filter', None)

        name = self.get_scene_name()

        if not cmds.objExists(name):
            cmds.select(self.target, r=True)
            cmds.select(self.association, add=True)

            results = cmds.blendShape(name=self.name)

        self.set_maya_attrs(attr_filter=attr_filter)
        self.set_maya_weights(interp_maps=interp_maps)

    def populate(self, maya_node=None):
        super(BlendShape, self).populate(maya_node=maya_node)
        self.target = get_target(self.name)

        name = self.get_scene_name()

        num_weights = cmds.blendShape(name, q=True, wc=True)
        attr_list = ['weight[' + str(i) + ']' for i in range(0, num_weights)]
        attrs = mz.build_attr_key_values(name, attr_list)
        self.attrs.update(attrs)

    @property
    def target(self):
        return self._target.split('|')[-1]

    @target.setter
    def target(self, target_mesh):
        self._target = cmds.ls(target_mesh, long=True)[0]

    @property
    def long_target(self):
        return self._target


def get_target(blend_shape):
    target = cmds.blendShape(blend_shape, q=True, t=True)
    return target
