import json
import inspect
import sys
import datetime
import logging

logger = logging.getLogger(__name__)


class IO(object):

    def write(self, file_path,
              component_data=True,
              node_data=True):
        """
        writes data to disk in json format

        Args:
            node_data:
            component_data:
            file_path (str): file path to write to disk

        Raises:
            IOError: If not able to write file

        """

        data = self.get_json_data(
            component_data=component_data,
            node_data=node_data
        )
        try:
            with open(file_path, 'w') as outfile:
                json.dump(data, outfile, cls=BaseNodeEncoder,
                          sort_keys=True, indent=4, separators=(',', ': '))
        except IOError:
            logger.error("Error: can\'t find file or write data")
        else:
            for b_node in self.nodes:
                b_node.mobject = b_node.mobject
            self.stats()
            logger.info('Wrote File: {}'.format(file_path))

    def retrieve_from_file(self, filepath):
        """
        reads data from a file

        Args:
            filepath (str): filepath to read from disk

        Raises:
            IOError: If not able to read file
        """
        before = datetime.datetime.now()
        try:
            with open(filepath, 'rb') as handle:
                data = json.load(handle, object_hook=self.load_base_node)
                # data = json.load(handle)
                self.from_json_data(data)
        except IOError:
            logger.error("Error: can\'t find file or read data")
        else:
            self.stats()
            for b_node in self.nodes:
                b_node.mobject = b_node.mobject
            after = datetime.datetime.now()
            logger.info('Read File: {} in {}'.format(filepath, after - before))

    def get_json_data(self, node_data=True, component_data=True):
        """
        Utility function to define data stored in json
        """

        tmp = []

        if node_data:
            logger.info("writing node_data")
            tmp.append(self.__wrap_data(self.nodes, 'node_data'))
        if component_data:
            logger.info("writing component_data")
            tmp.append(self.__wrap_data(self.data, 'component_data'))
        logger.info("writing info")
        tmp.append(self.__wrap_data(self.info, 'info'))

        return tmp

    def from_json_data(self, data):
        """
        Gets data out of json serialization and assigns it to object
        """
        data = self.__check_data(data)

        for d in data:
            if d['d_type'] == 'node_data':
                self.nodes = d['data']
                logger.info("reading node_data. {} nodes".format(len(d['data'])))
            if d['d_type'] == 'component_data':
                self.data = d['data']
                logger.info("reading component_data. ")
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

    @staticmethod
    def __wrap_data(data, type_):
        """
        Utility wrapper to identify data.
        """
        wrapper = dict()
        wrapper['d_type'] = type_
        wrapper['data'] = data
        return wrapper

    def load_base_node(self, json_object):
        """
        Loads json objects into proper classes

        Args:
            json_object (obj): json obj to perform action on

        Returns:
            obj:  Result of operation
        """
        if '_class' in json_object:
            module_ = json_object['_class'][0]

            type_ = self.get_type_from_json_object(json_object)
            if 'zBuilder.data' in module_:
                object = find_class('zBuilder.data', type_)
            elif 'zBuilder.nodes' in module_:
                object = find_class('zBuilder.nodes', type_)

            b_node = object(deserialize=json_object, setup=self)
            return b_node
        else:
            return json_object

    @staticmethod
    def get_type_from_json_object(json_object):
        """
        backwards compatibility here (change class name)
        Args:
            json_object:

        Returns:

        """
        if 'TYPE' in json_object:
            type_ = json_object['TYPE']
        elif '_type' in json_object:
            type_ = json_object['_type']
            json_object['TYPE'] = type_
            json_object.pop('_type', None)
        else:
            type_ = json_object['_class'][1].lower()
        return type_


class BaseNodeEncoder(json.JSONEncoder):
    def default(self, obj):
        if hasattr(obj, '_class'):
            if hasattr(obj, 'serialize'):
                return obj.serialize()
            else:
                return obj.__dict__
        else:
            return super(BaseNodeEncoder, self).default(obj)


def find_class(module_, type_):
    """

    Args:
        module_:
        type_:

    Returns:

    """
    for name, obj in inspect.getmembers(
            sys.modules[module_]):
        if inspect.isclass(obj):

            if type_ == obj.TYPE:
                return obj
