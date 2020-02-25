from zBuilder.nodes import Ziva
import zBuilder.zMaya as mz

from maya import cmds
from maya import mel
import logging

logger = logging.getLogger(__name__)


class LineOfActionNode(Ziva):
    """ This node for storing information related to zLineOfAction.
    """
    type = 'zLineOfAction'
    """ The type of node. """

    def __init__(self, parent=None, builder=None):
        super(LineOfActionNode, self).__init__(parent=parent, builder=builder)
        self.fiber = None

    def spawn_parameters(self):
        return {}

    def populate(self, maya_node=None):
        """ This populates the node given a selection.

        Args:
            maya_node: Maya node to populate with.
        """
        super(LineOfActionNode, self).populate(maya_node=maya_node)

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

        loas = []
        for i, loa in enumerate(self.long_association):
            if cmds.objExists(loa):
                loas.append(self.long_association[i])
            elif cmds.objExists(self.association[i]):
                loas.append(self.association[i])
            else:
                cmds.warning(loa + ' curve does not exists in scene, skippings line of action')

        if cmds.objExists(self.fiber):
            # check if the zFiber has a lineOf Action on it, if it does that is
            # what we want to use.  If not lets create a new one
            existing = cmds.listConnections(self.fiber, type='zLineOfAction')
            if not existing:
                if loas:
                    cmds.select(self.fiber, loas)
                    results_ = mel.eval('ziva -lineOfAction')
                    clt = cmds.ls(results_, type='zLineOfAction')[0]
                    cmds.rename(clt, self.name)
        else:
            cmds.warning(self.fiber + ' fiber does not exists in scene, skippings line of action')

        # set maya attributes
        self.set_maya_attrs(attr_filter=attr_filter)
