import re
import logging
from zBuilder.IO import is_sequence

logger = logging.getLogger(__name__)


class Bundle(object):
    """Mixin class to deal with storing node data and component data.  meant to
    be inherited by main.
    """
    def __init__(self):
        self.scene_items = list()

    def __iter__(self):
        """ This iterates through the scene_items.

        Returns:
            Iterator of scene_items.

        """
        return iter(self.scene_items)

    def __len__(self):
        """

        Returns: Length of scene_items.

        """
        return len(self.scene_items)

    def __eq__(self, other):
        """ Compares the bundles list.  Makes sure lists are in same order and every element in list 
        is equal.
        """
        return self.scene_items == other.scene_items

    def __ne__(self, other):
        """ Define a non-equality test
        """
        return not self == other

    def print_(self, type_filter=list(), name_filter=list()):
        """
        Prints out basic information for each scene item in the Builder.  Information is all
        information that is stored in the __dict__.  Useful for trouble shooting.

        Args:
            type_filter (:obj:`list` or :obj:`str`): filter by scene_item type.
                Defaults to :obj:`list`
            name_filter (:obj:`list` or :obj:`str`): filter by scene_item name.
                Defaults to :obj:`list`
        """

        for scene_item in self.get_scene_items(type_filter=type_filter, name_filter=name_filter):
            print(scene_item)

        print('----------------------------------------------------------------')

    def compare(self, type_filter=list(), name_filter=list()):
        """
        Compares info in memory with that which is in scene.

        Args:
            type_filter (:obj:`list` or :obj:`str`): filter by scene_item type.
                Defaults to :obj:`list`
            name_filter (:obj:`list` or :obj:`str`): filter by scene_item name.
                Defaults to :obj:`list`

        """

        for scene_item in self.get_scene_items(type_filter=type_filter, name_filter=name_filter):
            scene_item.compare()

    def stats(self, type_filter=str()):
        """
        Prints out basic information in Maya script editor.  Information is scene item types and counts.

        Args:
            type_filter (:obj:`str`): filter by scene_item type.
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

    def append_scene_item(self, scene_item):
        """ Deprecated. Use extend_scene_items instead, because batch processing is faster. """
        self.extend_scene_items(self, [scene_item])

    def extend_scene_items(self, scene_items):
        """
        Add a list of scene items into this bundle.
        Any duplicates with existing scene items replace the existing item.
        Duplicates are identified by long name.

        Args:
            scene_items: List of objects derived from zBuilder.nodes.Base
        """

        # The order of items in self.scene_items is important,
        # so we must update existing items in place and append new items in the order given.
        # To easily update existing items, here's an index to lookup where they are by name.
        old_items = {
            scene_item.long_name: index
            for index, scene_item in enumerate(self.scene_items)
        }

        bad_index = -1
        for scene_item in scene_items:
            index = old_items.get(scene_item.long_name, bad_index)
            if index != bad_index:
                self.scene_items[index] = scene_item
            else:
                self.scene_items.append(scene_item)

    def remove_scene_item(self, scene_item):
        """
        Removes a scene_item from the bundle list while keeping order.
        Args:
            scene_item (:obj:`obj`): The scene_item object to remove.
        """
        self.scene_items.remove(scene_item)

    def get_scene_items(self,
                        type_filter=list(),
                        name_filter=list(),
                        name_regex=None,
                        association_filter=list(),
                        association_regex=None,
                        invert_match=False):
        """
        Gets the scene items from builder for further inspection or modification.

        Args:
            type_filter (:obj:`str` or :obj:`list`, optional): filter by scene_item ``type``.
                Defaults to :obj:`list`.
            name_filter (:obj:`str` or :obj:`list`, optional): filter by scene_item ``name``.
                Defaults to :obj:`list`.
            name_regex (:obj:`str`): filter by scene_item name by regular expression.
                Defaults to ``None``.
            association_filter (:obj:`str` or :obj:`list`, optional): filter by scene_item ``association``.
                Defaults to :obj:`list`.
            association_regex (:obj:`str`): filter by scene_item ``association`` by regular expression.
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
        if not is_sequence(type_filter):
            type_filter = [type_filter]

        # put association filter in a list if it isn't
        if not is_sequence(association_filter):
            association_filter = [association_filter]

        # put name filter in a list if it isn't
        if not is_sequence(name_filter):
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
                if association_set and association_set.isdisjoint(item.nice_association):
                    return invert
                if association_regex and not re.search(association_regex, item.long_association):
                    return invert

            if name_regex and not re.search(name_regex, item.name):
                return invert
            return not invert

        return [item for item in self if keep_me(item, invert_match)]

    def string_replace(self, search, replace):
        """
        Searches and replaces with regular expressions the scene items in the builder.

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
