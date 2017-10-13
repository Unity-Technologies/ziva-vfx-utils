import logging

import maya.OpenMaya as om
import maya.cmds as mc
import maya.mel as mm
import zBuilder.zMaya as mz
import json

logger = logging.getLogger(__name__)


class BaseParameter(object):
    """ The base node for the node functionality of all nodes
    """
    type = None
    TYPES = None
    """ The type of node. """
    MAP_LIST = []
    """ List of maps to store. """
    SEARCH_EXCLUDE = ['_class', 'attrs', '_builder_type', 'type']
    """ List of attributes to exclude with a string_replace"""
    EXTEND_ATTR_LIST = list()
    """ List of maya attributes to add to attribute list when capturing."""

    def __init__(self, *args, **kwargs):
        self._name = None
        self.attrs = {}
        self._association = []
        self.__mobject = None

        self._class = (self.__class__.__module__, self.__class__.__name__)

        self._builder_type = self.__class__.__module__.split('.')
        self._builder_type = '{}.{}'.format(self._builder_type[0],
                                            self._builder_type[1])

        self._setup = kwargs.get('setup', None)

        if kwargs.get('deserialize', None):
            self.deserialize(kwargs.get('deserialize', None))

        # if args:
        #     self.populate(args[0])

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

    def populate(self, *args, **kwargs):
        """ Populates the node with the info from the passed maya node in args.

        This is deals with basic stuff including attributes.  For other things it
        is meant to be overridden in inherited node.

        Args:
            *args (str): The maya node to populate it with.

        """

        selection = mz.parse_args_for_selection(args)

        self.name = selection[0]
        self.type = mc.objectType(selection[0])
        attr_list = mz.build_attr_list(selection[0])
        if self.EXTEND_ATTR_LIST:
            attr_list.extend(self.EXTEND_ATTR_LIST)
        attrs = mz.build_attr_key_values(selection[0], attr_list)
        self.attrs = attrs
        self.mobject = selection[0]

    def build(self, *args, **kwargs):
        """ Builds the node in maya.  meant to be overwritten.
        """
        pass
        # raise NotImplementedError

    def string_replace(self, search, replace):
        """ Search and replaces items in the node.  Uses regular expressions.
        Uses SEARCH_EXCLUDE to define attributes to exclude from this process.

        Goes through the dictionary and search and replace items.

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
                # TODO needs functionality (replace keys)
                print 'DICT', item, self.__dict__[item], self.name
                # tmp = {}
                # for key in dictionary:
                #     new = mz.replace_long_name(search, replace, key)
                #     tmp[new] = dictionary[key]

    @property
    def long_name(self):
        """ Long name of node.
        """
        return self._name

    @property
    def name(self):
        """ Name of node.
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
        """ Compares node in memory with that which is in maya scene.

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
        This checks stored mObject and gets name of object in scene.  If no
        mObject it returns node name.

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
        Gets mObject stored with node.
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
