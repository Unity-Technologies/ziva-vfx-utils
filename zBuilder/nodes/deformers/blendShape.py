import logging
import maya.cmds as mc
from zBuilder.nodes.deformer import Deformer
import zBuilder.zMaya as mz

logger = logging.getLogger(__name__)


class BlendShapeNode(Deformer):
    type = 'blendShape'
    MAP_LIST = ['inputTarget[*].inputTargetGroup[*].targetWeights',
                'inputTarget[*].baseWeights']
    EXTEND_ATTR_LIST = ['origin']

    def __init__(self, *args, **kwargs):
        self._target = None

        Deformer.__init__(self, *args, **kwargs)

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

        if not mc.objExists(name):
            mc.select(self.target, r=True)
            mc.select(self.association, add=True)

            results = mc.blendShape()
            self.mobject = results[0]
        else:
            self.mobject = name

        self.set_maya_attrs(attr_filter=attr_filter)
        self.set_maya_weights(interp_maps=interp_maps)

    def populate(self, maya_node=None):
        super(BlendShapeNode, self).populate(maya_node=maya_node)
        self.target = get_target(self.name)

        num_weights = mc.blendShape(self.get_scene_name(), q=True, wc=True)
        attr_list = ['weight['+str(i)+']' for i in range(0, num_weights)]
        attrs = mz.build_attr_key_values(self.get_scene_name(), attr_list)
        self.attrs.update(attrs)

    @property
    def target(self):
        return self._target.split('|')[-1]

    @target.setter
    def target(self, target_mesh):
        self._target = mc.ls(target_mesh, long=True)[0]

    @property
    def long_target(self):
        return self._target


def get_target(blend_shape):
    target = mc.blendShape(blend_shape, q=True, t=True)
    return target

