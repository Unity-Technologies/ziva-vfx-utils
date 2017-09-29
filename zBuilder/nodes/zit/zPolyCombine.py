import logging
import maya.cmds as mc
import maya.mel as mm
import zBuilder.zMaya as mz

from zBuilder.nodes.deformerBase import DeformerBaseNode

logger = logging.getLogger(__name__)


class ZPolyCombineNode(DeformerBaseNode):
    TYPE = 'zPolyCombine'
    MAP_LIST = []

    def __init__(self, *args, **kwargs):
        self._result_name = None

        DeformerBaseNode.__init__(self, *args, **kwargs)

    def populate(self, *args, **kwargs):
        super(ZPolyCombineNode, self).populate(*args, **kwargs)

        self.result_name = self.get_result_name(self.name)

    def apply(self, *args, **kwargs):
        interp_maps = kwargs.get('interp_maps', 'auto')
        attr_filter = kwargs.get('attr_filter', None)

        name = self.get_scene_name()
        if not mc.objExists(name):
            mc.select(self.association, r=True)
            results = mm.eval('zPolyCombine')
            zpc = mc.ls(results, type='zPolyCombine')
            new_name = mc.rename(zpc, name)

            transform = mc.ls(results, type='transform')[0]
            shape = mc.listRelatives(transform)[0]
            mc.rename(transform, self.result_name)
            mc.rename(shape, self.result_name+'Shape')

            self.mobject = new_name
        else:
            self.mobject = name

        self.set_maya_attrs(attr_filter=attr_filter)
        self.set_maya_weights(interp_maps=interp_maps)

    @staticmethod
    def get_meshes(node):
        meshes = mc.listConnections('{}.inputPoly'.format(node))
        return meshes

    @staticmethod
    def get_result_name(node):
        output = mc.listConnections('{}.output'.format(node))[0]
        return output

    @property
    def result_name(self):
        return self._result_name

    @result_name.setter
    def result_name(self, name):
        self._result_name = name


