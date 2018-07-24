from zBuilder.nodes import Ziva
import zBuilder.zMaya as mz

import maya.cmds as mc
import maya.mel as mm
import logging

logger = logging.getLogger(__name__)


class FieldAdaptorNode(Ziva):
    """ This node for storing information related to fields.
    """
    type = 'zFieldAdaptor'
    """ The type of node. """

    def __init__(self, *args, **kwargs):
        self.output_bodies = []
        Ziva.__init__(self, *args, **kwargs)

    def populate(self, maya_node=None):
        """ This populates the node given a selection.

        Args:
            maya_node: Maya node to populate with.
        """
        super(FieldAdaptorNode, self).populate(maya_node=maya_node)
        self.input_field = get_field(self.get_scene_name())
        self.output_bodies = get_bodies(self.get_scene_name())


    @property
    def input_field(self):
        """ Name of parameter corresponding to maya node name.  Setting this
        property will check for long name and store that.  self.input_field still
        returns short name, self.long_field_name returns the stored long name.
        """
        if self._input_field:
            return self._input_field.split('|')[-1]
        else:
            return None

    @input_field.setter
    def input_field(self, name):
        if mc.ls(name, long=True):
            self._input_field = mc.ls(name, long=True)[0]
        else:
            self._input_field = name

    @property
    def long_field_name(self):
        """ Long name of parameter corresponding to long name of maya node.
        This property is not settable.  To set it use self.input_field.
        """
        return self._input_field

    def build(self, *args, **kwargs):
        """ Builds the zFieldAdaptor in maya scene.

        This keeps track of inputs and outputs of zFieldadaptor (field nodes and
        zCloth, zTissue respecitvely) and re-connects them.

        Args:
            attr_filter (dict):  Attribute filter on what attributes to get.
                dictionary is key value where key is node type and value is
                list of attributes to use.

                tmp = {'zSolver':['substeps']}
            permissive (bool): Pass on errors. Defaults to ``True``
        """
        attr_filter = kwargs.get('attr_filter', list())
        permissive = kwargs.get('permissive', True)

        name = self.name
        
        if not mc.objExists(name):
            # the field adaptor node does not exist in scene, lets create it 
            # then hook it up.
            results_ = mc.createNode('zFieldAdaptor',name=name)
            clt = mc.ls(results_, type='zFieldAdaptor')[0]
            self.mobject = clt
            mc.rename(clt, name)
            
        # check if field exists and if it does hook it up
        if mc.objExists(self.input_field):
            if not mc.isConnected('{}.message'.format(self.input_field), '{}.field'.format(name)):
                mc.connectAttr('{}.message'.format(self.input_field), '{}.field'.format(name))

        # check if bodies exist, if they do hook them up
        for output_body in self.output_bodies:
            # find exisiting connections on the bodies to adaptors as we
            # can have multiple adaptors connected to a single body.  In this 
            # case we need to hook it up to first availbale slot.
            exisiting = mc.listConnections('{}.fields'.format(output_body))
            exisiting_size = 0
            if exisiting:
                exisiting_size = len(exisiting)
            else:
                exisiting = []
            
            #if not mc.listConnections('{}.outField'.format(name)):    
            if name not in exisiting:
                mc.connectAttr('{}.outField'.format(name),'{}.fields[{}]'.format(output_body,str(exisiting_size)))

        # set maya attributes
        self.set_maya_attrs(attr_filter=attr_filter)

def get_bodies(zFieldAdaptor):
    """This gets the output bodies associated with a zFieldAdaptor.

    Args:
        zNode (string): [description]
    """
    if mc.objExists('{}.outField'.format(zFieldAdaptor)):
        body = mc.listConnections('{}.outField'.format(zFieldAdaptor))

    convert_to_long = mc.ls(body,l=True)
    return convert_to_long



def get_field(zFieldAdaptor):
    """This gets the field associated with a zFieldAdaptor.

    Args:
        zNode (string): [description]
    """
    if mc.objExists('{}.field'.format(zFieldAdaptor)):
        field = mc.listConnections('{}.field'.format(zFieldAdaptor))[0]

    convert_to_long = mc.ls(field,l=True)[0]
    return convert_to_long
