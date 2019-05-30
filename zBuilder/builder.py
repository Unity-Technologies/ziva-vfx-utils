from zBuilder.bundle import Bundle
import zBuilder.zMaya as mz
import zBuilder.nodes
import zBuilder.parameters
import zBuilder.IO as io
import zBuilder.ui.reader as reader

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

    def log(self):
        self.root_node.log()

    def view(self):
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
                        item_list.append(obj(parent=parent,maya_node=node, builder=self))
                if type_ == obj.type:

                    objct = obj(parent=parent, maya_node=node, builder=self)
                    item_list.append(objct)
        if not item_list:
            item_list.append(zBuilder.nodes.DGNode(parent=parent, maya_node=node, builder=self))

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

    def parameter_factory(self, type_, names):
        ''' This looks for zBuilder objects in sys.modules and instantiates
        desired one based on arguments.
        
        Args:
            type_ (str): The type of parameter to instentiate (map or mesh)
            names (str): The name of parameter to instentiate.  This should be 
                a node in the maya scene.  Either a mesh or a map name.
        
        Returns:
            object: zBuilder parameter object
        '''

        # put association filter in a list if it isn't
        if not isinstance(names, list):
            names = [names]

        for name, obj in inspect.getmembers(sys.modules['zBuilder.parameters']):
            if inspect.isclass(obj):
                if type_ == obj.type:
                    scene_items = self.bundle.get_scene_items(type_filter=type_)
                    scene_items = [x.long_name for x in scene_items]
                    for name in names:
                        if name not in scene_items:
                            return obj(*names, builder=self)

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

        parameters = self.bundle.get_scene_items()
        for parameter in parameters:
            parameter.build(*args, **kwargs)

    # @time_this
    def retrieve_from_scene(self, *args, **kwargs):
        """
        must create a method to inherit this class
        """
        selection = mz.parse_maya_node_for_selection(args)
        for item in selection:
            b_solver = self.node_factory(item)
            self.bundle.extend_scene_items(b_solver)

        self.bundle.stats()

    def write(self, file_path, type_filter=list(), invert_match=False):
        """ Writes out the scene items to a json file given a file path.

        Args:
            file_path (str): The file path to write to disk.
            type_filter (list, optional): Types of scene items to write.
            invert_match (bool): Invert the sense of matching, to select non-matching items.
                Defaults to ``False``
        """

        json_data = self.__get_json_data(type_filter=type_filter,
                                         invert_match=invert_match)

        if io.dump_json(file_path, json_data):
            for parameter in self.bundle.scene_items:
                if hasattr(parameter, 'mobject'):
                    parameter.mobject = parameter.mobject
            self.bundle.stats()
            logger.info('Wrote File: {}'.format(file_path))

    def retrieve_from_file(self, file_path):
        """ Reads scene items from a given file.  The items get placed in the bundle.

        Args:
            file_path (:obj:`str`): The file path to read from disk.

        """

        before = datetime.datetime.now()

        json_data = io.load_json(file_path)
        self.__assign_json_data(json_data)
        self.__assign_setup()
        self.bundle.stats()
        for parameter in self.bundle.scene_items:
            if hasattr(parameter, 'mobject'):
                parameter.mobject = parameter.mobject
        after = datetime.datetime.now()

        logger.info('Read File: {} in {}'.format(file_path, after - before))

    def __assign_json_data(self, json_data):
        """ Gets data out of json serialization and assigns it to node collection
        object.

        Args:
            json_data: Data to assign to builder object.
        """
        data = io.check_data(json_data)
        for d in data:

            if d['d_type'] == 'node_data':
                self.bundle.extend_scene_items(d['data'])
                logger.info("reading parameters. {} nodes".format(len(d['data'])))
            if d['d_type'] == 'component_data':
                # if d['data' is a dictionary it is saved as pre 1.0.0 so lets
                if not isinstance(d['data'], list):
                    for k, v in d['data'].iteritems():
                        for k2 in d['data'][k]:
                            self.bundle.scene_items.append(d['data'][k][k2])
                else:
                    # saved as 1.0.0
                    self.components = d['data']

                # logger.info("reading component_data. ")
            if d['d_type'] == 'info':
                logger.info("reading info")
                self.info = d['data']

    def __get_json_data(self, type_filter=[], invert_match=False):
        """ Utility function to define data stored in json
        Args:
            type_filter (list, optional): Types of scene items to write.
            invert_match (bool): Invert the sense of matching, to select non-matching items.
                Defaults to ``False``
        Returns:
            list: List of items to save out.
        """

        tmp = []

        logger.info("writing Scene Items")
        tmp.append(io.wrap_data(self.bundle.get_scene_items(type_filter=type_filter, invert_match=invert_match), 'node_data'))
        logger.info("writing info")
        tmp.append(io.wrap_data(self.info, 'info'))

        return tmp

    def __assign_setup(self):
        """

        Returns:

        """
        for x in self.bundle:
            x.builder = self

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
            type_filter (:obj:`list` or :obj:`str`): filter by parameter type.
                Defaults to :obj:`list`
            name_filter (:obj:`list` or :obj:`str`): filter by parameter name.
                Defaults to :obj:`list`
        """
        self.bundle.print_(type_filter=type_filter, name_filter=name_filter)

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
        # self.get_scene_items.__doc__ = self.bundle.get_scene_items.__doc__

        return self.bundle.get_scene_items(type_filter=type_filter,
                                           name_filter=name_filter,
                                           name_regex=name_regex,
                                           association_filter=association_filter,
                                           association_regex=association_regex,
                                           invert_match=invert_match)


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

    raise StandardError('Cannot find class in zBuilder.builders')
