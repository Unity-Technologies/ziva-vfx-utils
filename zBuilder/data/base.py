import logging
import json
import maya.cmds as mc
import zBuilder.zMaya as mz

logger = logging.getLogger(__name__)


class BaseComponent(object):
    """ This is the base node for storing component data..

    Args:
        deserialize (dict, optional): a dictionary to deserialize into node.
    """
    type = None
    """ The type of the node."""
    SEARCH_EXCLUDE = ['_class']
    """ List of attributes to exclude with a string_replace"""

    def __init__(self, *args, **kwargs):

        self._name = None
        self._setup = kwargs.get('setup', None)

        if kwargs.get('deserialize', None):
            self.deserialize(kwargs.get('deserialize', None))

        self.type = self.type

    def __eq__(self, other):
        """ Are names == in node objects?
        """
        if isinstance(other, BaseComponent):
            return self.name == other.name

    def __ne__(self, other):
        """ Define a non-equality test
        """
        return not self.__eq__(other)

    def string_replace(self, search, replace):
        """ Search and replaces items in the node.  Uses regular expressions.
        Uses SEARCH_EXCLUDE to define attributes to exclude from this process.

        Goes through the dictionary and search and replace items.

        Args:
            search (str): string to search for.
            replace (str): string to replace it with.

        """
        for item in self.__dict__:
            if item not in self.SEARCH_EXCLUDE:
                if isinstance(self.__dict__[item], (tuple, list)):
                    if self.__dict__[item]:
                        new_names = []
                        for name in self.__dict__[item]:
                            if isinstance(name, basestring):
                                new_name = mz.replace_long_name(search, replace, name)
                                new_names.append(new_name)
                                self.__dict__[item] = new_names
                elif isinstance(self.__dict__[item], basestring):
                    if self.__dict__[item]:
                        self.__dict__[item] = mz.replace_long_name(
                            search, replace, self.__dict__[item])
                elif isinstance(self.__dict__[item], dict):
                    # TODO needs functionality (replace keys)
                    print 'DICT', item, self.__dict__[item], self.name
                    # raise StandardError('HELP')

    @property
    def long_name(self):
        return self._name

    @property
    def name(self):
        """ The name of the node.
        """
        return self._name.split('|')[-1]

    @name.setter
    def name(self, name):
        try:
            self._name = mc.ls(name, long=True)[0]
        except IndexError:
            self._name = name

    @property
    def type(self):
        """ The type of node.
        """
        try:
            return self.TYPE
        except AttributeError:
            return None

    @type.setter
    def type(self, type_):
        """
        Sets type of node

        Args:
            type_ (str): the type of node.
        """
        self.TYPE = type_

    def serialize(self):
        """  Makes node serializable.

        This replaces an mObject with the name of the object in scene to make it
        serializable for writing out to json.  Then it loops through keys in
        dict and saves out a temp dict of items that can be serializable and
        returns that temp dict for json writing purposes.

        Returns:
            dict: of serializable items
        """

        # culling __dict__ of any non-serializable items so we can save as json
        output = dict()
        for key in self.__dict__:
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


