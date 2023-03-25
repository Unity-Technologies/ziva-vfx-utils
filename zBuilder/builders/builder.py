import inspect
import logging
import re
import sys
# For parameter_factory() and find_class(), though not use directly,
import zBuilder.nodes.parameters

from collections import Counter
from zBuilder.utils.commonUtils import is_sequence, is_string, parse_version_info
from zBuilder.utils.mayaUtils import get_type, parse_maya_node_for_selection
from zBuilder import __version__

logger = logging.getLogger(__name__)


class Builder(object):
    """ The main entry point for using zBuilder.

    """

    def __init__(self):
        self.scene_items = list()
        from zBuilder.nodes.base import Base
        self.root_node = Base()
        self.root_node.name = 'ROOT'

    def __eq__(self, other):
        """ Compares the builders.
        """
        return (type(other) == type(self)) and (self.scene_items == other.scene_items)

    def __ne__(self, other):
        """ Define a non-equality test
        """
        return not self == other

    def log(self):
        self.root_node.log()

    def node_factory(self, node, parent=None):
        """Given a maya node, this checks objType and instantiates the proper
        zBuilder.node and populates it and returns it.

        Args:
            node (:obj:`str`): Name of maya node.
            get_parameters (bool):
        Returns:
            obj: zBuilder node populated.
        """
        type_ = get_type(node)
        if not parent:
            parent = self.root_node

        scene_items = []
        node_created = True
        obj = find_class('zBuilder.nodes', type_)
        obb = obj(parent=parent, builder=self)
        try:
            obb.populate(maya_node=node)

        except Exception:
            logger.exception('Failed to populate node: {}, skipped.'.format(node))
            node_created = False
        if node_created:
            obb.post_populate()
            scene_items.append(obb)

        for node in scene_items:
            if hasattr(node, 'spawn_parameters'):
                parameters = self.get_node_parameters(node)
                for parameter in parameters:
                    node.add_parameter(parameter)
                    scene_items.append(parameter)

        return scene_items

    def get_node_parameters(self, node, types=None):
        """
        Get parameters (e.g. maps and meshes) for the specified node.
        Args:
            node (zBuilder node): zBuilder scene item
            types (list, optional): node types to return, e.g. map, mesh.
            If None return all types.

        Returns:
            list of zBuilder node parameters
        """
        # get the parameter info for a node in a dict format
        node_parameter_info = node.spawn_parameters()
        parameters = []
        if not types:
            types = node_parameter_info.keys()
        for parameter_type, parameter_args in node_parameter_info.items():
            for parameter_arg in parameter_args:
                if parameter_type in types:
                    parameter = self.parameter_factory(parameter_type, parameter_arg)
                    parameters.append(parameter)

        return parameters

    def parameter_factory(self, parameter_type, parameter_args):
        ''' This looks for zBuilder objects in sys.modules and instantiates
        desired one based on arguments.

        Args:
            type_ (str): The type of parameter to instantiate (map or mesh)
            names (str or list): The name of parameter to instantiate.
                This should be a node in the Maya scene, either a mesh or a map name.
                Currently sometimes parameter_names could be a list.
                It is a list when dealing with a map.
                The second element is the payload whereas the first is the name.

        Returns:
            object: zBuilder parameter object, either one created or
            an existing one that has already been created.
        '''
        # put association filter in a list if it isn't
        if not is_sequence(parameter_args):
            parameter_args = [parameter_args]

        for _, obj in inspect.getmembers(sys.modules['zBuilder.nodes']):
            if inspect.isclass(obj) and parameter_type == obj.type:
                scene_item_nodes = self.get_scene_items(type_filter=parameter_type)
                scene_item_names = [y.long_name for y in scene_item_nodes]

                # the first element in parameter_args is the name.
                parameter_name = parameter_args[0]
                try:
                    # There is an existing scene item for this item so lets just
                    # return that.
                    index = scene_item_names.index(parameter_name)
                    return scene_item_nodes[index]
                except ValueError:
                    # No scene item with given parameter_name,
                    # create one and return that.
                    return obj(*parameter_args, builder=self)

    def make_node_connections(self):
        """This makes connections between this node and any other node in scene_items.  The expectations
        is that this gets run after anytime the scene items get populated.
        """
        for item in self.get_scene_items():
            item.make_node_connections()

    def retrieve_from_scene(self, *args, **kwargs):
        """
        must create a method to inherit this class
        """
        selection = parse_maya_node_for_selection(args)
        for item in selection:
            b_solver = self.node_factory(item)
            self._extend_scene_items(b_solver)

        self.stats()

    def write(self, file_path, type_filter=None, invert_match=False):
        """
        Wraps 'write()' defined in serialize.py. This is used for backward compatibility.
        """
        logger.warning(
            'This method will be deprecated. Use write() defined in zBuilder.builders.serialize instead.'
        )
        import zBuilder.builders.serialize as serialize
        serialize.write(file_path, self, type_filter, invert_match)

    def retrieve_from_file(self, file_path):
        """
        Wraps 'read()' defined in serialize.py. This is used for backward compatibility.
        """
        logger.warning(
            'This method will be deprecated. Use read() defined in zBuilder.builders.serialize instead.'
        )
        import zBuilder.builders.serialize as serialize
        serialize.read(file_path, self)

    def stats(self):
        """
        Print scene item types and their counts.
        """
        node_types = [item.type for item in self.scene_items]
        type_counter = Counter(node_types)
        for k, v in type_counter.items():
            logger.info('{} {}'.format(k, v))

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
            #TODO: include parent and attachment: VFXACT-1113

    def print_(self, type_filter=None, name_filter=None):
        """
        Prints out basic information for each scene item in the Builder.  Information is all
        information that is stored in the __dict__.  Useful for trouble shooting.

        Args:
            type_filter (:obj:`list` or :obj:`str`): filter by scene_item type.
                Defaults to :obj:`None`
            name_filter (:obj:`list` or :obj:`str`): filter by scene_item name.
                Defaults to :obj:`None`
        """
        for item in self.get_scene_items(type_filter, name_filter, [], [], None, False):
            logger.debug(item)
        logger.debug('-' * 80)

    def get_scene_items(self,
                        type_filter=None,
                        name_filter=None,
                        name_regex=None,
                        association_filter=None,
                        association_regex=None,
                        invert_match=False):
        """
        Gets the scene items from builder for further inspection or modification.

        Args:
            type_filter (:obj:`str` or :obj:`list`, optional): filter by scene_item ``type``.
                Defaults to ``None``.
            name_filter (:obj:`str` or :obj:`list`, optional): filter by scene_item ``name``.
                Defaults to ``None``.
            name_regex (:obj:`str`): filter by scene_item name by regular expression.
                Defaults to ``None``.
            association_filter (:obj:`str` or :obj:`list`, optional): filter by scene_item ``association``.
                Defaults to ``None``.
            association_regex (:obj:`str`): filter by scene_item ``association`` by regular expression.
                Defaults to ``None``.
            invert_match (bool): Invert the sense of matching, to select non-matching items.
                Defaults to ``False``
        Returns:
            list: List of scene items.
        """
        # put type filter in a list if it isn't
        if not is_sequence(type_filter):
            type_filter = [type_filter] if type_filter else None
        if type_filter:
            assert all(is_string(t) for t in type_filter), "type filter requires string type"

        # put association filter in a list if it isn't
        if not is_sequence(association_filter):
            association_filter = [association_filter] if association_filter else None
        if association_filter:
            assert all(is_string(a)
                       for a in association_filter), "association filter requires string type"

        # put name filter in a list if it isn't
        if not is_sequence(name_filter):
            name_filter = [name_filter] if name_filter else None
        if name_filter:
            assert all(is_string(n) for n in name_filter), "name filter requires string type"

        # if no filters are used just return full list as it is faster
        if not type_filter and \
           not association_filter and \
           not name_filter and \
           not name_regex and \
           not association_regex:
            return self.scene_items

        type_set = set(type_filter) if type_filter else None
        name_set = set(name_filter) if name_filter else None
        association_set = set(association_filter) if association_filter else None

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

        return [item for item in self.scene_items if keep_me(item, invert_match)]

    def remove_scene_item(self, item_to_remove):
        """
        Removes a scene item from the builder while keeping order.
        Args:
            item_to_remove (:obj:`obj`): The item object to remove.
        """
        self.scene_items.remove(item_to_remove)

    def _extend_scene_items(self, new_scene_items):
        """
        Add a list of scene items to existing items.
        Any duplicates with existing scene items replace the existing item.
        Duplicates are identified by long name.

        Args:
            new_scene_items: List of objects derived from zBuilder.nodes.Base
        """
        # The order of items in self.scene_items is important,
        # so we must update existing items in place and append new items in the order given.
        # To easily update existing items, here's an index to lookup where they are by name.
        old_items = {item.long_name: index for index, item in enumerate(self.scene_items)}

        bad_index = -1
        for item in new_scene_items:
            index = old_items.get(item.long_name, bad_index)
            if index != bad_index:
                self.scene_items[index] = item
            else:
                self.scene_items.append(item)


# TODO: Move node registration and type introspection methods such as, find_class,
# node_factory, parameter_factory functions out of builder.py
def find_class(module, obj_type):
    """
    Given a module and a type returns class object. If no class objects are
    found it returns a DGNode class object.

    Args:
        module (:obj:`str`): The module to look for.
        obj_type (:obj:`str`): The type to look for.

    Returns:
        obj: class object.
    """
    # The parameters module is moved to zBuilder.nodes since version 2.1,
    # patch the module path to compatible old setups.
    major, minor, patch, _ = parse_version_info(__version__)
    if module == 'zBuilder.parameters' and (major, minor, patch) >= (2, 1, 0):
        module = 'zBuilder.nodes'

    for _, obj in inspect.getmembers(sys.modules[module]):
        if inspect.isclass(obj):
            if obj_type in obj.TYPES or obj_type == obj.type:
                return obj

    # if class object is not found lets return a DG node object
    from zBuilder.nodes.dg_node import DGNode
    return DGNode
