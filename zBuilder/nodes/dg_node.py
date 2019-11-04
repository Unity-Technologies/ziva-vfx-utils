import logging
import inspect
import copy

import maya.OpenMaya as om
import maya.cmds as mc
import maya.mel as mm

import zBuilder.zMaya as mz
from zBuilder.nodes.base import Base
from zBuilder.nodes.base import serialize_object

logger = logging.getLogger(__name__)


class DGNode(Base):
    """ The base node for the node functionality of all nodes

    Args:
        builder (object, optional): The builder object for reference.

    Attributes:
        :rtype: :func:`type` (str): type of parameter.  Tied with maya node type.
        attrs (dict): A place for the maya attributes dictionary.

    """
    type = None
    TYPES = None
    """ Types of maya nodes this parameter is aware of.  Only needed 
        if parameter can deal with multiple types.  Else leave at None """
    MAP_LIST = []
    """ List of maya node attribute names that represent the paintable map. """
    SEARCH_EXCLUDE = ['_class', 'attrs', '_builder_type', 'type']
    """ A list of attribute names in __dict__ to
            exclude from the string_replace method. """
    EXTEND_ATTR_LIST = list()
    """ List of maya node attribute names to add
            to the auto generated attribute list to include."""

    def __init__(self, parent=None, builder=None):
        super(DGNode, self).__init__(parent=parent, builder=builder)

        self.attrs = {}
        self._association = []
        self._mobject_handle = None

    def __str__(self):
        if self.name:
            name = self.name
            output = ''
            output += '= {} <{} {}> ==================================\n'.format(
                name, self.__class__.__module__, self.__class__.__name__)
            for key in self.__dict__:
                try:
                    output += '\t{} - {}\n'.format(key, self.__dict__[key].__repr__())
                except:
                    output += '\t{} - {}\n'.format(key, self.__dict__[key])

            return output
        return '<%s.%s>' % (self.__class__.__module__, self.__class__.__name__)

    def __repr__(self):
        output = '{}("{}")'.format(self.__class__.__name__, self.name)
        return output

    def __deepcopy__(self, memo):
        # Some attributes cannot be deepcopied so define a listy of attributes
        # to ignore.
        non_copyable_attrs = ('_mobject_handle', 'depends_on')

        result = type(self)()

        for k, v in self.__dict__.items():
            # skip over attributes defined as non-copyable in non_copyable_attrs
            if k not in non_copyable_attrs:
                setattr(result, k, copy.deepcopy(v, memo))

        return result

    def serialize(self):
        """  Makes node serializable.

        This replaces an mObject with the name of the object in scene to make it
        serializable for writing out to json.  Then it loops through keys in
        dict and saves out a temp dict of items that can be serializable and
        returns that temp dict for json writing purposes.

        Replaces .mobject mobject with a string name before serilization.
        Afterwords it converts it back to an mObject.

        Returns:
            dict: of serializable items
        """
        # convert mObjectHandle to name of maya object (str)
        self._mobject_handle = mz.get_name_from_m_object(self.mobject)

        output = serialize_object(self)

        self.mobject = self._mobject_handle

        return output

    def deserialize(self, json_data):
        """ Deserializes a node with given dict.

        Assigns a dictionary to __dict__.  Adds an mObject to the .mobject if 
        applicable.

        Args:
            json_data(dict): The given dict.
        """
        self.__dict__ = json_data

        # Finding the mObject in scene if it exists
        self.mobject = self._mobject_handle

    def populate(self, maya_node=None):
        """ Populates the node with the info from the passed maya node in args.

        This is deals with basic stuff including attributes.  For other things it
        is meant to be overridden in inherited node.

        Args:
            maya_node (str): The maya node to populate parameter with.

        """

        # selection = mz.parse_maya_node_for_selection(maya_node)
        maya_node = mz.check_maya_node(maya_node)
        self.name = maya_node
        self.type = mc.objectType(maya_node)
        attr_list = mz.build_attr_list(maya_node)
        if self.EXTEND_ATTR_LIST:
            attr_list.extend(self.EXTEND_ATTR_LIST)
        attrs = mz.build_attr_key_values(maya_node, attr_list)
        self.attrs = attrs
        self.mobject = maya_node

    def build(self, *args, **kwargs):
        """ Builds the node in maya.  meant to be overwritten.
        """
        raise NotImplementedError

    @property
    def association(self):
        """ associations of node.
        """
        tmp = []
        for item in self._association:
            tmp.append(item.split('|')[-1])
        return tmp

    @association.setter
    def association(self, association):
        self._association = mc.ls(association, long=True)

    @property
    def long_association(self):
        """ Long names of associations.
        """
        return self._association

    def compare(self):
        """ Compares populated parameter with that which is in maya scene.

        Returns:
            prints out items that are different.
        """
        name = self.name

        attr_list = self.attrs.keys()
        if mc.objExists(name):
            if attr_list:
                for attr in attr_list:
                    scene_val = mc.getAttr(name + '.' + attr)
                    obj_val = self.attrs[attr]['value']
                    if scene_val != obj_val:
                        print('DIFF:', name + '.' + attr, '\tobject value:', obj_val, '\tscene value:', scene_val)

    def get_scene_name(self, long_name=False):
        """This checks stored mObject and gets name of maya object in scene.  If no
        mObject it returns parameter name.

        Args:
            long_name (bool): Return the fullpath or not. Defaults to False.

        Returns:
            (str) Name of maya object.
        """
        name = self.long_name

        if self.mobject:
            name = mz.get_name_from_m_object(self.mobject, long_name=True)

        if not long_name:
            name = name.split('|')[-1]

        return name

    def set_maya_attrs(self, attr_filter=None):
        """Given a Builder node this set the attributes of the object in the maya
        scene.  It first does a mObject check to see if it has been tracked, if
        it has it uses that instead of stored name.

        Args:
            attr_filter (dict):  Attribute filter on what attributes to set.
                dictionary is key value where key is node type and value is
                list of attributes to use.

                af = {'zSolver':['substeps']}

        Returns:
            nothing.
        """
        scene_name = self.get_scene_name()

        type_ = self.type
        node_attrs = self.attrs.keys()
        if attr_filter:
            if attr_filter.get(type_, None):
                node_attrs = list(set(node_attrs).intersection(attr_filter[type_]))

        for attr in node_attrs:
            if self.attrs[attr]['type'] == 'doubleArray':
                if mc.objExists('{}.{}'.format(scene_name, attr)):
                    if not mc.getAttr('{}.{}'.format(scene_name, attr), l=True):
                        mc.setAttr('{}.{}'.format(scene_name, attr),
                                   self.attrs[attr]['value'],
                                   type='doubleArray')
                else:
                    text = '{}.{} not found, skipping.'.format(scene_name, attr)
                    logger.info(text)
            else:
                if mc.objExists('{}.{}'.format(scene_name, attr)):
                    if not mc.getAttr('{}.{}'.format(scene_name, attr), l=True):
                        try:
                            mc.setAttr('{}.{}'.format(scene_name, attr), self.attrs[attr]['value'])
                        except:
                            pass
                else:
                    text = '{}.{} not found, skipping.'.format(scene_name, attr)
                    logger.info(text)

            # check the alias
            if mc.objExists('{}.{}'.format(scene_name, attr)):
                alias = self.attrs[attr].get('alias', None)
                if alias:
                    try:
                        mc.aliasAttr(alias, '{}.{}'.format(scene_name, attr))
                    except RuntimeError:
                        pass

    @property
    def mobject(self):
        """
        Gets mObject out of mObjectHandle.  Checks if it is valid before releasing it.
        Returns:
            mObject

        """
        if not isinstance(self._mobject_handle, str):
            if self._mobject_handle:
                if self._mobject_handle.isValid():
                    return self._mobject_handle.object()

        return None

    @mobject.setter
    def mobject(self, maya_node):
        """
        Tracks an mObject with a builder node.  Given a maya node it looks up
        its mobject and stores that in a list that corresponds with the
        builder node list.
        Args:
            maya_node (str): The maya node to track.

        Returns:
            Nothing

        """
        self._mobject_handle = None
        if mc.objExists(maya_node):
            selection_list = om.MSelectionList()
            selection_list.add(maya_node)
            mobject = om.MObject()
            selection_list.getDependNode(0, mobject)
            self._mobject_handle = om.MObjectHandle(mobject)

    def break_connection_to_scene(self):
        """Sets the mObject for the node to None.  This is useful if you want to break the 
        connection between the node and what is in the scene.
        """
        self._mobject_handle = None
