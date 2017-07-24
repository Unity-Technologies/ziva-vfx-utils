from zBuilder.nodes.base import BaseNode
import maya.cmds as mc
import maya.mel as mm
import zBuilder.zMaya as mz
import logging

logger = logging.getLogger(__name__)

class EmbedderNode(BaseNode):
    def __init__(self):
        BaseNode.__init__(self)

        self.__embedded_meshes = None
        self.__collision_meshes = None

    def string_replace(self, search, replace, name=True, association=True):
        super(EmbedderNode, self).string_replace(search, replace)
        print 'zEmbedder:string_replace'

    def set_collision_meshes(self,meshes):
        self.__collision_meshes = meshes

    def set_embedded_meshes(self,meshes):
        self.__embedded_meshes = meshes

    def get_collision_meshes(self,longName=False):
        if longName:
            return self.__collision_meshes
        else:
            tmp = {}
            msh = []
            for name in self.__collision_meshes:
                for item in self.__collision_meshes[name]:
                    msh.append(item.split('|')[-1])
                tmp[name.split('|')[-1]] = msh
            return tmp

    def get_embedded_meshes(self,longName=False):
        if longName:
            return self.__embedded_meshes
        else:
            tmp = {}
            msh = []
            for name in self.__embedded_meshes:
                for item in self.__embedded_meshes[name]:
                    msh.append(item.split('|')[-1])
                tmp[name.split('|')[-1]] = msh
            return tmp

    def print_(self):
        super(EmbedderNode, self).print_()
        if self.get_collision_meshes(longName=True):
            print 'Collision Meshes: ',self.get_collision_meshes(longName=True)
        if self.get_embedded_meshes(longName=True):
            print 'Embedded Meshes: ',self.get_embedded_meshes(longName=True)


def get_zGeos(bodies):
    mc.select(bodies,r=True)
    zGeo = mm.eval('zQuery-t "zGeo"')
    if zGeo:
        return zGeo
    else:
        return []


def get_zEmbedder(bodies):
    mc.select(bodies,r=True)
    embedder = mm.eval('zQuery -t "zEmbedder"')
    if embedder:
        return embedder[0]
    else:
        return None



def get_embedded_meshes(bodies):

    collision_meshes = {}
    embedded_meshes = {}
    for body in bodies:
        colMesh = mm.eval('zQuery -cm -l ' + body )
        emMesh = mm.eval('zQuery -em -l ' + body)
        if emMesh and colMesh:
            emMesh = list(set(set(emMesh)-set(colMesh)))
            if emMesh == []:
                emMesh = None

        if emMesh:
            embedded_meshes[body] = emMesh
        if colMesh:
            collision_meshes[body] = colMesh

    return embedded_meshes,collision_meshes
    
