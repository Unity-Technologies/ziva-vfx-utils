import maya.cmds as mc
import zBuilder.zMaya as mz

import re
import time

import logging

logger = logging.getLogger(__name__)


class NodeCollection(object):
    # __metaclass__ = abc.ABCMeta
    """
    This is an object that holds the node data in a list
    """

    def __init__(self):
        import zBuilder

        self.__collection = list()
        self._data = list()
        self.info = dict()
        self.info['version'] = zBuilder.__version__
        self.info['current_time'] = time.strftime("%d/%m/%Y  %H:%M:%S")
        self.info['maya_version'] = mc.about(v=True)
        self.info['operating_system'] = mc.about(os=True)

    def __iter__(self):
        return iter(self.__collection)

    def __len__(self):
        return len(self.__collection)

    def print_(self, type_filter=list(), name_filter=list(), component_data=False):

        """
        print info on each node

        Args:
            type_filter (str): filter by node type.  Defaults to list()
            name_filter (str): filter by node name. Defaults to list()
            component_data (bool): prints name of data stored.  Defaults to False

        """

        for node in self.get_nodes(type_filter=type_filter,
                                   name_filter=name_filter):
            print node

        print '----------------------------------------------------------------'

        if component_data:
            for item in self.data:
                 print item

    def compare(self, type_filter=list(), name_filter=list()):

        """
        Compares info in memory with that which is in scene.

        Args:
            type_filter (str): filter by node type.  Defaults to list()
            name_filter (str): filter by node name. Defaults to list()

        """

        for node in self.get_nodes(type_filter=type_filter,
                                   name_filter=name_filter):
            node.compare()

    def stats(self, type_filter=list()):
        """
        prints out basic stats on data

        Args:
            type_filter (str): filter by node type.  Defaults to list()
        """
        tmp = {}
        for i, d in enumerate(self):

            t = d.type
            if type_filter:
                if type_filter == t:
                    if not t in tmp:
                        tmp[t] = []
                    if type_filter not in tmp:
                        tmp[type_filter] = []
                    tmp[type_filter].append(d)
            else:
                if not t in tmp:
                    tmp[t] = []
                tmp[t].append(d)

        for key in tmp:
            logger.info('{} {}'.format(key, len(tmp[key])))

        data_types = set([item.type for item in self.data])

        output = 'component data: '
        for data_type in data_types:
            amount = len([x for x in self.data if x.type == data_type])
            output += '{} {}   '.format(data_type, amount)

        logger.info(output)

    @property
    def data(self):
        """

        Returns:

        """
        return self._data

    @data.setter
    def data(self, data):
        """

        Returns:

        """
        self._data = data

    def add_data(self, data):
        """
        appends a data obj to the data list.  Checks if data is already in list,
        if it is it overrides the previous one.

        Args:

        """
        if data in self._data:
            self._data = [data if item == data else item for item in self._data]
        else:
            self._data.append(data)

    @property
    def nodes(self):
        return self.__collection

    @nodes.setter
    def nodes(self, value):
        self.__collection = value

    def add_node(self, node):
        """
        appends a node to the node list.  Checks if node is already in list, if
        it is it overrides the previous one.

        Args:
            node (obj): the node obj to append to collection list.
        """

        if node in self.__collection:
            self.__collection = [node if item == node else item for item in self.__collection]
        else:
            self.__collection.append(node)

    def remove_node(self, node):
        """
        Removes a given node from list
        Args:
            node:

        Returns:

        """
        self.nodes.remove(node)

    def remove_data(self, data):
        self.data.remove(data)
    #
    # def get_data(self, type_filter=list(), name_filter=list()):
    #     """
    #     get nodes in data object
    #
    #     Args:
    #         type_filter (str or list): filter by node type.  Defaults to list()
    #         name_filter (str or list): filter by node name.  Looks for association.  Defaults to list()
    #
    #     Returns:
    #         [] of component data
    #     """
    #
    #     if not type_filter and not name_filter:
    #         return self.nodes
    #
    #     if not isinstance(type_filter, list):
    #         type_filter = [type_filter]
    #     #
    #     if not isinstance(name_filter, list):
    #         name_filter = [name_filter]
    #
    #     if type_filter:
    #         items = [x for x in self.data if x.type in type_filter]
    #     else:
    #         items = self.data
    #
    #     if name_filter:
    #         items = [item for item in items if item.name in name_filter]
    #
    #     return items

    def get_data(self, type_filter=list(),
                  name_filter=list(),
                  name_regex=None):
        """
        get nodes in data object

        Args:
            type_filter (str or list): filter by node type.  Defaults to list()
            name_filter (str or list): filter by node name.  Defaults to list()
            name_regex (str) filter by node name by regular expression.  Defaults to None
        Returns:
            [] of nodes
        """
        if not type_filter and not name_filter and not name_regex:
            return self.data

        if not isinstance(type_filter, list):
            type_filter = [type_filter]

        if not isinstance(name_filter, list):
            name_filter = [name_filter]

        type_set = set(type_filter)
        name_set = set(name_filter)

        def keep_me(item):
            if type_set and item.type not in type_set:
                return False
            if name_set and item.name not in name_set:
                return False
            if name_regex and not re.search(name_regex, item.name):
                return False
            return True

        return [item for item in self.data if keep_me(item)]

    def get_nodes(self, type_filter=list(),
                  name_filter=list(),
                  name_regex=None,
                  association_filter=list(),
                  association_regex=None):
        """
        get nodes in data object

        Args:
            type_filter (str or list): filter by node type.  Defaults to list()
            name_filter (str or list): filter by node name.  Defaults to list()
            name_regex (str) filter by node name by regular expression.  Defaults to None
            association_filter (str or list): filter by node association.  Looks for association.  Defaults to list()
            association_regex (str) filter by node association by regular expression.  Defaults to None
        Returns:
            [] of nodes
        """
        if not type_filter and not association_filter and not name_filter and not name_regex and not association_regex:
            return self.nodes

        if not isinstance(type_filter, list):
            type_filter = [type_filter]

        if not isinstance(association_filter, list):
            association_filter = [association_filter]

        if not isinstance(name_filter, list):
            name_filter = [name_filter]

        type_set = set(type_filter)
        name_set = set(name_filter)
        association_set = set(association_filter)

        def keep_me(item):
            if type_set and item.type not in type_set:
                return False
            if name_set and item.name not in name_set:
                return False
            if association_set and association_set.isdisjoint(item.association):
                return False
            if name_regex and not re.search(name_regex, item.name):
                return False
            if association_regex and not re.search(association_regex, item.association):
                return False
            return True

        return [item for item in self if keep_me(item)]

    def string_replace(self, search, replace):
        """
        searches and replaces with regular expressions items in data

        Args:
            search (str): what to search for
            replace (str): what to replace it with

        Example:
            replace `r_` at front of item with `l_`:

            >>> z.string_replace('^r_','l_')

            replace `_r` at end of line with `_l`:

            >>> z.string_replace('_r$','_l')
        """
        for node in self:
            node.string_replace(search, replace)

        for item in self.data:
            item.string_replace(search, replace)

    def apply(self, *args, **kwargs):
        """
        must create a method to inherit this class
        """
        raise NotImplementedError("Subclass must implement abstract method")

    def retrieve_from_scene(self, *args, **kwargs):
        """
        must create a method to inherit this class
        """
        raise NotImplementedError("Subclass must implement abstract method")


def replace_dict_keys(search, replace, dictionary):
    """
    Does a search and replace on dictionary keys

    Args:
        search (str): search term
        replace (str): replace term
        dictionary (dict): the dictionary to do search on

    Returns:
        dict: result of search and replace
    """
    tmp = {}
    for key in dictionary:
        new = mz.replace_long_name(search, replace, key)
        tmp[new] = dictionary[key]

    return tmp



