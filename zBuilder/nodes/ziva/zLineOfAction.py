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
        self.fiber_item = None

    def spawn_parameters(self):
        return {}

    def populate(self, maya_node=None):
        """ This populates the node given a selection.

        Args:
            maya_node: Maya node to populate with.
        """
        super(LineOfActionNode, self).populate(maya_node=maya_node)

        fiber_name = mz.get_lineOfAction_fiber(self.get_scene_name())

        scene_item = self.builder.get_scene_items(name_filter=fiber_name)
        if scene_item:
            self.fiber_item = scene_item[0]

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
        for loa in self.nice_association:
            if cmds.objExists(loa):
                loas.append(loa)
            else:
                cmds.warning(loa + ' curve does not exists in scene')

        if not loas:
            cmds.warning('No curves found, skipping line of action')
            return

        if cmds.objExists(self.fiber_item.name):
            # check if the zFiber has a lineOf Action on it, if it does that is
            # what we want to use.  If not lets create a new one
            existing = cmds.listConnections(self.fiber_item.name, type='zLineOfAction')
            if not existing:
                cmds.select(self.fiber_item.name, loas)
                results_ = mel.eval('ziva -lineOfAction')
                clt = cmds.ls(results_, type='zLineOfAction')[0]
                self.name = mz.safe_rename(clt, self.name)
        else:
            cmds.warning(self.fiber_item.name + ' fiber does not exists in scene, skipping line of action')

        # set maya attributes
        self.set_maya_attrs(attr_filter=attr_filter)
