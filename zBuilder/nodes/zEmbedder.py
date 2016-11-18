from base import BaseNode
import maya.cmds as mc
import maya.mel as mm
import zBuilder.zMaya as mz


class EmbedderNode(BaseNode):
    def __init__(self):
        BaseNode.__init__(self)
        #self._association = {}

        self.__embedded_meshes = None
        self.__collision_meshes = None

    def string_replace(self,search,replace,name=True,association=True):
        super(EmbedderNode, self).string_replace(search,replace)
        print 'zEmbedder:string_replace'

        pass

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

    def _print(self):
        super(EmbedderNode, self)._print()
        print 'Collision Meshes: ',self.get_collision_meshes(longName=True)
        print 'Embedded Meshes: ',self.get_embedded_meshes(longName=True)



def replace_longname(search,replace,longName):
    items = longName.split('|')
    newName = ''
    for i in items:
        if i:
            i = re.sub(search, replace,i)
            newName+='|'+i

    return newName


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


    #print embedded_meshes,'em'
    #print collision_meshes,'col'

    return embedded_meshes,collision_meshes
    
    # tmp={}
    # embedder = get_zEmbedder(bodies)
    
    # for body in bodies:
    #     if body not in tmp:
    #         tmp[body] = {}
    #         tmp[body]['collision'] = []
    #         tmp[body]['embedded'] = []


    #     zGeo = get_zGeos(body)
    #     if zGeo:
    #         zGeo = zGeo[0]
    #         zEmbedders = mc.listConnections(zGeo+'.oGeo',c=True,t='zEmbedder',p=True)
    #         if zEmbedders:
    #             if len(zEmbedders) > 2:
    #                 for item in zEmbedders[3::2]:
    #                     i = item.split('iGeo')[1]
    #                     embedded = mc.listConnections(embedder+'.outputGeometry'+i)[0]

    #                     shape = mc.listRelatives(embedded,c=True)[0]
    #                     message_to_tissue = mc.listConnections(shape+'.message',type='zTissue')
    #                     if message_to_tissue:
    #                         tmp[body]['collision'].append(True)
    #                     else:
    #                         tmp[body]['collision'].append(False)

    #                     tmp[body]['embedded'].append(embedded)

    # return tmp