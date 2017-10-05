import json
import inspect
import sys
import datetime
import logging

logger = logging.getLogger(__name__)


class IO(object):
    """Mixin class to deal with reading and writing files.  Meant to be
    inherited in main.

    """

    def write(self, file_path,
              component_data=True,
              node_data=True):
        """ writes data to disk in json format.

        Args:
            file_path (str): The file path to write to disk.
            node_data (bool, optional): Optionally suppress writing out of node
                objects.  Defaults to ``True``.
            component_data (bool, optional): Optionally suppress writing out of
                data objects.  Defaults to ``True``.
        Raises:
            IOError: If not able to write file.
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

    def retrieve_from_file(self, file_path):
        """ Reads data from a given file.

        Args:
            file_path (:obj:`str`): The file path to read from disk.

        Raises:
            IOError: If not able to read file.
        """
        before = datetime.datetime.now()
        try:
            with open(file_path, 'rb') as handle:
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
            logger.info('Read File: {} in {}'.format(file_path, after - before))

    def get_json_data(self, node_data=True, component_data=True):
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
            logger.info("writing node_data")
            tmp.append(self.__wrap_data(self.nodes, 'node_data'))
        if component_data:
            logger.info("writing component_data")
            tmp.append(self.__wrap_data(self.data, 'component_data'))
        logger.info("writing info")
        tmp.append(self.__wrap_data(self.info, 'info'))

        return tmp

    def from_json_data(self, data):
        """ Gets data out of json serialization and assigns it to node collection
        object.

        Args:
            data: Data to check.
        """
        data = self.__check_data(data)
        for d in data:

            if d['d_type'] == 'node_data':
                self.nodes = d['data']
                logger.info("reading node_data. {} nodes".format(len(d['data'])))
            if d['d_type'] == 'component_data':
                # if d['data' is a dictionary it is saved as pre 1.0.0 so lets
                if not isinstance(d['data'], list):
                    for k, v in d['data'].iteritems():
                        for k2 in d['data'][k]:
                            self.data.append(d['data'][k][k2])
                else:
                    # saved as 1.0.0
                    self.data = d['data']

                logger.info("reading component_data. ")
            if d['d_type'] == 'info':
                logger.info("reading info")
                self.info = d['data']

    def __check_data(self, data):
        """ Utility to check data format.  Used to check if data is wrapped in
        dictionary.  If it isn't it wraps it.  Used to deal with older zBuilder
        files.

        Args:
            data: Data to check.

        Returns:
            Result of operation.
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
        """ Utility wrapper to identify data.

        Args:
            type_ (:obj:`str`): The type of data it is.
        """
        wrapper = dict()
        wrapper['d_type'] = type_
        wrapper['data'] = data
        return wrapper

    def load_base_node(self, json_object):
        """
        Loads json objects into proper classes.

        Args:
            json_object (obj): json obj to perform action on

        Returns:
            obj:  Result of operation
        """
        self.update_json(json_object)

        if '_class' in json_object:
            module_ = json_object['_class'][0]

            type_ = json_object['TYPE']
            if 'zBuilder.data' in module_:
                obj = find_class('zBuilder.data', type_)
            elif 'zBuilder.nodes' in module_:
                obj = find_class('zBuilder.nodes', type_)

            b_node = obj(deserialize=json_object, setup=self)
            return b_node
        else:
            return json_object

    @staticmethod
    def update_json(json_object):
        """
        This takes the json_object and updates it to work with 1.0.0

        Returns:
            modified json_object
        """

        # replacing key attribute names with value.  A simple swap.
        replace_me = dict()
        replace_me['_type'] = 'TYPE'
        replace_me['_attrs'] = 'attrs'
        replace_me['_value'] = 'value'
        replace_me['__collection'] = 'nodes'
        replace_me['_zFiber'] = 'fiber'

        if '_class' in json_object:

            for key, value in replace_me.iteritems():
                if key in json_object:
                    json_object[value] = json_object[key]
                    json_object.pop(key, None)
                else:
                    # print 'NOPE', value, json_object.keys()
                    # maps and meshes didn't have a type.  lets make one.
                    if value == 'TYPE':
                        json_object[value] = json_object['_class'][1].lower()

        return json_object


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
    """ Given a module and a type returns class object.

    Args:
        module_ (:obj:`str`): The module to look for.
        type_ (:obj:`str`): The type to look for.

    Returns:
        obj: class object.
    """
    for name, obj in inspect.getmembers(
            sys.modules[module_]):
        if inspect.isclass(obj):

            if type_ == obj.TYPE:
                return obj
