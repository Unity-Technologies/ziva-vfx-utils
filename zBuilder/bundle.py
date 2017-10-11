import maya.cmds as mc
import zBuilder.zMaya as mz

import re
import time

import logging

logger = logging.getLogger(__name__)


class Bundle(object):
    """Mixin class to deal with storing node data and component data.  meant to
    be inherited by main.
    """

    def __init__(self):
        import zBuilder

        self.nodes = list()
        self.components = list()
        self.info = dict()
        self.info['version'] = zBuilder.__version__
        self.info['current_time'] = time.strftime("%d/%m/%Y  %H:%M:%S")
        self.info['maya_version'] = mc.about(v=True)
        self.info['operating_system'] = mc.about(os=True)

    def __iter__(self):
        """ This iterates through the nodes.

        Returns:
            Iterator of nodes.

        """
        return iter(self.nodes)

    def __len__(self):
        """

        Returns: Length of nodes.

        """
        return len(self.nodes)

    def print_(self, type_filter=list(), name_filter=list(), components=False):
        """Prints info on each node.

        Args:
            type_filter (:obj:`list` or :obj:`str`): filter by node type.
                Defaults to :obj:`list`
            name_filter (:obj:`list` or :obj:`str`): filter by node name.
                Defaults to :obj:`list`
            components (:obj:`bool`): prints name of data stored.  Defaults to ``False``

        """

        for node in self.get_nodes(type_filter=type_filter,
                                   name_filter=name_filter):
            print node

        print '----------------------------------------------------------------'

        if components:
            for item in self.components:
                 print item

    def compare(self, type_filter=list(), name_filter=list()):

        """
        Compares info in memory with that which is in scene.

        Args:
            type_filter (:obj:`list` or :obj:`str`): filter by node type.
                Defaults to :obj:`list`
            name_filter (:obj:`list` or :obj:`str`): filter by node name.
                Defaults to :obj:`list`

        """

        for node in self.get_nodes(type_filter=type_filter,
                                   name_filter=name_filter):
            node.compare()

    def stats(self, type_filter=str()):
        """
        prints out basic stats on data

        Args:
            type_filter (:obj:`str`): filter by node type.
                Defaults to :obj:`str`
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

        data_types = set([item.type for item in self.components])

        output = 'components: '
        for data_type in data_types:
            amount = len([x for x in self.components if x.type == data_type])
            output += '{} {}   '.format(data_type, amount)

        logger.info(output)

    def add_component(self, component):
        """ appends a data obj to the data list.  Checks if data is already in
        list, if it is it overrides the previous one.

        Args:
            component (:obj:`obj`) data object to append to list
        """
        if component in self.components:
            self.components = [component if item == component else item for item in self.components]
        else:
            self.components.append(component)

    def add_node(self, node):
        """
        appends a node to the node list.  Checks if node is already in list, if
        it is it overrides the previous one.

        Args:
            node (:obj:`obj`): the node obj to append to collection list.
        """

        if node in self.nodes:
            self.nodes = [node if item == node else item for item in self.nodes]
        else:
            self.nodes.append(node)

    def remove_node(self, node):
        """
        Removes a node from the node list while keeping order.
        Args:
            node (:obj:`obj`): The node object to remove.
        """
        self.nodes.remove(node)

    def remove_component(self, component):
        """
        Removes a data from the data list while keeping order.
        Args:
            component (:obj:`obj`): The data obj to remove.
        """
        self.components.remove(component)

    def get_component(self, type_filter=list(),
                      name_filter=list(),
                      name_regex=None):
        """
        Gets data objects from data list.

        Args:
            type_filter (:obj:`str` or :obj:`list`, optional): filter by data ``type``.
                Defaults to :obj:`list`.
            name_filter (:obj:`str` or :obj:`list`, optional): filter by data ``name``.
                Defaults to :obj:`list`.
            name_regex (:obj:`str`): filter by node name by regular expression.
                Defaults to ``None``.
        Returns:
            list: List of data objects.
        """
        if not type_filter and not name_filter and not name_regex:
            return self.components

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

        return [item for item in self.components if keep_me(item)]

    def get_nodes(self, type_filter=list(),
                  name_filter=list(),
                  name_regex=None,
                  association_filter=list(),
                  association_regex=None):

        """
        Gets node objects from node list.

        Args:
            type_filter (:obj:`str` or :obj:`list`, optional): filter by node ``type``.
                Defaults to :obj:`list`.
            name_filter (:obj:`str` or :obj:`list`, optional): filter by node ``name``.
                Defaults to :obj:`list`.
            name_regex (:obj:`str`): filter by node name by regular expression.
                Defaults to ``None``.
            association_filter (:obj:`str` or :obj:`list`, optional): filter by node ``association``.
                Defaults to :obj:`list`.
            association_regex (:obj:`str`): filter by node ``association`` by regular expression.
                Defaults to ``None``.
        Returns:
            list: List of node objects.
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
            if association_regex and not re.search(association_regex,
                                                   item.association):
                return False
            return True

        return [item for item in self if keep_me(item)]

    def string_replace(self, search, replace):
        """
        searches and replaces with regular expressions items in data

        Args:
            search (:obj:`str`): what to search for
            replace (:obj:`str`): what to replace it with

        Example:
            replace `r_` at front of item with `l_`:

            >>> z.string_replace('^r_','l_')

            replace `_r` at end of line with `_l`:

            >>> z.string_replace('_r$','_l')
        """
        for node in self:
            node.string_replace(search, replace)

        for item in self.components:
            item.string_replace(search, replace)


def replace_dict_keys(search, replace, dictionary):
    """
    Does a search and replace on dictionary keys

    Args:
        search (:obj:`str`): search term
        replace (:obj:`str`): replace term
        dictionary (:obj:`dict`): the dictionary to do search on

    Returns:
        :obj:`dict`: result of search and replace
    """
    tmp = {}
    for key in dictionary:
        new = mz.replace_long_name(search, replace, key)
        tmp[new] = dictionary[key]

    return tmp



