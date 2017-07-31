import re
import maya.cmds as mc
import maya.mel as mm
import maya.OpenMaya as om

import logging

logger = logging.getLogger(__name__)

class Map(object):
    def __init__(self):
        self._class = (self.__class__.__module__,self.__class__.__name__)

        self._name = None


    def get_name(self,longName=False):
        if self._name:
            if longName:
                return self._name
            else:
                return self._name.split('|')[-1]
        else:
            return None
        
    def set_name(self,name):
        self._name = name   

    def set_mesh(self,mesh):
        self._mesh = mesh   

    def get_mesh(self,longName=False):

        if self._mesh:
            if longName:
                return self._mesh
            else:
                return self._mesh.split('|')[-1]
        else:
            return None



    def set_value(self,value):
        #print value
        self._value = value

    def get_value(self):
        return self._value

    def string_replace(self,search,replace):
        # name replace----------------------------------------------------------
        name = self.get_name(longName=True)
        newName = replace_longname(search,replace,name)
        self.set_name(newName)

        mesh = self.get_mesh(longName=True)
        newMesh = replace_longname(search,replace,mesh)
        self.set_mesh(newMesh)

    # def __str__(self):
    #     if self.get_name():
    #         return '<%s.%s "%s">' % (self.__class__.__module__,self.__class__.__name__, self.get_name())
    #     return '<%s.%s>' % (self.__class__.__module__,self.__class__.__name__)

    # def __repr__(self):
    #     return self.__str__()

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
            if '|' in longName:
                newName+='|'+i
            else:
                newName += i

    if newName != longName:
        logger.info('replacing name: {}  {}'.format(longName,newName))

    return newName




def set_weights(nodes,data,interp_maps=False):
    logger.info('DEPRACATED: Use .set_maya_weights_for_builder_node')
    for node in nodes:
        maps = node.get_maps()
        name = node.get_name()

        for mp in maps:
            mapData = data.get_data_by_key_name('map',mp)
            meshData = data.get_data_by_key_name('mesh',mapData.get_mesh(longName=True))
            mname= meshData.get_name(longName=True)
            mnameShort = meshData.get_name(longName=False)
            wList = mapData.get_value()


            #mname= maps[attr]['mesh'] 
            #wList = maps[attr]['value']
            #mnameShort = mname.split('|')[-1]

            if mc.objExists(mnameShort):
                #mesh = meshes[mname]

                if interp_maps == 'auto':
                    
                    cur_conn = get_mesh_connectivity(mnameShort)

                    #print len(cur_conn['points']),len(mesh.get_point_list())
                    if len(cur_conn['points']) != len(meshData.get_point_list()):
                        interp_maps=True

                if interp_maps == True:
                    logger.info('interpolating maps...{}'.format(mp))
                    origMesh = meshData.build( )
                    wList = interpolateValues(origMesh,mnameShort,wList)

                if mc.objExists('%s[0]' % (mp)):
                    if not mc.getAttr('%s[0]' % (mp),l=True):
                        tmp = []
                        for w in wList:
                            tmp.append(str(w))
                        val = ' '.join(tmp)
                        cmd = "setAttr "+'%s[0:%d] ' % (mp, len(wList)-1)+val
                        #print 'setting',name,attr
                        mm.eval(cmd)

                else:
                    try:
                        #print 'here we go',name,attr,wList
                        mc.setAttr(mp,wList,type='doubleArray')
                    except:
                        pass
                if interp_maps == True:
                    mc.delete(origMesh)






def get_weights(node,mesh,attr):
    tmp = {}

    vc = mc.polyEvaluate(mesh,v=True)

    try:
        value = mc.getAttr('%s.%s[0:%d]' % (node,attr, vc-1))
    except:
        value = mc.getAttr('%s.%s' % (node,attr))

    return value







def get_map_data( node,attr,mesh ):
    mapName = '{}.{}'.format(node,attr)
    value = get_weights(node,mesh,attr)
    m = Map()
    m.set_name(mapName)
    m.set_mesh(mesh)
    m.set_value(value)
    return m