import re
import logging

logger = logging.getLogger(__name__)


class Bundle(object):
    """Mixin class to deal with storing node data and component data.  meant to
    be inherited by main.
    """

    def __init__(self):
        self.scene_items = list()

    def __iter__(self):
        """ This iterates through the parameters.

        Returns:
            Iterator of parameters.

        """
        return iter(self.scene_items)

    def __len__(self):
        """

        Returns: Length of parameters.

        """
        return len(self.scene_items)

    def print_(self, type_filter=list(), name_filter=list()):
        """
        Prints out basic information for each scene item in the Builder.  Information is all
        information that is stored in the __dict__.  Useful for trouble shooting.

        Args:
            type_filter (:obj:`list` or :obj:`str`): filter by parameter type.
                Defaults to :obj:`list`
            name_filter (:obj:`list` or :obj:`str`): filter by parameter name.
                Defaults to :obj:`list`
        """

        for scene_item in self.get_scene_items(type_filter=type_filter,
                                              name_filter=name_filter):
            print scene_item

        print '----------------------------------------------------------------'

    def compare(self, type_filter=list(), name_filter=list()):

        """
        Compares info in memory with that which is in scene.

        Args:
            type_filter (:obj:`list` or :obj:`str`): filter by parameter type.
                Defaults to :obj:`list`
            name_filter (:obj:`list` or :obj:`str`): filter by parameter name.
                Defaults to :obj:`list`

        """

        for scene_item in self.get_scene_items(type_filter=type_filter,
                                              name_filter=name_filter):
            scene_item.compare()

    def stats(self, type_filter=str()):
        """
        Prints out basic information in Maya script editor.  Information is scene item types and counts.

        Args:
            type_filter (:obj:`str`): filter by parameter type.
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

        # data_types = set([item.type for item in self.parameters])
        # output = 'parameters: '
        # for data_type in data_types:
        #     amount = len([x for x in self.parameters if x.type == data_type])
        #     output += '{} {}   '.format(data_type, amount)
        # logger.info(output)

    def append_scene_item(self, scene_item):
        """
        appends a parameter to the parameter list.  Checks if parameter is
        already in list, if it is it overrides the previous one.

        Args:
            scene_item (:obj:`obj`): the parameter to append to collection list.
        """

        if scene_item in self.scene_items:
            self.scene_items = [scene_item if item == scene_item else item for item in self.scene_items]
        else:
            self.scene_items.append(scene_item)

    def extend_scene_items(self, scene_items):
        """

        Args:
            scene_items:

        Returns:

        """
        for scene_item in scene_items:
            self.append_scene_item(scene_item)

    def remove_scene_item(self, scene_item):
        """
        Removes a scene_item from the bundle list while keeping order.
        Args:
            scene_item (:obj:`obj`): The scene_item object to remove.
        """
        self.scene_items.remove(scene_item)

    def get_scene_items(self, type_filter=list(),
                        name_filter=list(),
                        name_regex=None,
                        association_filter=list(),
                        association_regex=None,
                        invert_match=False):

        """
        Gets the scene items from builder for further inspection or modification.

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
            invert_match (bool): Invert the sense of matching, to select non-matching items.
                Defaults to ``False``
        Returns:
            list: List of scene items.
        """
        # if no filters are used just return full list as it is faster
        if not type_filter and not association_filter and not name_filter and not name_regex and not association_regex:
            return self.scene_items

        # put type filter in a list if it isn't
        if not isinstance(type_filter, list):
            type_filter = [type_filter]

        # put association filter in a list if it isn't
        if not isinstance(association_filter, list):
            association_filter = [association_filter]

        # put name filter in a list if it isn't
        if not isinstance(name_filter, list):
            name_filter = [name_filter]

        type_set = set(type_filter)
        name_set = set(name_filter)
        association_set = set(association_filter)

        def keep_me(item, invert):
            if type_set and item.type not in type_set:
                return invert
            if name_set and item.name not in name_set:
                return invert
            if hasattr(item, 'association'):
                if association_set and association_set.isdisjoint(item.association):
                    return invert
                if association_regex and not re.search(association_regex,
                                                       item.association):
                    return invert

            if name_regex and not re.search(name_regex, item.name):
                return invert
            return not invert

        return [item for item in self if keep_me(item, invert_match)]

    def string_replace(self, search, replace):
        """
        Searches and replaces with regular expressions scene items in the builder.

        Args:
            search (:obj:`str`): what to search for
            replace (:obj:`str`): what to replace it with

        Example:
            replace `r_` at front of item with `l_`:

            >>> z.string_replace('^r_','l_')

            replace `_r` at end of line with `_l`:

            >>> z.string_replace('_r$','_l')
        """
        for item in self.scene_items:
            item.string_replace(search, replace)


