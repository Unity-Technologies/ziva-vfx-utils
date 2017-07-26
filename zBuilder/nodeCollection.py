import json
import maya.cmds as mc
import re

import importlib
import time
import datetime
import logging

logger = logging.getLogger(__name__)


class NodeCollection(object):
    # __metaclass__ = abc.ABCMeta
    '''
    This is an object that holds the node data in a list
    '''

    def __init__(self):
        import zBuilder

        self.__collection = []
        self.data = {}
        self.info = {}
        self.info['version'] = zBuilder.__version__
        self.info['current_time'] = time.strftime("%d/%m/%Y  %H:%M:%S")
        self.info['maya_version'] = mc.about(v=True)
        self.info['operating_system'] = mc.about(os=True)

    def print_(self, type_filter=None, name_filter=None, component_data=True):

        '''
        print info on each node

        Args:
            type_filter (str): filter by node type.  Defaults to None
            name_filter (str): filter by node name. Defaults to None
            component_data (bool): prints name of data stored.  Defaults to False

        '''

        for node in self.get_nodes(type_filter=type_filter,
                                   name_filter=name_filter):
            node.print_()
        print '----------------------------------------------------------------'
        for key in self.data:
            print 'Component Data - {}: {}'.format(key, self.data[key].keys())

    def compare(self, type_filter=None, name_filter=None):

        '''
        print info on each node

        Args:
            type_filter (str): filter by node type.  Defaults to **None**
            name_filter (str): filter by node name. Defaults to **None**
            print_data (bool): prints name of data stored.  Defaults to **False**

        '''

        for node in self.get_nodes(type_filter=type_filter,
                                   name_filter=name_filter):
            node.compare()

    def stats(self, type_filter=None):
        '''
        prints out basic stats on data

        Args:
            type_filter (str): filter by node type.  Defaults to None
        '''
        tmp = {}
        for i, d in enumerate(self.get_nodes()):
            t = d.get_type()
            if type_filter:
                if type_filter == t:
                    if not t in tmp:
                        tmp[t] = []
                    if type_filter not in tmp:
                        tmp[type_filter] = []
                    tmp[type_filter].append(d)
            else:
                if not t in tmp:
                    tmp[t] = []
                tmp[t].append(d)

        for key in tmp:
            logger.info('{} {}'.format(key, len(tmp[key])))

    def add_data(self, key, name, data=None):
        '''
        appends a mesh to the mesh list

        Args:
            key (str): places data in this key in dict.
            name (str): name of data to place.
        '''
        if not key in self.data:
            self.data[key] = {}

        if not self.get_data_by_key_name(key, name):
            self.data[key][name] = data
            # logger.info("adding data type: {}  name: {}".format(key,name) )

    def get_data_by_key_name(self, key, name):
        '''
        Gets data given 'key'

        Args:
            key (str): the key to get data from.
            name (str): name of the data.

        Returns:
            obj: Object of data.

        Example:
            
            >>> get_data_by_key_name('mesh','l_bicepMuscle')
        '''
        if self.data.get(key):
            return self.data[key].get(name, None)
        else:
            return None

    def get_data_by_key(self, key):
        '''
        Gets all data for given 'key'

        args:
            key (str): the key to get data from

        returns:
            list: of data objs

        Example:
           get_data_by_key('mesh')
        '''
        return self.data.get(key, None)

    def add_node(self, node):
        '''
        appends a node to the node list

        Args:
            node (obj): the node obj to append to collection list.
        '''
        self.__collection.append(node)

    def get_nodes(self, type_filter=None, name_filter=None):
        '''
        get nodes in data object

        Args:
            type_filter (str): filter by node type.  Defaults to **None**
            name_filter (str): filter by node name.  Defaults to **None**

        Returns:
            [] of nodes
        '''
        items = []
        if not type_filter:
            return self.__collection
        else:
            for i, node in enumerate(self.__collection):
                if node.get_type() == type_filter:

                    if name_filter:
                        if not isinstance(name_filter, (list, tuple)):
                            name_filter = name_filter.split(' ')
                        if not set(name_filter).isdisjoint(
                                node.get_association()):
                            items.append(node)
                    else:
                        items.append(node)
        return items

    def get_node_by_name(self, name):
        """
        utility function to get node by name.

        Args:
            name (str): name of node.

        Returns:
            builder node (obj)
        """
        for node in self.__collection:
            if node.get_name() == name:
                return node

    def set_nodes(self, nodes):
        """
        Args:
            nodes (list): the nodes to replace the collection with
        """
        self.__collection = nodes

    def string_replace(self, search, replace):
        '''
        searches and replaces with regular expressions items in data

        Args:
            search (str): what to search for
            replace (str): what to replace it with

        Example:
            replace `r_` at front of item with `l_`:

            >>> z.string_replace('^r_','l_')

            replace `_r` at end of line with `_l`:

            >>> z.string_replace('_r$','_l')
        '''
        # print 'SEARCh',search
        # print 'REPLACE',replace
        for node in self.get_nodes():
            node.string_replace(search, replace)

        # deal with the data search and replacing
        for key in self.data:

            # replace the key names in data
            self.data[key] = replace_dict_keys(search, replace, self.data[key])

            # run search and replace on individual items
            for item in self.data[key]:
                self.data[key][item].string_replace(search, replace)

    def write(self, filepath,
              component_data=True,
              node_data=True):
        '''
        writes data to disk in json format

        Args:
            filepath (str): filepath to write to disk

        Raises:
            IOError: If not able to write file

        '''
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
            logger.info('Wrote File: {}'.format(filepath))

    def retrieve_from_file(self, filepath):
        '''
        reads data from a file

        Args:
            filepath (str): filepath to read from disk

        Raises:
            IOError: If not able to read file
        '''
        try:
            with open(filepath, 'rb') as handle:
                data = json.load(handle, object_hook=load_base_node)
                self.from_json_data(data)
        except IOError:
            print "Error: can\'t find file or read data"
        else:
            logger.info('Read File: {}'.format(filepath))

    def get_json_data(self, node_data=True, component_data=True):
        '''
        Utility function to define data stored in json
        '''
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
        '''
        Gets data out of json serialization
        '''
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
        '''
        Utility to check data format.
        '''
        if 'd_type' in data[0]:
            return data
        else:
            tmp = []
            tmp.append(self.__wrap_data(data[0], 'node_data'))
            tmp.append(self.__wrap_data(data[1], 'component_data'))
            if len(data) == 3:
                tmp.append(self.__wrap_data(data[2], 'info'))
            return tmp

    def __wrap_data(self, data, type_):
        '''
        Utility wrapper to identify data.
        '''
        wrapper = {}
        wrapper['d_type'] = type_
        wrapper['data'] = data
        return wrapper

    # @abc.abstractmethod
    def apply(self, *args, **kwargs):
        '''
        must create a method to inherit this class
        '''
        pass

    # @abc.abstractmethod
    def retrieve_from_scene(self, *args, **kwargs):
        '''
        must create a method to inherit this class
        '''
        pass


def replace_dict_keys(search, replace, dictionary):
    '''
    Does a search and replace on dictionary keys

    Args:
        search (str): search term
        replace (str): replace term
        dictionary (dict): the dictionary to do search on

    Returns:
        dict: result of search and replace
    '''
    tmp = {}
    for key in dictionary:
        new = replace_longname(search, replace, key)
        tmp[new] = dictionary[key]

    return tmp


def time_this(original_function):
    def new_function(*args, **kwargs):
        before = datetime.datetime.now()
        x = original_function(*args, **kwargs)
        after = datetime.datetime.now()
        logger.info("Finished: ---Elapsed Time = {0}".format(after - before))
        return x

    return new_function


class BaseNodeEncoder(json.JSONEncoder):
    def default(self, obj):
        if hasattr(obj, '_class'):
            return obj.__dict__
        else:
            return super(BaseNodeEncoder, self).default(obj)


def load_base_node(json_object):
    '''
    Loads json objects into proper classes

    Args:
        json_object (obj): json obj to perform action on

    Returns:
        obj:  Result of operation
    '''
    if '_class' in json_object:
        module = json_object['_class'][0]
        name = json_object['_class'][1]

        node = str_to_class(module, name)
        node.__dict__ = json_object
        return node

    else:
        return json_object


def replace_longname(search, replace, longName):
    '''
    does a search and replace on a long name.  It splits it up by ('|') then
    performs it on each piece

    Args:
        search (str): search term
        replace (str): replace term
        longName (str): the long name to perform action on

    returns:
        str: result of search and replace
    '''
    items = longName.split('|')
    newName = ''
    for i in items:
        if i:
            i = re.sub(search, replace, i)
            if '|' in longName:
                newName += '|' + i
            else:
                newName += i

    if newName != longName:
        logger.info('replacing name: {}  {}'.format(longName, newName))

    return newName


def str_to_class(module, name):
    '''
    Given module and name instantiantes a class

    Args:
        module (str): module
        name (str): the class name

    returns:
        obj: class object
    '''

    if module == 'zBuilder.data.map':
        module = 'zBuilder.data.maps'

    i = importlib.import_module(module)
    MyClass = getattr(i, name)
    instance = MyClass()
    return instance
