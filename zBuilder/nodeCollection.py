import json
from nodes.base import BaseNode
#from nodes.mesh import Mesh
import zBuilder.nodes.mesh as mesh
import maya.cmds as mc
import abc
import re
import sys
import os.path
import importlib


#TODO delete a node

class NodeCollection(object):
    __metaclass__ = abc.ABCMeta
    '''
    This is an object that holds the node data in a list
    '''
    def __init__(self):
        self.collection = []
        self.meshes = {}
        self.info = {}
        self.info['data_version'] = .1
        #self.info['current_time'] = mc.about(cti=True)
        self.info['maya_version'] = mc.about(v=True)
        self.info['operating_system'] = mc.about(os=True)



    def _print(self,_type='all',_filter=None):
        '''
        print info on each node

        keyword arguments:
            _type -- filter by node type (default: 'all')
        '''
        for node in self.get_nodes(_type=_type,_filter=_filter):
            node._print()

    def stats(self,_type='all'):
        '''
        prints out basic stats on data

        keywords:
            _type -- filter by node type (default: 'all')
        '''
        tmp = {}
        for i,d in enumerate(self.collection):
            t = d.get_type()
            if t==_type or _type == 'all':
                if t not in tmp:
                    tmp[t] = []
                tmp[t].append(d)

        for key in tmp:
            print key, len(tmp[key])

    def add_mesh(self,name):
        '''
        appends a mesh to the mesh list

        args:
            node -- the node to append
        '''

        connectivity = mesh.get_mesh_connectivity(name)
        m = mesh.Mesh()
        m.set_name(name)
        m.set_polygon_counts(connectivity['polygonCounts'])
        m.set_polygon_connects(connectivity['polygonConnects'])
        m.set_point_list(connectivity['points'])

        self.meshes[name] = m

    def get_mesh(self,mesh_name):
        return self.meshes.get(mesh_name,None)


    def get_meshes(self):
        return self.meshes

    def add_node(self,node):
        '''
        appends a node to the node list

        args:
            node -- the node to append
        '''
        self.collection.append(node)

    def get_nodes(self,_type='all',_filter=None):
        '''
        get nodes in data object

        keywords:
            _type   -- filter by node type (default: 'all')
            _filter -- filter by node name (default: None)
        returns:
            [] of nodes
        '''
        items = []
        if _type == 'all':
            return self.collection
        else:
            for i,node in enumerate(self.collection):
                if node.get_type() == _type:
                    if _filter:
                        if not isinstance(_filter, (list, tuple)):
                            _filter = _filter.split(' ')
                        if not set(_filter).isdisjoint(node.get_association()):
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

        pop = []
        changed = {}
        for mesh in self.meshes:
            new = replace_longname(search,replace,mesh)
            if new != mesh:
                changed[new] = self.meshes[mesh]
                pop.append(mesh)

        for p,c in zip(pop,changed):
            self.meshes.pop(p)
            self.meshes[c] = changed[c]




    def write(self,filepath):
        '''
        writes data to disk

        args:
            filepath -- filepath to write

        '''
        data = self.get_json_data()
        with open(filepath, 'w') as outfile:
            json.dump(data, outfile, cls=BaseNodeEncoder,
                sort_keys=True, indent=4, separators=(',', ': '))
            print 'wrote-> ',filepath

    def get_json_data(self):
        ''''''
        return [self.collection,self.meshes,self.info]

    def from_json_data(self, data):
        ''''''
        self.collection = data[0]
        self.meshes = data[1]
        if len(data) == 3:
            self.info = data[2]

    @abc.abstractmethod
    def apply(self):
        pass

    @abc.abstractmethod
    def retrieve_from_scene(self,selection):
        pass

    def retrieve_from_file(self,filepath):
        '''
        reads data from a file

        args:
            filepath -- filepath to read
        '''
        with open(filepath, 'rb') as handle:
            data = json.load(handle, object_hook=load_base_node)
            #print len(data),'fffff'
            self.from_json_data(data)
        print 'read-> ',filepath





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


