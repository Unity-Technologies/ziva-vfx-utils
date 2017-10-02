import logging
import json
import maya.cmds as mc

logger = logging.getLogger(__name__)


class BaseComponent(object):
    TYPE = None

    def __init__(self, *args, **kwargs):

        self._name = None
        self._setup = kwargs.get('setup', None)

        if kwargs.get('deserialize', None):
            self.deserialize(kwargs.get('deserialize', None))

    def __eq__(self, other):
        if isinstance(other, BaseComponent):
            return self.name == other.name

    def __ne__(self, other):
        """Define a non-equality test"""
        return not self.__eq__(other)

    @property
    def long_name(self):
        return self._name

    @property
    def name(self):
        return self._name.split('|')[-1]

    @name.setter
    def name(self, name):
        try:
            self._name = mc.ls(name, long=True)[0]
        except IndexError:
            self._name = name

    @property
    def type(self):
        """
        get type of node

        Returns:
            (str) of node name
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
        """
        it loops through keys in dict and saves out a temp dict of items that
        can be serializable and returns that temp dict for json writing
        purposes.

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
        """
        For now this sets the mobject with the string that is there now.

        Returns:

        """
        for key in dictionary:
            if key not in ['_setup', '_class']:
                self.__dict__[key] = dictionary[key]


