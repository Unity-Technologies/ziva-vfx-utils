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
        self.data = {}
        self.info = {}
        self.info['data_version'] = .1
        self.info['current_time'] = time.strftime("%d/%m/%Y  %H:%M:%S")
        self.info['maya_version'] = mc.about(v=True)
        self.info['operating_system'] = mc.about(os=True)




    def print_(self,type_filter=None,node_filter=None,print_data=False):

        '''
        print info on each node

        keyword arguments:
            type_filter -- filter by node type (default: None)
            node_filter -- filter by node name (default: None)
            print_data -- prints name of data stored (ie meshes) (default: False)

        '''

        for node in self.get_nodes(type_filter=type_filter,node_filter=node_filter):

            node.print_()

        if print_data:
            print self.data['mesh'].keys()

    def stats(self,type_filter=None):
        '''
        prints out basic stats on data

        keywords:
            _type -- filter by node type (default: 'all')
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

        args:
            node -- the node to append
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
        return self.data[key].get(name,None)


    def get_data_by_key(self,key):
        return self.data[key]

    def add_node(self,node):
        '''
        appends a node to the node list

        args:
            node -- the node to append
        '''
        self.collection.append(node)


    def get_nodes(self,type_filter=None,node_filter=None):

        '''
        get nodes in data object

        keywords:
            type_filter -- filter by node type (default: None)
            node_filter -- filter by node name (default: None)
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

        args:
            search -- what to search for
            replace -- what to replace it with

        keywords:
            name -- to search and replace name of node (default: True)
            association -- to search and replace associations (default: True)
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
        writes data to disk

        args:
            filepath -- filepath to write

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

        args:
            filepath -- filepath to read
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
        ''''''
        return [self.collection,self.data,self.info]

    def from_json_data(self, data):
        ''''''
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
        pass


def replace_dict_keys(search,replace,dictionary):

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
        #if isinstance(obj, BaseNode):
        if hasattr(obj, '_class'):
            return obj.__dict__
        else:
            return super(BaseNodeEncoder, self).default(obj)




def load_base_node(json_object):
    #print json_object
    if '_class' in json_object:
        module = json_object['_class'][0]
        name = json_object['_class'][1]
        node = str_to_class(module,name)
        node.__dict__ = json_object
        return node

    else:
        return json_object

def replace_longname(search,replace,longName):
    items = longName.split('|')
    newName = ''
    for i in items:
        if i:
            i = re.sub(search, replace,i)
            newName+='|'+i

    return newName

def str_to_class(module,name):

    i = importlib.import_module( module )
    MyClass = getattr(i, name)
    instance = MyClass()
    return instance


