import json
from nodes.base import BaseNode
import zBuilder.data.mesh as mesh
import maya.cmds as mc
import abc
import re
import sys
import os.path
import importlib
import time
import datetime 

class NodeCollection(object):
    __metaclass__ = abc.ABCMeta
    '''
    This is an object that holds the node data in a list
    '''
    def __init__(self):
        self.collection = []
        self.data = {} #: DATTTTA
        self.info = {}
        self.info['data_version'] = .1
        self.info['current_time'] = time.strftime("%d/%m/%Y  %H:%M:%S")
        self.info['maya_version'] = mc.about(v=True)
        self.info['operating_system'] = mc.about(os=True)




    def print_(self,type_filter=None,node_filter=None,print_data=False):

        '''
        print info on each node

        Args:
            type_filter (str): filter by node type.  Defaults to None
            node_filter (str): filter by node name. Defaults to None
            print_data (bool): prints name of data stored.  Defaults to False

        '''

        for node in self.get_nodes(type_filter=type_filter,node_filter=node_filter):

            node.print_()

        if print_data: 
            print self.data['mesh'].keys()

    def stats(self,type_filter=None):
        '''
        prints out basic stats on data

        Args:
            type_filter (str): filter by node type.  Defaults to None
        '''
        tmp = {}
        for i,d in enumerate(self.collection):
            t = d.get_type()
            if type_filter:
                if type_filter==t:
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
            print key, len(tmp[key])

    def add_data(self,key,name):
        '''
        appends a mesh to the mesh list

        Args:
            key (str): places data in this key in dict.
            name (str): name of data to place.
        '''
        if key == 'mesh':
            if not key in self.data:
                self.data[key] = {}
            if not self.get_data(key,name):
                connectivity = mesh.get_mesh_connectivity(name)
                m = mesh.Mesh()
                m.set_name(name)
                m.set_polygon_counts(connectivity['polygonCounts'])
                m.set_polygon_connects(connectivity['polygonConnects'])
                m.set_point_list(connectivity['points'])

                self.data[key][name] = m

    def get_data(self,key,name):
        '''
        Gets data given 'key'

        Args:
            key (str): the key to get data from.
            name (str): name of the data.

        Returns:
            obj: of data

        Example:
            get_data('mesh','l_bicepMuscle')
        '''
        return self.data[key].get(name,None)


    def get_data_by_key(self,key):
        '''
        Gets all data for given 'key'

        args:
            key (str): the key to get data from

        returns:
            list: of data objs

        Example:
           get_data('mesh')
        '''
        return self.data.get(key,None)
        #return self.data[key]

    def add_node(self,node):
        '''
        appends a node to the node list

        Args:
            node (obj): the node obj to append to collection list.
        '''
        self.collection.append(node)


    def get_nodes(self,type_filter=None,node_filter=None):

        '''
        get nodes in data object

        keywords:
            type_filter (str): filter by node type.  Defaults to None
            node_filter (str): filter by node name.  Defaults to None
        returns:
            [] of nodes
        '''
        items = []
        if not type_filter:
            return self.collection
        else:
            for i,node in enumerate(self.collection):
                if node.get_type() == type_filter:

                    if node_filter:
                        if not isinstance(node_filter, (list, tuple)):
                            node_filter = node_filter.split(' ')
                        if not set(node_filter).isdisjoint(node.get_association()):
                            items.append(node)
                    else:
                        items.append(node)
        return items


    def string_replace(self,search,replace):
        '''
        searches and replaces with regular expressions items in data

        Args:
            search (str): what to search for
            replace (str): what to replace it with

        Examples:
            # replace r_ at front of item with l_
            z.string_replace('^r_','l_')

            # replace _r at end of line with _l
            z.string_replace('_r$','_l')
        '''
        for node in self.get_nodes():
            node.string_replace(search,replace)

        # deal with the mesh search and replacing
        for key in self.data:
            self.data[key] = replace_dict_keys(search,replace,self.data[key])
            for item in self.data[key]:
                self.data[key][item].string_replace(search,replace)




    def write(self,filepath):
        '''
        writes data to disk in json format

        Args:
            filepath (str): filepath to write to disk

        Raises:
            IOError: If not able to write file

        '''
        data = self.get_json_data()
        try:
            with open(filepath, 'w') as outfile:
                json.dump(data, outfile, cls=BaseNodeEncoder,
                    sort_keys=True, indent=4, separators=(',', ': '))
        except IOError:
            print "Error: can\'t find file or write data"
        else:
            print 'wrote-> ',filepath

    def retrieve_from_file(self,filepath):
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
                #print len(data),'fffff'
                self.from_json_data(data)
        except IOError:
            print "Error: can\'t find file or read data"   
        else:
            print 'read-> ',filepath

    def get_json_data(self):
        '''
        Utility function to define data stored in json
        '''
        return [self.collection,self.data,self.info]

    def from_json_data(self, data):
        '''
        Gets data out of json serilization
        '''
        self.collection = data[0]
        self.data = data[1]
        if len(data) == 3:
            self.info = data[2]

    @abc.abstractmethod
    def apply(self):
        '''
        must create a method to inherit this class
        '''
        pass

    @abc.abstractmethod
    def retrieve_from_scene(self,selection):
        '''
        must create a method to inherit this class
        '''
        pass


def replace_dict_keys(search,replace,dictionary):
    '''
    Does a search and replace on dictionary kes

    Args:
        search (str): search term
        replace (str): replace term
        dictionary (dict): the dictionary to do search on

    Returns:
        dict: result of search and replace
    '''
    tmp = {}
    for key in dictionary:
        new = replace_longname(search,replace,key)
        tmp[new] = dictionary[key]

    return tmp

def time_this(original_function):      
    def new_function(*args,**kwargs):
                        
        before = datetime.datetime.now()                     
        x = original_function(*args,**kwargs)                
        after = datetime.datetime.now()                      
        print "Finished: ---Elapsed Time = {0}".format(after-before)      
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
        node = str_to_class(module,name)
        node.__dict__ = json_object
        return node

    else:
        return json_object

def replace_longname(search,replace,longName):
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
            i = re.sub(search, replace,i)
            newName+='|'+i

    return newName

def str_to_class(module,name):
    '''
    Given module and name instantiantes a class

    Args:
        module (str): module
        name (str): the class name

    returns:
        obj: class object
    '''
    i = importlib.import_module( module )
    MyClass = getattr(i, name)
    instance = MyClass()
    return instance


