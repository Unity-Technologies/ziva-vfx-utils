import logging

import zBuilder
import zBuilder.IO as io
import zBuilder.zMaya as mz

import maya.cmds as mc

import time
import json

logger = logging.getLogger(__name__)


class Base(object):

    TYPES = None
    SEARCH_EXCLUDE = ['_class', 'attrs', '_builder_type', 'type']
    """ A list of attribute names in __dict__ to
            exclude from the string_replace method. """

    def __init__(self, *args, **kwargs):
        self._name = None
        self._class = (self.__class__.__module__, self.__class__.__name__)

        self._builder_type = self.__class__.__module__.split('.')
        self._builder_type = '{}.{}'.format(self._builder_type[0], self._builder_type[1])

        self.builder = kwargs.get('builder', None)
        deserialize = kwargs.get('deserialize', None)

        self._children = []
        self._parent = kwargs.get('parent', None)

        self.info = dict()
        self.info['version'] = zBuilder.__version__
        self.info['current_time'] = time.strftime("%d/%m/%Y  %H:%M:%S")
        self.info['maya_version'] = mc.about(v=True)
        self.info['operating_system'] = mc.about(os=True)

        if self._parent is not None:
            self._parent.add_child(self)

        if deserialize:
            self.deserialize(deserialize)

    def __eq__(self, other):
        """ Are names == in node objects?
        """
        if isinstance(other, Base):
            return self.name == other.name

    def __ne__(self, other):
        """ Define a non-equality test
        """
        return not self.__eq__(other)

    def add_child(self, child):
        self._children.append(child)

    def child(self, row):
        return self._children[row]

    def child_count(self):
        return len(self._children)

    def parent(self):
        return self._parent

    def row(self):
        if self._parent is not None:
            return self._parent._children.index(self)
        else:
            return 0

    def log(self, tab_level=-1):
        output = ""
        tab_level += 1

        for i in range(tab_level):
            output += "\t"
        output += "|-----" + self._name + "\n"

        print self._children
        print self._parent
        for child in self._children:
            output += child.log(tab_level)

        tab_level -= 1
        output += "\n"

        return output

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
        if self._name:
            return self._name.split('|')[-1]
        else:
            return None

    @name.setter
    def name(self, name):
        if mc.ls(name, long=True):
            self._name = mc.ls(name, long=True)[0]
        else:
            self._name = name

    def serialize(self):
        """  Makes node serializable.

        It loops through keys in __dict__ and saves out a temp dict of items
        that can be serializable and returns that temp dict for json writing
        purposes.

        Returns:
            dict: of serializable items
        """
        output = serialize_object(self)
        return output

    def deserialize(self, dictionary):
        """ Deserializes a node with given dict.

        Takes a dictionary and goes through keys and fills up __dict__.

        Args (dict): The given dict.
        """
        self.__dict__ = dictionary

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
        for item in searchable:
            if isinstance(self.__dict__[item], (tuple, list)):
                new_names = []
                for name in self.__dict__[item]:
                    if isinstance(name, basestring):
                        new_name = mz.replace_long_name(search, replace, name)
                        new_names.append(new_name)
                        self.__dict__[item] = new_names
            elif isinstance(self.__dict__[item], basestring):
                self.__dict__[item] = mz.replace_long_name(search, replace, self.__dict__[item])
            elif isinstance(self.__dict__[item], dict):
                new_names = []
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

    def write(self, file_path):
        """ Writes out the scene item to a json file given a file path.

        Args:
            file_path (str): The file path to write to disk.
        """
        # json_data = io.pack_zbuilder_contents(self)
        node_data = dict()
        node_data['d_type'] = 'node_data'
        node_data['data'] = self

        info = dict()
        info['d_type'] = 'info'
        info['data'] = self.builder.info

        json_data = [node_data, info]

        if io.dump_json(file_path, json_data):
            logger.info('Wrote File: %s' % file_path)


def serialize_object(obj):
    """ Takes in a python obj and scrubs through the __dict__

    Args:
        obj ([object]): Python object to inspect.

    Returns:
        dict: Of serializable obj
    """

    obj._parent = None
    obj._children = None

    # tmp_tmp = []
    output = dict()
    for key in obj.__dict__:
        if hasattr(obj.__dict__[key], '_class') and hasattr(obj.__dict__[key], 'serialize'):
            output[key] = obj.__dict__[key].serialize()
        try:
            json.dumps(obj.__dict__[key])
            output[key] = obj.__dict__[key]
        except TypeError:
            pass

    return output
