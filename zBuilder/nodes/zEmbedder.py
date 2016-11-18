from base import BaseNode
import maya.cmds as mc
import maya.mel as mm
import zBuilder.zMaya as mz


class EmbedderNode(BaseNode):
    def __init__(self):
        BaseNode.__init__(self)
        #self._association = {}

    def string_replace(self,search,replace,name=True,association=True):
        super(EmbedderNode, self).string_replace(search,replace)
        print 'zEmbedder:string_replace'
        #print self.get_association()
        pass

    def get_association(self,longName=False):
        return self._association



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



def get_embedded_association(bodies):

    tmp = {}
    for body in bodies:
        colMesh = mm.eval('zQuery -cm ' + body)
        emMesh = mm.eval('zQuery -em ' + body)
        if emMesh and colMesh:
            emMesh = set(set(emMesh)-set(colMesh))

        print colMesh,'col'
        print emMesh,'em'

    return {}
    
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