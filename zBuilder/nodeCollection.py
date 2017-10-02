import json
import maya.cmds as mc

import zBuilder.zMaya as mz

import importlib
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

    # TODO lookup by short name
    def get_data(self, type_filter=list(), name_filter=list()):
        """
        get nodes in data object

        Args:
            type_filter (str or list): filter by node type.  Defaults to list()
            name_filter (str or list): filter by node name.  Looks for association.  Defaults to list()

        Returns:
            [] of component data
        """

        if not type_filter and not name_filter:
            return self.nodes

        if not isinstance(type_filter, list):
            type_filter = [type_filter]
        #
        if not isinstance(name_filter, list):
            name_filter = [name_filter]

        if type_filter:
            items = [x for x in self.data if x.type in type_filter]
        else:
            items = self.data

        if name_filter:
            items = [item for item in items if item.name in name_filter]

        return items

    def get_nodes(self, type_filter=list(), name_filter=list()):
        """
        get nodes in data object

        Args:
            type_filter (str or list): filter by node type.  Defaults to list()
            name_filter (str or list): filter by node name.  Looks for association.  Defaults to list()

        Returns:
            [] of nodes
        """
        # if not type_filter and not name_filter:
        #     return self.nodes
        #

        #
        # if not isinstance(name_filter, list):
        #     name_filter = [name_filter]
        #
        # types = set(type_filter or [])
        # names = set(name_filter or [])
        # print types
        # print names
        # keep_type = lambda item : type_filter is None or item.type in types
        # keep_name = lambda item : name_filter is None or not names.isdisjoint(item.association)
        # return [item for item in self if keep_name(item) and keep_type(item)]

        if not type_filter and not name_filter:
            return self.nodes

        if not isinstance(type_filter, list):
            type_filter = [type_filter]

        if not isinstance(name_filter, list):
            name_filter = [name_filter]

        if type_filter:
            items = [x for x in self if x.type in type_filter]
        else:
            items = self.nodes

        if name_filter:
            nf_set = set(name_filter)
            items = [item for item in items if not nf_set.isdisjoint(item.association)]

        return items

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
        [node.string_replace(search, replace) for node in self]

        # deal with the data search and replacing
        for key in self.data:

            # replace the key names in data
            self.data[key] = replace_dict_keys(search, replace, self.data[key])

            # run search and replace on individual items
            for item in self.data[key]:
                self.data[key][item].string_replace(search, replace)

    # @abc.abstractmethod
    def apply(self, *args, **kwargs):
        """
        must create a method to inherit this class
        """
        raise NotImplementedError("Subclass must implement abstract method")

    # @abc.abstractmethod
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



