import logging
import maya.cmds as mc
from zBuilder.nodes.deformerBase import DeformerBaseNode

logger = logging.getLogger(__name__)


class BlendShapeNode(DeformerBaseNode):
    type = 'blendShape'
    MAP_LIST = ['inputTarget[0].inputTargetGroup[0].targetWeights']
    EXTEND_ATTR_LIST = ['origin']

    def __init__(self, *args, **kwargs):
        self._target = None

        DeformerBaseNode.__init__(self, *args, **kwargs)

    def build(self, *args, **kwargs):
        interp_maps = kwargs.get('interp_maps', 'auto')
        attr_filter = kwargs.get('attr_filter', None)

        name = self.get_scene_name()
        if not mc.objExists(name):
            mc.select(self.target, r=True)
            mc.select(self.association, add=True)

            results = mc.blendShape()
            self.mobject = results
        else:
            self.mobject = name

        self.set_maya_attrs(attr_filter=attr_filter)
        self.set_maya_weights(interp_maps=interp_maps)

    def populate(self, *args, **kwargs):
        super(BlendShapeNode, self).populate(*args, **kwargs)
        self.target = get_target(self.name)

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

