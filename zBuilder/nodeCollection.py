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
        self.data = dict()
        self.info = dict()
        self.info['version'] = zBuilder.__version__
        self.info['current_time'] = time.strftime("%d/%m/%Y  %H:%M:%S")
        self.info['maya_version'] = mc.about(v=True)
        self.info['operating_system'] = mc.about(os=True)

    def print_(self, type_filter=None, name_filter=None, component_data=True):

        """
        print info on each node

        Args:
            type_filter (str): filter by node type.  Defaults to None
            name_filter (str): filter by node name. Defaults to None
            component_data (bool): prints name of data stored.  Defaults to False

        """

        for node in self.get_nodes(type_filter=type_filter,
                                   name_filter=name_filter):
            node.print_()

        print '----------------------------------------------------------------'

        for key in self.data:
            print self.data[key]

    def compare(self, type_filter=None, name_filter=None):

        """
        print info on each node

        Args:
            type_filter (str): filter by node type.  Defaults to **None**
            name_filter (str): filter by node name. Defaults to **None**
            print_data (bool): prints name of data stored.  Defaults to **False**

        """

        for node in self.get_nodes(type_filter=type_filter,
                                   name_filter=name_filter):
            node.compare()

    def stats(self, type_filter=None):
        """
        prints out basic stats on data

        Args:
            type_filter (str): filter by node type.  Defaults to None
        """
        tmp = {}
        # print
        for i, d in enumerate(self.get_nodes()):
            # print d#,self.get_nodes()
            t = d.get_type()
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

        data_types = self.get_data().keys()
        output = 'component data: '
        for data_type in data_types:
            amount = len(self.get_data_by_key(data_type))
            output += '{} {}   '.format(data_type,amount)

        logger.info(output)

    def add_data_object(self, data):
        """
        appends a mesh to the mesh list

        Args:

        """
        type_ = data.TYPE
        name = data.get_name(long_name=True)
        if not type_ in self.data:
            self.data[type_] = {}

        if not self.get_data_by_key_name(type_, name):
            self.data[type_][name] = data

    def get_data(self):
        """

        Returns:

        """
        return self.data

    def set_data(self, data):
        """

        Returns:

        """
        self.data = data

    def get_data_by_key_name(self, key, name):
        """
        Gets data given 'key'

        Args:
            key (str): the key to get data from.
            name (str): name of the data.

        Returns:
            obj: Object of data.

        Example:
            
            >>> get_data_by_key_name('mesh','l_bicepMuscle')
        """
        if self.data.get(key):
            return self.data[key].get(name, None)
        else:
            return None

    def get_data_by_key(self, key):
        """
        Gets all data for given 'key'

        args:
            key (str): the key to get data from

        returns:
            list: of data objs

        Example:
           get_data_by_key('mesh')
        """
        return self.data.get(key, None)

    def add_node(self, node):
        """
        appends a node to the node list

        Args:
            node (obj): the node obj to append to collection list.
        """
        self.__collection.append(node)

    def get_nodes(self, type_filter=None, name_filter=None):
        """
        get nodes in data object

        Args:
            type_filter (str): filter by node type.  Defaults to **None**
            name_filter (str): filter by node name.  Defaults to **None**

        Returns:
            [] of nodes
        """
        items = []
        if not type_filter:
            return self.__collection
        else:
            for i, node in enumerate(self.__collection):
                if node.get_type() == type_filter:

                    if name_filter:
                        if not isinstance(name_filter, (list, tuple)):
                            name_filter = name_filter.split(' ')
                        if not set(name_filter).isdisjoint(
                                node.get_association()):
                            items.append(node)
                    else:
                        items.append(node)
        return items

    def get_node_by_name(self, name):
        """
        utility function to get node by name.

        Args:
            name (str): name of node.

        Returns:
            builder node (obj)
        """
        for node in self.__collection:
            if node.get_name() == name:
                return node

    def set_nodes(self, nodes):
        """
        Args:
            nodes (list): the nodes to replace the collection with
        """
        self.__collection = nodes

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
        for node in self.get_nodes():
            node.string_replace(search, replace)

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



