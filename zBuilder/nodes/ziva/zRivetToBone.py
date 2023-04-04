import logging

from maya import cmds
from zBuilder.utils.mayaUtils import get_short_name, safe_rename
from .zivaBase import Ziva

logger = logging.getLogger(__name__)


class RivetToBoneNode(Ziva):
    """ This node for storing information related to zRivetToBone.
    """
    type = 'zRivetToBone'

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
        self.rivet_locator = cmds.listConnections('{}.segments'.format(self.name))[0]
        parent = cmds.listRelatives(self.rivet_locator, p=True)
        self.rivet_locator_parent = parent[0] if parent else []

    @property
    def long_curve_name(self):
        """ Long name of parameter corresponding to long name of maya node.
        This property is not settable.  To set it use self.name.
        """
        return self._curve

    @property
    def curve(self):
        """ Name of parameter corresponding to maya node name.
        Setting this property will check for long name and store that.
        self.name still returns short name, self.long_name returns the stored long name.
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

    def do_build(self, *args, **kwargs):
        """ Builds the zRivetToBone in maya scene.

        Kwargs:
            permissive (bool): Pass on errors. Defaults to ``True``
        """
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
                results = cmds.zRivetToBone()
                self.name = safe_rename(results[0], self.name)
                # restore name of rivet locator
                if self.rivet_locator:
                    self.rivet_locator = safe_rename(results[1], self.rivet_locator)

                # parent locator to group if group node already exists
                if self.rivet_locator_parent and cmds.objExists(self.rivet_locator_parent):
                    cmds.parent(self.rivet_locator, self.rivet_locator_parent)

        else:
            message = 'Missing items from scene: check for existance of {} and {}'.format(crv, bone)
            if permissive:
                logger.warning(message)
            else:
                raise Exception(message)

        self.set_maya_attrs()


def is_cv_connected_to_rivet(crv, cv):
    shape = cmds.listRelatives(crv, c=True, fullPath=True)[0]
    hist = cmds.listHistory(shape)
    rivets = cmds.ls(hist, type='zRivetToBone')
    for rivet in rivets:
        if cmds.getAttr(rivet + '.cvIndices') == cv:
            return True
    return False
