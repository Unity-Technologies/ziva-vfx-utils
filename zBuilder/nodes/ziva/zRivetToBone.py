from zBuilder.nodes import Ziva
import logging
import zBuilder.zMaya as mz
from maya import cmds
from maya import mel

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
        scene_name = self.get_scene_name()
        curve_shape = cmds.deformer(scene_name, q=True, g=True)[0]
        self.curve = cmds.listRelatives(curve_shape, p=True, f=True)[0]
        self.cv_indices = cmds.getAttr(scene_name + '.cvIndices')

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
            return self._curve.split('|')[-1]
        else:
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

        else:
            message = 'Missing items from scene: check for existance of {} and {}'.format(crv, bone)
            if permissive:
                logger.warning(message)
            else:
                raise Exception(message)

        self.set_maya_attrs(attr_filter=attr_filter)


def is_cv_connected_to_rivet(crv, cv):
    shape = cmds.listRelatives(crv, c=True, fullPath=True)[0]
    hist = cmds.listHistory(shape)
    rivets = cmds.ls(hist, type='zRivetToBone')
    for rivet in rivets:
        if cmds.getAttr(rivet + '.cvIndices') == cv:
            return True
    return False
