from zBuilder.bundle import Bundle
from zBuilder.commonUtils import is_sequence, is_string, time_this
from zBuilder.mayaUtils import get_type, parse_maya_node_for_selection
from maya import cmds
import inspect
import json
import logging
import sys
import time

logger = logging.getLogger(__name__)


class Builder(object):
    """ The main entry point for using zBuilder.

    """
    def __init__(self):
        self.bundle = Bundle()
        import zBuilder
        from zBuilder.nodes.base import Base
        self.root_node = Base()
        self.root_node.name = 'ROOT'

        self.info = dict()
        self.info['version'] = zBuilder.__version__
        self.info['current_time'] = time.strftime("%d/%m/%Y  %H:%M:%S")
        self.info['maya_version'] = cmds.about(v=True)
        self.info['operating_system'] = cmds.about(os=True)


    def __eq__(self, other):
        """ Compares the builders.
        """
        return type(other) == type(self) and self.bundle == other.bundle


    def __ne__(self, other):
        """ Define a non-equality test
        """
        return not self == other


    def log(self):
        self.root_node.log()


    def view(self):
        import zBuilder.ui.reader as reader
        reader.view(root_node=self.root_node)


    def node_factory(self, node, parent=None, get_parameters=True):
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
        obj = find_class('zBuilder.nodes', type_)
        obb = obj(parent=parent, builder=self)
        obb.populate(maya_node=node)
        scene_items.append(obb)

        if get_parameters:
            for node in scene_items:
                if hasattr(node, 'spawn_parameters'):
                    parameters = self.get_node_parameters(node)
                    for parameter in parameters:
                        node.add_parameter(parameter)
                        scene_items.append(parameter)

        return scene_items


    def get_node_parameters(self, node, types=[]):
        """
        Get parameters (e.g. maps and meshes) for the specified node.
        Args:
            node (zBuilder node): zBuilder scene item
            types (list): node types to return, e.g. map, mesh. If empty return all types.

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
            type_ (str): The type of parameter to instentiate (map or mesh)
            names (str or list): The name of parameter to instentiate.  This should be 
                a node in the maya scene.  Either a mesh or a map name.

                Currently sometimes parameter_names could be a list.  It is a list
                when dealing with a map.  The second element is the payload 
                whereas the first is the name.
        
        Returns:
            object: zBuilder parameter object, either one created or an existing one that has 
            already been created.
        '''
        # put association filter in a list if it isn't
        if not is_sequence(parameter_args):
            parameter_args = [parameter_args]

        import zBuilder.parameters
        for _, obj in inspect.getmembers(sys.modules['zBuilder.parameters']):
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
                    # When valueerror there is no exisitng scene item with that name
                    # so lets create one and return that.
                    return obj(*parameter_args, builder=self)


    def make_node_connections(self):
        """This makes connections between this node and any other node in scene_items.  The expectations
        is that this gets run after anytime the scene items get populated.
        """
        for item in self.get_scene_items():
            item.make_node_connections()


    def build(self, *args, **kwargs):
        logger.info('Building....')

        for scene_item in self.get_scene_items():
            scene_item.build(*args, **kwargs)


    def retrieve_from_scene(self, *args, **kwargs):
        """
        must create a method to inherit this class
        """
        selection = parse_maya_node_for_selection(args)
        for item in selection:
            b_solver = self.node_factory(item)
            self.bundle.extend_scene_items(b_solver)

        self.stats()


    @time_this
    def write(self, file_path, type_filter=[], invert_match=False):
        """ Writes out the scene items to a json file given a file path.

        Args:
            file_path (str): The file path to write to disk.
            type_filter (list, optional): Types of scene items to write.
            invert_match (bool): Invert the sense of matching, to select non-matching items.
                Defaults to ``False``
        """

        from zBuilder.IO import pack_zbuilder_contents, BaseNodeEncoder
        json_data = pack_zbuilder_contents(self, type_filter, invert_match)
        with open(file_path, 'w') as outfile:
            json.dump(json_data, outfile, cls=BaseNodeEncoder, sort_keys=True, indent=4, separators=(',', ': '))

        self.stats()
        logger.info('Wrote File: %s' % file_path)

        # loop through the scene items
        for scene_item in self.get_scene_items():
            # loop through scene item attributes as defined by each scene item
            for attr in scene_item.SCENE_ITEM_ATTRIBUTES:
                if attr in scene_item.__dict__:
                    if scene_item.__dict__[attr]:
                        restored = self.restore_scene_items_from_string(scene_item.__dict__[attr])
                        scene_item.__dict__[attr] = restored


    @time_this
    def retrieve_from_file(self, file_path):
        """ Reads scene items from a given file.  The items get placed in the bundle.

        Args:
            file_path (:obj:`str`): The file path to read from disk.

        """

        from zBuilder.IO import load_base_node, unpack_zbuilder_contents
        with open(file_path, 'rb') as handle:
            json_data = json.load(handle, object_hook=load_base_node)
            unpack_zbuilder_contents(self, json_data)

        # The json data is now loaded.  We need to go through the defined scene item attributes
        # (The attributes that hold un-serializable scene items) and replace the string name
        # with the proper scene item.

        # loop through the scene items
        for scene_item in self.get_scene_items():
            # loop through scene item attributes as defined by each scene item
            for attr in scene_item.SCENE_ITEM_ATTRIBUTES:
                if attr in scene_item.__dict__:
                    if scene_item.__dict__[attr]:
                        restored = self.restore_scene_items_from_string(scene_item.__dict__[attr])
                        scene_item.__dict__[attr] = restored

        self.stats()


    def stats(self):
        """
        Prints out basic information in Maya script editor.  Information is scene item types and counts.
        """
        self.bundle.stats(None)


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
        self.bundle.string_replace(search, replace)


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
        self.bundle.print_(type_filter, name_filter)


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
        # put type filter in a list if it isn't
        if not is_sequence(type_filter):
            type_filter = [type_filter]
        if type_filter:
            assert all(is_string(t) for t in type_filter), "type filter requires string type"

        # put association filter in a list if it isn't
        if not is_sequence(association_filter):
            association_filter = [association_filter]
        if association_filter:
            assert all(is_string(a) for a in association_filter), "association filter requires string type"

        # put name filter in a list if it isn't
        if not is_sequence(name_filter):
            name_filter = [name_filter]
        if name_filter:
            assert all(is_string(n) for n in name_filter), "name filter requires string type"

        return self.bundle.get_scene_items(type_filter,
                                           name_filter,
                                           name_regex,
                                           association_filter,
                                           association_regex,
                                           invert_match)


    def restore_scene_items_from_string(self, item):
        if is_sequence(item):
            if item:
                item = self.get_scene_items(name_filter=item)
        elif isinstance(item, dict):
            for parm in item:
                item[parm] = self.get_scene_items(name_filter=item[parm])
        else:
            item = self.get_scene_items(name_filter=item)
            if item:
                item = item[0]
        return item


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
    for _, obj in inspect.getmembers(sys.modules[module]):
        if inspect.isclass(obj):
            if obj_type in obj.TYPES or obj_type == obj.type:
                return obj

    # if class object is not found lets return a DG node object
    from zBuilder.nodes.dg_node import DGNode
    return DGNode


def get_node_types_with_maps():
    """
    This searches through the modules for existing node type objects and returns 
    the ones that have maps associated with it.  Useful for performing actions on 
    node types with maps.  MAP_LIST is a class attr so it is not being instantiated here.
    """
    returns = []
    for _, obj in inspect.getmembers(sys.modules['zBuilder.nodes']):
        if inspect.isclass(obj):
            if obj.MAP_LIST:
                returns.append(obj.type)
    return returns
