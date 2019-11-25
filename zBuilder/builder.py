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
        import maya.cmds as mc
        from zBuilder.nodes.base import Base

        self.root_node = Base()
        self.root_node.name = 'ROOT'

        self.info = dict()
        self.info['version'] = zBuilder.__version__
        self.info['current_time'] = time.strftime("%d/%m/%Y  %H:%M:%S")
        self.info['maya_version'] = mc.about(v=True)
        self.info['operating_system'] = mc.about(os=True)

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

        item_list = []
        for name, obj in inspect.getmembers(sys.modules['zBuilder.nodes']):
            if inspect.isclass(obj):
                if obj.TYPES:
                    if type_ in obj.TYPES:
                        obb = obj(parent=parent, builder=self)
                        obb.populate(maya_node=node)
                        item_list.append(obb)
                if type_ == obj.type:

                    objct = obj(parent=parent, builder=self)
                    objct.populate(maya_node=node)

                    item_list.append(objct)
        if not item_list:
            objct = zBuilder.nodes.DGNode(parent=parent, builder=self)
            objct.populate(maya_node=node)
            item_list.append(objct)

        if get_parameters:
            for obj__ in item_list:
                if hasattr(obj__, 'spawn_parameters'):
                    others = obj__.spawn_parameters()
                    for k, values in others.iteritems():
                        for v in values:
                            obj = self.parameter_factory(k, v)
                            if obj:
                                item_list.append(obj)

        return item_list

    def parameter_factory(self, parameter_type, parameter_names):
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
            object: zBuilder parameter object
        '''
        # put association filter in a list if it isn't
        if not isinstance(parameter_names, list):
            parameter_names = [parameter_names]

        for name, obj in inspect.getmembers(sys.modules['zBuilder.parameters']):
            if inspect.isclass(obj):
                if parameter_type == obj.type:
                    scene_items = self.bundle.get_scene_items(type_filter=parameter_type)
                    scene_items = [x.long_name for x in scene_items]
                    if any(x not in scene_items for x in parameter_names):
                        return obj(*parameter_names, builder=self)

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

    def retrieve_from_file(self, file_path):
        """ Reads scene items from a given file.  The items get placed in the bundle.

        Args:
            file_path (:obj:`str`): The file path to read from disk.

        """
        before = datetime.datetime.now()
        json_data = io.load_json(file_path)
        io.unpack_zbuilder_contents(self, json_data)
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

    def break_connection_to_scene(self):
        """Sets the mObject for all scene items to None.  This is useful if you want to break the 
        connection between the node and what is in the scene.
        """
        for item in self.get_scene_items(type_filter=['map', 'mesh'], invert_match=True):
            item.break_connection_to_scene()


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
