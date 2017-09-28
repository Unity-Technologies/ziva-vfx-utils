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

    def set_fiber(self, fiber):
        self._zFiber = fiber

    def get_fiber(self, long_name=False):
        return self._zFiber

    def populate(self, *args, **kwargs):
        """

        Returns:
            object:
        """

        # logger.info('retrieving {}'.format(args))
        selection = mz.parse_args_for_selection(args)

        self.name = selection[0]
        self.type = mz.get_type(selection[0])
        self.set_attr_list(mz.build_attr_list(selection[0]))
        self.populate_attrs(selection[0])
        self.mobject = selection[0]

        mesh = mz.get_association(selection[0])
        self.association = mesh
        self.set_fiber(mz.get_lineOfAction_fiber(self.get_scene_name()))

    def apply(self, *args, **kwargs):

        """

        Args:
            *args:
            **kwargs:

        Returns:

        """
        attr_filter = kwargs.get('attr_filter', None)
        name = self.get_scene_name()
        association = self.association
        fiber = self.get_fiber()
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

