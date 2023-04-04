from maya import cmds
from zBuilder.utils.mayaUtils import get_short_name, safe_rename
from .zivaBase import Ziva


class FieldAdaptorNode(Ziva):
    """ This node for storing information related to fields.
    """
    type = 'zFieldAdaptor'

    def __init__(self, parent=None, builder=None):
        super(FieldAdaptorNode, self).__init__(parent=parent, builder=builder)
        self.output_bodies = []

    def populate(self, maya_node=None):
        """ This populates the node given a selection.

        Args:
            maya_node: Maya node to populate with.
        """
        super(FieldAdaptorNode, self).populate(maya_node=maya_node)

        if cmds.objExists('{}.field'.format(self.name)):
            field = cmds.listConnections('{}.field'.format(self.name))[0]
            self.input_field = cmds.ls(field, l=True)[0]

        if cmds.objExists('{}.outField'.format(self.name)):
            body = cmds.listConnections('{}.outField'.format(self.name))
            self.output_bodies = cmds.ls(body, l=True)

    @property
    def input_field(self):
        """ Name of parameter corresponding to maya node name.  Setting this
        property will check for long name and store that.  self.input_field still
        returns short name, self.long_field_name returns the stored long name.
        """
        if self._input_field:
            return get_short_name(self._input_field)
        return None

    @input_field.setter
    def input_field(self, name):
        if cmds.ls(name, long=True):
            self._input_field = cmds.ls(name, long=True)[0]
        else:
            self._input_field = name

    @property
    def long_field_name(self):
        """ Long name of parameter corresponding to long name of maya node.
        This property is not settable.  To set it use self.input_field.
        """
        return self._input_field

    def do_build(self, *args, **kwargs):
        """ Builds the zFieldAdaptor in maya scene.

        This keeps track of inputs and outputs of zFieldadaptor (field nodes and
        zCloth, zTissue respecitvely) and re-connects them.

        Args:
            permissive (bool): Pass on errors. Defaults to ``True``
        """
        name = self.name

        if not cmds.objExists(name):
            # the field adaptor node does not exist in scene, lets create it
            # then hook it up.
            results_ = cmds.createNode('zFieldAdaptor', name=name)
            clt = cmds.ls(results_, type='zFieldAdaptor')[0]
            safe_rename(clt, name)

        # check if field exists and if it does hook it up
        if cmds.objExists(self.input_field):
            if not cmds.isConnected('{}.message'.format(self.input_field), '{}.field'.format(name)):
                cmds.connectAttr('{}.message'.format(self.input_field), '{}.field'.format(name))

        # check if bodies exist, if they do hook them up
        for output_body in self.output_bodies:
            # find exisiting connections on the bodies to adaptors as we
            # can have multiple adaptors connected to a single body.  In this
            # case we need to hook it up to first availbale slot.
            exisiting = cmds.listConnections('{}.fields'.format(output_body))
            exisiting_size = 0
            if exisiting:
                exisiting_size = len(exisiting)
            else:
                exisiting = []

            #if not cmds.listConnections('{}.outField'.format(name)):
            if name not in exisiting:
                cmds.connectAttr('{}.outField'.format(name),
                                 '{}.fields[{}]'.format(output_body, str(exisiting_size)))

        # set maya attributes
        self.set_maya_attrs()
