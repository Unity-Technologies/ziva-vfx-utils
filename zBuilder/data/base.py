import logging
import json

logger = logging.getLogger(__name__)


class BaseComponent(object):
    TYPE = None

    def __init__(self, *args, **kwargs):

        self._name = None

    def get_name(self, long_name=False):
        """

        Args:
            long_name:

        Returns:

        """
        if self._name:
            if long_name:
                return self._name
            else:
                return self._name.split('|')[-1]
        else:
            return None

    def set_name(self, name):
        self._name = name

    def serialize(self):
        """
        it loops through keys in dict and saves out a temp dict of items that
        can be serializable and returns that temp dict for json writing
        \purposes.

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
            self.__dict__[key] = dictionary[key]
        #  self.set_mobject(self.get_mobject())
        print 'deserialize: ', self.__repr__()

