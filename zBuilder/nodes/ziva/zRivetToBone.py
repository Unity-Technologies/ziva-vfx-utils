import logging

from maya import cmds
from maya import mel
from zBuilder.mayaUtils import get_short_name
from zBuilder.nodes import Ziva
import zBuilder.zMaya as mz

logger = logging.getLogger(__name__)


class RivetToBoneNode(Ziva):
    """ This node for storing information related to zRivetToBone.
    """
    type = 'zRivetToBone'
    """ The type of node. """
    def __init__(self, parent=None, builder=None):
        super(RivetToBoneNode, self).__init__(parent=parent, builder=builder)
        self.cv_indices = []

    def populate(self, maya_node=None):
        """ This populates the node given a selection.

        Args:
            maya_node: Maya node to populate with.
        """
        super(RivetToBoneNode, self).populate(maya_node=maya_node)
        curve_shape = cmds.deformer(self.name, q=True, g=True)[0]
        self.curve = cmds.listRelatives(curve_shape, p=True, f=True)[0]
        self.cv_indices = cmds.getAttr(self.name + '.cvIndices')
        self.rivet_locator = get_rivet_locator(self.name)
        self.rivet_locator_parent = get_rivet_locator_parent(self.rivet_locator)

    @property
    def long_curve_name(self):
        """ Long name of parameter corresponding to long name of maya node.
        This property is not settable.  To set it use self.name.
        """
        return self._curve

    @property
    def curve(self):
        """ Name of parameter corresponding to maya node name.  Setting this
        property will check for long name and store that.  self.name still
        returns short name, self.long_name returns the stored long name.
        """
        if self._curve:
            return get_short_name(self._curve)
        return None

    @curve.setter
    def curve(self, curve_name):
        if cmds.ls(curve_name, long=True):
            self._curve = cmds.ls(curve_name, long=True)[0]
        else:
            self._curve = curve_name

    def build(self, *args, **kwargs):
        """ Builds the zRivetToBone in maya scene.

        Kwargs:
            attr_filter (dict):  Attribute filter on what attributes to get.
                dictionary is key value where key is node type and value is
                list of attributes to use.

                tmp = {'zSolver':['substeps']}

            permissive (bool): Pass on errors. Defaults to ``True``
        """
        attr_filter = kwargs.get('attr_filter', list())
        permissive = kwargs.get('permissive', True)

        crv = self.long_curve_name
        if not cmds.objExists(crv):
            crv = self.curve
        cv_index = self.cv_indices
        bone = self.nice_association[0]

        cmds.select(cl=True)
        if cmds.objExists(crv) and cmds.objExists(bone):
            if not is_cv_connected_to_rivet(crv, cv_index):
                for i in cv_index:
                    cmds.select('{}.cv[{}]'.format(crv, i), add=True)
                cmds.select(bone, add=True)
                results = mel.eval('zRivetToBone')
                self.name = mz.safe_rename(results[0], self.name)
                # restore name of rivet locator
                self.rivet_locator = mz.safe_rename(results[1], self.rivet_locator)
                # parent locator to group if group node already exists
                if cmds.objExists(self.rivet_locator_parent):
                    cmds.parent(self.rivet_locator, self.rivet_locator_parent)

        else:
            message = 'Missing items from scene: check for existance of {} and {}'.format(crv, bone)
            if permissive:
                logger.warning(message)
            else:
                raise Exception(message)

        self.set_maya_attrs(attr_filter=attr_filter)


def get_rivet_locator_parent(rivet_to_bone_locator):
    """queries a rivet to bone and returns the locators transform

    Args:
        rivet_to_bone_locator (string): the rivet to bone node to query

    Returns:
        string: Parent node of rivet locator or empty list if None
    """
    parent = cmds.listRelatives(rivet_to_bone_locator, p=True)
    if parent:
        return parent[0]
    return []


def get_rivet_locator(rivet_to_bone):
    """queries a rivet to bone and returns the locators transform

    Args:
        rivet_to_bone (string): the rivet to bone node to query

    Returns:
        string: transform of the rivet to bone locator
    """
    locator_shape = cmds.listConnections('{}.segments'.format(rivet_to_bone))
    return locator_shape[0]


def is_cv_connected_to_rivet(crv, cv):
    shape = cmds.listRelatives(crv, c=True, fullPath=True)[0]
    hist = cmds.listHistory(shape)
    rivets = cmds.ls(hist, type='zRivetToBone')
    for rivet in rivets:
        if cmds.getAttr(rivet + '.cvIndices') == cv:
            return True
    return False
