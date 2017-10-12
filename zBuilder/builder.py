from zBuilder.bundle import Bundle

import zBuilder.zMaya as mz
import zBuilder.components
import zBuilder.parameters
import zBuilder.IO as io
from functools import wraps
import datetime
import sys
import inspect
import logging

logger = logging.getLogger(__name__)


class Builder(object):
    """ The main class for using zBuilder.

    This inherits from nodeCollection which is a glorified list.
    """
    def __init__(self):
        # Bundle.__init__(self)
        self.bundle = Bundle()

    def parameter_factory(self, node):
        """Given a maya node, this checks objType and instantiats the proper
        zBuilder.node and populates it and returns it.

        Args:
            node (:obj:`str`): Name of maya node.

        Returns:
            obj: zBuilder node populated.
        """
        type_ = mz.get_type(node)
        for name, obj in inspect.getmembers(sys.modules['zBuilder.parameters']):
            if inspect.isclass(obj):
                if obj.TYPES:
                    if type_ in obj.TYPES:
                        return obj(node, setup=self)
                if type_ == obj.type:
                    return obj(node, setup=self)
        return zBuilder.parameters.BaseParameter(node, setup=self)

    def component_factory(self, *args, **kwargs):
        """ This instantiates and populates a zBuilder data node based on type.
        Since we can't check type against what is passed we need to pass type
        explicitly.  As of writing type is either map or mesh.
        Args:
            args: args get passed directly to node instantiation.
            type (:obj:`str`): Type of data node to instantiate.

        Returns:
            obj: zBuilder data node populated.
        """
        type_ = kwargs.get('type', True)

        for name, obj in inspect.getmembers(sys.modules['zBuilder.components']):
            if inspect.isclass(obj):
                if type_ == obj.type:
                    return obj(*args, setup=self)

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

        b_nodes = self.bundle.get_parameters()
        for b_node in b_nodes:
            b_node.build()

    # def apply(self, *args, **kwargs):
    #
    #     self.build(args, kwargs)
    #     logger.info('.apply() DEPRECATED.  Use .build() instead.')

    # @time_this
    def retrieve_from_scene(self, *args, **kwargs):
        """
        must create a method to inherit this class
        """
        selection = mz.parse_args_for_selection(args)
        for item in selection:
            b_solver = self.parameter_factory(item)
            self.bundle.add_parameter(b_solver)

        self.bundle.stats()

    def write(self, file_path, components=True, parameters=True):
        """ writes data to disk in json format.

        Args:
            file_path (str): The file path to write to disk.
            parameters (bool, optional): Optionally suppress writing out of node
                objects.  Defaults to ``True``.
            components (bool, optional): Optionally suppress writing out of
                data objects.  Defaults to ``True``.
        """

        json_data = self.__get_json_data(component_data=components,
                                         node_data=parameters)

        if io.dump_json(file_path, json_data):
            for b_node in self.bundle.parameters:
                b_node.mobject = b_node.mobject
            self.bundle.stats()
            logger.info('Wrote File: {}'.format(file_path))

    def retrieve_from_file(self, file_path):
        """ Reads data from a given file.  The data gets placed in the nodeCollection.

        Args:
            file_path (:obj:`str`): The file path to read from disk.

        """

        before = datetime.datetime.now()

        json_data = io.load_json(file_path)
        self.__assign_json_data(json_data)
        self.bundle.stats()
        for b_node in self.bundle.parameters:
            b_node.mobject = b_node.mobject
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
                self.parameters = d['data']
                logger.info("reading node_data. {} nodes".format(len(d['data'])))
            if d['d_type'] == 'component_data':
                # if d['data' is a dictionary it is saved as pre 1.0.0 so lets
                if not isinstance(d['data'], list):
                    for k, v in d['data'].iteritems():
                        for k2 in d['data'][k]:
                            self.bundle.components.append(d['data'][k][k2])
                else:
                    # saved as 1.0.0
                    self.components = d['data']

                logger.info("reading component_data. ")
            if d['d_type'] == 'info':
                logger.info("reading info")
                self.info = d['data']

    def __get_json_data(self, node_data=True, component_data=True):
        """ Utility function to define data stored in json
        Args:
            node_data (bool, optional): Optionally suppress storing node data.
            component_data (bool, optional): Optionally suppress storing
                component data.
        Returns:
            list: List of items to save out.
        """

        tmp = []

        if node_data:
            logger.info("writing parameters")
            tmp.append(io.wrap_data(self.bundle.parameters, 'node_data'))
        if component_data:
            logger.info("writing components")
            tmp.append(io.wrap_data(self.bundle.components, 'component_data'))
        logger.info("writing info")
        tmp.append(io.wrap_data(self.info, 'info'))

        return tmp
