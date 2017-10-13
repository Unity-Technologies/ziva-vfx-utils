import zBuilder.zMaya as mz

import re


import logging

logger = logging.getLogger(__name__)


class Bundle(object):
    """Mixin class to deal with storing node data and component data.  meant to
    be inherited by main.
    """

    def __init__(self):
        import zBuilder

        self.parameters = list()

    def __iter__(self):
        """ This iterates through the parameters.

        Returns:
            Iterator of parameters.

        """
        return iter(self.parameters)

    def __len__(self):
        """

        Returns: Length of parameters.

        """
        return len(self.parameters)

    @property
    def data(self):
        logger.info("self.data deprecated, use self.components")
        return self.components

    def print_(self, type_filter=list(), name_filter=list(), components=False):
        """Prints info on each parameter.

        Args:
            type_filter (:obj:`list` or :obj:`str`): filter by parameter type.
                Defaults to :obj:`list`
            name_filter (:obj:`list` or :obj:`str`): filter by parameter name.
                Defaults to :obj:`list`
            components (:obj:`bool`): prints name of data stored.  Defaults to ``False``

        """

        for parameter in self.get_parameters(type_filter=type_filter,
                                             name_filter=name_filter):
            print parameter

        print '----------------------------------------------------------------'
        #
        # if components:
        #     for item in self.components:
        #          print item

    def compare(self, type_filter=list(), name_filter=list()):

        """
        Compares info in memory with that which is in scene.

        Args:
            type_filter (:obj:`list` or :obj:`str`): filter by parameter type.
                Defaults to :obj:`list`
            name_filter (:obj:`list` or :obj:`str`): filter by parameter name.
                Defaults to :obj:`list`

        """

        for parameter in self.get_parameters(type_filter=type_filter,
                                             name_filter=name_filter):
            parameter.compare()

    def stats(self, type_filter=str()):
        """
        prints out basic stats on data

        Args:
            type_filter (:obj:`str`): filter by parameter type.
                Defaults to :obj:`str`
        """
        # tmp = {}
        # for i, d in enumerate(self):
        #
        #     t = d.type
        #     if type_filter:
        #         if type_filter == t:
        #             if not t in tmp:
        #                 tmp[t] = []
        #             if type_filter not in tmp:
        #                 tmp[type_filter] = []
        #             tmp[type_filter].append(d)
        #     else:
        #         if not t in tmp:
        #             tmp[t] = []
        #         tmp[t].append(d)
        #
        # for key in tmp:
        #     logger.info('{} {}'.format(key, len(tmp[key])))

        data_types = set([item.type for item in self.parameters])
        output = 'parameters: '
        for data_type in data_types:
            amount = len([x for x in self.parameters if x.type == data_type])
            output += '{} {}   '.format(data_type, amount)
        logger.info(output)

    def add_parameter(self, parameter):
        """
        appends a parameter to the parameter list.  Checks if parameter is
        already in list, if it is it overrides the previous one.

        Args:
            parameter (:obj:`obj`): the parameter to append to collection list.
        """

        #if parameter in self.parameters:
        #    self.parameters = [parameter if item == parameter else item for item in self.parameters]
        #else:
        self.parameters.extend(parameter)

    def remove_parameter(self, parameter):
        """
        Removes a parameter from the parameter list while keeping order.
        Args:
            parameter (:obj:`obj`): The parameter object to remove.
        """
        self.parameters.remove(parameter)

    def get_parameters(self, type_filter=list(),
                       name_filter=list(),
                       name_regex=None,
                       association_filter=list(),
                       association_regex=None):

        """
        Gets parameters from parameter list.

        Args:
            type_filter (:obj:`str` or :obj:`list`, optional): filter by parameter ``type``.
                Defaults to :obj:`list`.
            name_filter (:obj:`str` or :obj:`list`, optional): filter by parameter ``name``.
                Defaults to :obj:`list`.
            name_regex (:obj:`str`): filter by parameter name by regular expression.
                Defaults to ``None``.
            association_filter (:obj:`str` or :obj:`list`, optional): filter by parameter ``association``.
                Defaults to :obj:`list`.
            association_regex (:obj:`str`): filter by parameter ``association`` by regular expression.
                Defaults to ``None``.
        Returns:
            list: List of parameters.
        """
        if not type_filter and not association_filter and not name_filter and not name_regex and not association_regex:
            return self.parameters

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
        searches and replaces with regular expressions items in parameters and
        components

        Args:
            search (:obj:`str`): what to search for
            replace (:obj:`str`): what to replace it with

        Example:
            replace `r_` at front of item with `l_`:

            >>> z.string_replace('^r_','l_')

            replace `_r` at end of line with `_l`:

            >>> z.string_replace('_r$','_l')
        """
        for item in self.parameters:
            item.string_replace(search, replace)
        #
        # for item in self.components:
        #     item.string_replace(search, replace)


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



