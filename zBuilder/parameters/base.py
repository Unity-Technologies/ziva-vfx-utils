import logging

import maya.OpenMaya as om
import maya.cmds as mc
import maya.mel as mm
import zBuilder.zMaya as mz
import json

logger = logging.getLogger(__name__)


class BaseParameter(object):
    """ The base node for the node functionality of all nodes

    Args:
        maya_node (str, optional): maya node to populate parameter with.
        setup (object, optional): The builder object for reference.
        deserialize (dict, optional): if given a dictionary to deserialize it
            fills hte parameter with contents of dictionary using the deserialize
            method.

    Attributes:
        type (str): type of parameter.  Tied with maya node type.
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

    def __init__(self, maya_node=None, builder=None, deserialize=None):
        self._name = None
        self.attrs = {}
        self._association = []
        self.__mobject = None

        self._class = (self.__class__.__module__, self.__class__.__name__)

        self._builder_type = self.__class__.__module__.split('.')
        self._builder_type = '{}.{}'.format(self._builder_type[0],
                                            self._builder_type[1])

        self.builder = builder

        if deserialize:
            self.deserialize(deserialize)

        # if maya_node:
        #    self.populate(maya_node=maya_node)

    def __eq__(self, other):
        """ Are names == in node objects?
        """
        if isinstance(other, BaseParameter):
            return self.name == other.name

    def __ne__(self, other):
        """ Define a non-equality test
        """
        return not self.__eq__(other)

    def __str__(self):
        if self.name:
            name = self.name
            output = ''
            output += '= {} <{} {}> ==================================\n'.format(name,self.__class__.__module__, self.__class__.__name__)
            for key in self.__dict__:
                output += '\t{} - {}\n'.format(key, self.__dict__[key])

            return output
        return '<%s.%s>' % (self.__class__.__module__, self.__class__.__name__)

    def __repr__(self):
        output = '{}("{}")'.format(self.__class__.__name__, self.name)
        return output

    def serialize(self):
        """  Makes node serializable.

        This replaces an mObject with the name of the object in scene to make it
        serializable for writing out to json.  Then it loops through keys in
        dict and saves out a temp dict of items that can be serializable and
        returns that temp dict for json writing purposes.

        Returns:
            dict: of serializable items
        """
        # removing and storing mobject as a string (object name)
        if hasattr(self, '__mobject'):
            if self.__mobject:
                self.__mobject = mz.get_name_from_m_object(self.__mobject)

        # culling __dict__ of any non-serializable items so we can save as json
        output = dict()
        for key in self.__dict__:
            if hasattr(self.__dict__[key], '_class') and hasattr(self.__dict__[key], 'serialize'):
                output[key] = self.__dict__[key].serialize()
            try:
                json.dumps(self.__dict__[key])
                output[key] = self.__dict__[key]
            except TypeError:
                pass
        return output

    def deserialize(self, dictionary):
        """ Deserializes a node with given dict.

        Takes a dictionary and goes through keys and fills up __dict__.

        Args (dict): The given dict.
        """
        for key in dictionary:
            if key not in ['_setup', '_class']:
                self.__dict__[key] = dictionary[key]

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
        pass
        # raise NotImplementedError

    def string_replace(self, search, replace):
        """ Search and replaces items in the node.  Uses regular expressions.
        Uses SEARCH_EXCLUDE to define attributes to exclude from this process.

        Goes through the __dict__ and search and replace items.

        Works with strings, lists of strings and dictionaries where the values
        are either strings or list of strings.  More specific searches should be
        overridden here.

        Args:
            search (str): string to search for.
            replace (str): string to replace it with.

        """
        searchable = [x for x in self.__dict__ if x not in self.SEARCH_EXCLUDE]
        # print 'SEARCH: ', searchable
        for item in searchable:
            if isinstance(self.__dict__[item], (tuple, list)):
                new_names = []
                for name in self.__dict__[item]:
                    if isinstance(name, basestring):
                        new_name = mz.replace_long_name(search, replace, name)
                        new_names.append(new_name)
                        self.__dict__[item] = new_names
            elif isinstance(self.__dict__[item], basestring):
                self.__dict__[item] = mz.replace_long_name(search,
                                                           replace,
                                                           self.__dict__[item])
            elif isinstance(self.__dict__[item], dict):
                self.__dict__[item] = mz.replace_dict_keys(search, replace, self.__dict__[item])
                for key, v in self.__dict__[item].iteritems():
                    if isinstance(v, basestring):
                        new_name = mz.replace_long_name(search, replace, v)
                        new_names.append(new_name)
                        self.__dict__[item][key] = new_names
                    if isinstance(v, (tuple, list)):
                        new_names = []
                        for name in self.__dict__[item][key]:
                            if isinstance(item, basestring):
                                new_name = mz.replace_long_name(search, replace, name)
                                new_names.append(new_name)
                                self.__dict__[item][key] = new_names

    @property
    def long_name(self):
        """ Long name of parameter corresponding to long name of maya node.
        This property is not settable.  To set it use self.name.
        """
        return self._name

    @property
    def name(self):
        """ Name of parameter corresponding to maya node name.  Setting this
        property will check for long name and store that.  self.name still
        returns short name, self.long_name returns the stored long name.
        """
        return self._name.split('|')[-1]

    @name.setter
    def name(self, name):
        self._name = mc.ls(name, long=True)[0]

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
        # if isinstance(association, str):
        #     self._association = [association]
        # else:
        #     self._association = association

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
                        print 'DIFF:', name + '.' + attr, '\tobject value:', obj_val, '\tscene value:', scene_val

    def get_scene_name(self, long_name=False):
        """
        This checks stored mObject and gets name of maya object in scene.  If no
        mObject it returns parameter name.

        Args:
            long_name (bool): Return the fullpath or not.  Defaults to True.

        Returns:
            (str) Name of maya object.
        """
        name = None
        if self.mobject:
            name = mz.get_name_from_m_object(self.mobject)

        if not name:
            name = self.long_name

        if not long_name:
            name = name.split('|')[-1]
        return name

    def set_maya_attrs(self, attr_filter=None):
        """
        Given a Builder node this set the attributes of the object in the maya
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
                node_attrs = list(
                    set(node_attrs).intersection(attr_filter[type_]))

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
                            mc.setAttr('{}.{}'.format(scene_name, attr),
                                       self.attrs[attr]['value'])
                        except:
                            pass
                else:
                    text = '{}.{} not found, skipping.'.format(scene_name, attr)
                    logger.info(text)

    @property
    def mobject(self):
        """
        Gets mObject stored with parameter.
        Returns:
            mObject

        """
        return self.__mobject

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
        self.__mobject = None
        if maya_node:
            if mc.objExists(maya_node):
                selection_list = om.MSelectionList()
                selection_list.add(maya_node)
                mobject = om.MObject()
                selection_list.getDependNode(0, mobject)
                self.__mobject = mobject
