from zBuilder.nodes import ZivaBaseNode
import zBuilder.zMaya as mz

import maya.cmds as mc
import maya.mel as mm
import logging

logger = logging.getLogger(__name__)


class LineOfActionNode(ZivaBaseNode):
    TYPE = 'zLineOfAction'

    def __init__(self, *args, **kwargs):
        self._zFiber = None

        ZivaBaseNode.__init__(self, *args, **kwargs)

    @property
    def fiber(self):
        return self._zFiber

    @fiber.setter
    def fiber(self, fiber):
        self._zFiber = fiber

    def populate(self, *args, **kwargs):
        super(LineOfActionNode, self).populate(*args, **kwargs)

        self.fiber = mz.get_lineOfAction_fiber(self.get_scene_name())

    def apply(self, *args, **kwargs):

        """

        Args:
            *args:
            **kwargs:

        Returns:

        """
        attr_filter = kwargs.get('attr_filter', list())
        permissive = kwargs.get('permissive', True)

        name = self.get_scene_name()
        association = self.association
        fiber = self.fiber
        if mc.objExists(association[0]) and mc.objExists(fiber):
            if not mc.objExists(name):
                mc.select(fiber, association[0])
                results_ = mm.eval('ziva -lineOfAction')
                clt = mc.ls(results_, type='zLineOfAction')[0]
                self.mobject = clt
                mc.rename(clt, name)

            else:
                self.mobject = name
                mc.rename(name, self.name)

        else:
            mc.warning(association[
                           0] + ' mesh does not exists in scene, skippings line of action')

        # set maya attributes
        self.set_maya_attrs(attr_filter=attr_filter)

