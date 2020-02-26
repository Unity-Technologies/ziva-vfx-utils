from zBuilder.bundle import Bundle
import zBuilder.zMaya as mz
import zBuilder.nodes
import zBuilder.parameters
import zBuilder.IO as io

import copy
from functools import wraps
import datetime
import sys
import inspect
import logging
import time

logger = logging.getLogger(__name__)


class Builder(object):
    """ The main entry point for using zBuilder.

    """

    def __init__(self):
        self.bundle = Bundle()
        import zBuilder
        from maya import cmds
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
        try:
            import zBuilder.ui.reader as reader
        except ImportError:
            raise Exception("Ziva Scene Panel supported on Maya 2017+")

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
        type_ = mz.get_type(node)
        if not parent:
            parent = self.root_node

        scene_items = []
        for name, obj in inspect.getmembers(sys.modules['zBuilder.nodes']):
            if inspect.isclass(obj):
                if type_ in obj.TYPES or type_ == obj.type:
                    obb = obj(parent=parent, builder=self)
                    obb.populate(maya_node=node)
                    scene_items.append(obb)
        if not scene_items:
            objct = zBuilder.nodes.DGNode(parent=parent, builder=self)
            objct.populate(maya_node=node)
            scene_items.append(objct)

        if get_parameters:
            for node in scene_items:
                if hasattr(node, 'spawn_parameters'):
                    parameters = self.get_parameters_from_node(node)
                    for parameter in parameters:
                        node.add_parameter(parameter)
                        scene_items.append(parameter)

        return scene_items

    def get_parameters_from_node(self, node, types=[]):
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
        for parameter_type, parameter_args in node_parameter_info.iteritems():
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
        if not io.is_sequence(parameter_args):
            parameter_args = [parameter_args]

        for name, obj in inspect.getmembers(sys.modules['zBuilder.parameters']):
            if inspect.isclass(obj) and parameter_type == obj.type:
                scene_item_nodes = self.bundle.get_scene_items(type_filter=parameter_type)
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

    @staticmethod
    def time_this(original_function):
        """
        A decorator to time functions.
        """

        @wraps(original_function)
        def new_function(*args, **kwargs):
            before = datetime.datetime.now()
            x = original_function(*args, **kwargs)
            after = datetime.datetime.now()
            logger.info("Finished: ---Elapsed Time = {0}".format(after - before))
            return x

        return new_function

    def build(self, *args, **kwargs):
        logger.info('Building....')

        for scene_item in self.bundle.get_scene_items():
            scene_item.build(*args, **kwargs)

    def retrieve_from_scene(self, *args, **kwargs):
        """
        must create a method to inherit this class
        """
        selection = mz.parse_maya_node_for_selection(args)
        for item in selection:
            b_solver = self.node_factory(item)
            self.bundle.extend_scene_items(b_solver)

        self.bundle.stats()

    def write(self, file_path, type_filter=[], invert_match=False):
        """ Writes out the scene items to a json file given a file path.

        Args:
            file_path (str): The file path to write to disk.
            type_filter (list, optional): Types of scene items to write.
            invert_match (bool): Invert the sense of matching, to select non-matching items.
                Defaults to ``False``
        """
        json_data = io.pack_zbuilder_contents(self,
                                              type_filter=type_filter,
                                              invert_match=invert_match)
        if io.dump_json(file_path, json_data):
            self.bundle.stats()
            logger.info('Wrote File: %s' % file_path)

        # loop through the scene items
        for scene_item in self.get_scene_items():
            # loop through scene item attributes as defined by each scene item
            for attr in scene_item.SCENE_ITEM_ATTRIBUTES:
                if attr in scene_item.__dict__:
                    if scene_item.__dict__[attr]:
                        restored = restore_scene_items_from_string(scene_item.__dict__[attr], self)
                        scene_item.__dict__[attr] = restored

    def retrieve_from_file(self, file_path):
        """ Reads scene items from a given file.  The items get placed in the bundle.

        Args:
            file_path (:obj:`str`): The file path to read from disk.

        """
        before = datetime.datetime.now()
        json_data = io.load_json(file_path)
        io.unpack_zbuilder_contents(self, json_data)

        # The json data is now loaded.  We need to go through the defined scene item attributes
        # (The attributes that hold un-serializable scene items) and replace the string name
        # with the proper scene item.

        # loop through the scene items
        for scene_item in self.get_scene_items():
            # loop through scene item attributes as defined by each scene item
            for attr in scene_item.SCENE_ITEM_ATTRIBUTES:
                if attr in scene_item.__dict__:
                    if scene_item.__dict__[attr]:
                        restored = restore_scene_items_from_string(scene_item.__dict__[attr], self)
                        scene_item.__dict__[attr] = restored

        self.bundle.stats()
        after = datetime.datetime.now()
        logger.info('Read File: {} in {}'.format(file_path, after - before))

    def stats(self):
        """
        Prints out basic information in Maya script editor.  Information is scene item types and counts.
        """
        self.bundle.stats()

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
        self.bundle.print_(type_filter=type_filter, name_filter=name_filter)

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

        return self.bundle.get_scene_items(type_filter=type_filter,
                                           name_filter=name_filter,
                                           name_regex=name_regex,
                                           association_filter=association_filter,
                                           association_regex=association_regex,
                                           invert_match=invert_match)


def restore_scene_items_from_string(item, builder):
    if io.is_sequence(item):
        if item:
            item = builder.get_scene_items(name_filter=item)
    elif isinstance(item, dict):
        for parm in item:
            item[parm] = builder.get_scene_items(name_filter=item[parm])
    else:
        item = builder.get_scene_items(name_filter=item)
        if item:
            item = item[0]
    return item


def builder_factory(class_name):
    """A factory node to return the correct Builder given class name.

    If it cannot find a class it uses the base Builder class.

    Args:
        type_ ([:obj:`str`]):  The class name to search for.

    Returns:
        [:obj:`obj`]: Builder object.

    Raises:
        [Error]: if class_name cannot be found.
    """

    for name, obj in inspect.getmembers(sys.modules['zBuilder.builders']):
        if inspect.isclass(obj):
            if class_name == obj.__name__:
                return obj()

    raise Exception('Cannot find class in zBuilder.builders')
