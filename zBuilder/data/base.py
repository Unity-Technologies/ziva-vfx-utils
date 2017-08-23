import logging

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
