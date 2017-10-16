from zBuilder.parameters import ZivaBaseParameter
import zBuilder.zMaya as mz

import maya.cmds as mc
import maya.mel as mm
import logging

logger = logging.getLogger(__name__)


class LineOfActionNode(ZivaBaseParameter):
    """ This node for storing information related to zLineOfAction.
    """
    type = 'zLineOfAction'
    """ The type of node. """

    def __init__(self, *args, **kwargs):
        self.fiber = None

        ZivaBaseParameter.__init__(self, *args, **kwargs)

    def populate(self, *args, **kwargs):
        """ This extends ZivaBase.populate()

        Adds fiber storage.

        Args:
            *args: Maya node to populate with.
        """
        super(LineOfActionNode, self).populate(*args, **kwargs)

        self.fiber = mz.get_lineOfAction_fiber(self.get_scene_name())

    def build(self, *args, **kwargs):
        """ Builds the Line of Actions in maya scene.

        Args:
            attr_filter (dict):  Attribute filter on what attributes to get.
                dictionary is key value where key is node type and value is
                list of attributes to use.

                tmp = {'zSolver':['substeps']}
            permissive (bool): Pass on errors. Defaults to ``True``
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

