import logging
import zBuilder.zMaya as mz
import maya.cmds as mc

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
        self._builder_type = '{}.{}'.format(self._builder_type[0],
                                            self._builder_type[1])

        self.builder = kwargs.get('builder', None)
        deserialize = kwargs.get('deserialize', None)

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

