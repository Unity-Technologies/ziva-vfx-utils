import json

import maya.cmds as mc
import zBuilder.zMaya as mz

import importlib
import time

import logging

logger = logging.getLogger(__name__)


class IO(object):

    def write(self, filepath,
              component_data=True,
              node_data=True):
        """
        writes data to disk in json format

        Args:
            node_data:
            component_data:
            filepath (str): filepath to write to disk

        Raises:
            IOError: If not able to write file

        """

        data = self.get_json_data(
            component_data=component_data,
            node_data=node_data
        )
        try:
            with open(filepath, 'w') as outfile:
                json.dump(data, outfile, cls=BaseNodeEncoder,
                          sort_keys=True, indent=4, separators=(',', ': '))
        except IOError:
            print "Error: can\'t find file or write data"
        else:
            for b_node in self.get_nodes():
                b_node.set_mobject(b_node.get_mobject())
            self.stats()
            logger.info('Wrote File: {}'.format(filepath))

    def retrieve_from_file(self, filepath):
        """
        reads data from a file

        Args:
            filepath (str): filepath to read from disk

        Raises:
            IOError: If not able to read file
        """
        try:
            with open(filepath, 'rb') as handle:
                data = json.load(handle, object_hook=load_base_node)

                self.from_json_data(data)
        except IOError:
            print "Error: can\'t find file or read data"
        else:
            self.stats()
            for b_node in self.get_nodes():
                b_node.set_mobject(b_node.get_mobject())
                b_node.set_data(self.get_data())

            logger.info('Read File: {}'.format(filepath))

    def get_json_data(self, node_data=True, component_data=True):
        """
        Utility function to define data stored in json
        """

        tmp = []

        if node_data:
            logger.info("writing node_data")
            tmp.append(self.__wrap_data(self.get_nodes(), 'node_data'))
        if component_data:
            logger.info("writing component_data")
            tmp.append(self.__wrap_data(self.data, 'component_data'))
        logger.info("writing info")
        tmp.append(self.__wrap_data(self.info, 'info'))

        return tmp

    def from_json_data(self, data):
        """
        Gets data out of json serialization
        """
        data = self.__check_data(data)

        for d in data:
            if d['d_type'] == 'node_data':
                logger.info("reading node_data")
                self.set_nodes(d['data'])
            if d['d_type'] == 'component_data':
                logger.info("reading component_data")
                self.data = d['data']
            if d['d_type'] == 'info':
                logger.info("reading info")
                self.info = d['data']

    def __check_data(self, data):
        """
        Utility to check data format.
        """
        if 'd_type' in data[0]:
            return data
        else:
            tmp = list()
            tmp.append(self.__wrap_data(data[0], 'node_data'))
            tmp.append(self.__wrap_data(data[1], 'component_data'))
            if len(data) == 3:
                tmp.append(self.__wrap_data(data[2], 'info'))
            return tmp

    def __wrap_data(self, data, type_):
        """
        Utility wrapper to identify data.
        """
        wrapper = dict()
        wrapper['d_type'] = type_
        wrapper['data'] = data
        return wrapper


class BaseNodeEncoder(json.JSONEncoder):
    def default(self, obj):
        if hasattr(obj, '_class'):
            if hasattr(obj, 'serialize'):
                return obj.serialize()
            else:
                return obj.__dict__
        else:
            return super(BaseNodeEncoder, self).default(obj)


def load_base_node(json_object):
    """
    Loads json objects into proper classes

    Args:
        json_object (obj): json obj to perform action on

    Returns:
        obj:  Result of operation
    """
    if '_class' in json_object:
        module_ = json_object['_class'][0]
        name = json_object['_class'][1]

        # TODO this
        node = str_to_class(module_, name)

        if hasattr(node, 'deserialize'):
            node.deserialize(json_object)

        else:
            node.__dict__ = json_object

        return node

    else:
        return json_object


def str_to_class(module_, name):
    """
    Given module and name instantiates a class

    Args:
        module_ (str): module
        name (str): the class name

    returns:
        obj: class object
    """

    if module_ == 'zBuilder.data.map':
        module_ = 'zBuilder.data.maps'

    i = importlib.import_module(module_)
    my_class = getattr(i, name)
    instance = my_class()
    return instance

