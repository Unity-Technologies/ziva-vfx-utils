from zBuilder.nodeCollection import NodeCollection
import zBuilder.nodes
import zBuilder.zMaya as mz
from zBuilder.data import Map
from zBuilder.data import Mesh

from functools import wraps
import datetime
import sys
import inspect
import logging

logger = logging.getLogger(__name__)


class Builder(NodeCollection):
    def __init__(self):
        NodeCollection.__init__(self)

    @staticmethod
    def node_factory(node):
        """

        Args:
            node:

        Returns:

        """
        type_ = mz.get_type(node)
        for name, obj in inspect.getmembers(sys.modules['zBuilder.nodes']):
            if inspect.isclass(obj):
                if type_ == obj().get_type():
                    return obj().create(node)

    @staticmethod
    def component_factory(*args):
        """

        Args:
            *args:

        Returns:

        """
        type_ = args[0]
        for name, obj in inspect.getmembers(sys.modules['zBuilder.data']):
            if inspect.isclass(obj):
                if type_ == obj().get_type():
                    return obj(*args[1:])

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

    # TODO name of this method is lame.
    def store_maps(self):
        for node in self.get_nodes():
            map_names = node.get_maps()
            mesh_names = node.get_association(long_name=True)
            if map_names and mesh_names:
                for map_name, mesh_name in zip(map_names, mesh_names):
                    # TODO data_factory?????? For all types
                    map_data_object = self.component_factory('map', map_name, mesh_name)
                    self.add_data(map_data_object)
                    logger.info('Retrieving Data : {}'.format(map_data_object))

    def store_mesh(self):
        for node in self.get_nodes():
            map_names = node.get_maps()
            mesh_names = node.get_association(long_name=True)
            if map_names and mesh_names:
                for map_name, mesh_name in zip(map_names, mesh_names):
                    if not self.get_data_by_key_name('mesh', mesh_name):
                        mesh_data_object = self.component_factory('mesh', mesh_name)
                        self.add_data(mesh_data_object)
                        logger.info('Retrieving Data : {}'.format(mesh_data_object))
