import maya.cmds as mc
import maya.mel as mm
import maya.OpenMaya as om

import zBuilder.data.maps as mps

import logging

logger = logging.getLogger(__name__)


class MayaMixin(object):
    """
    A Mixin class to deal with Maya specific functionality



    """
    def __init__(self):
        self.__mObjects = []


    def clear_mObjects(self):

        self.__mObjects = [None] * len(self.collection)

    def add_mObject(self,maya_node,node):

        index = self.collection.index(node)

        if mc.objExists(maya_node):
            selectionList = om.MSelectionList()
            selectionList.add( maya_node )
            mObject = om.MObject()
            selectionList.getDependNode( 0, mObject )
             
            self.__mObjects[index] = mObject
            #logger.info(mObject) 
        else:
            self.__mObjects[index] = None

    def __get_name_from_mObject(self,node,fullPath=True):
        index = self.collection.index(node)
        mobject = self.__mObjects[index]

        if mobject:
            if mobject.hasFn(om.MFn.kDagNode):
                dagpath = om.MDagPath()
                om.MFnDagNode(mobject).getPath(dagpath)
                if fullPath:
                    return dagpath.fullPathName()
                else:
                    return dagpath.partialPathName()
            else:
                return om.MFnDependencyNode(mobject).name()
        else:
            return None

    #---------------------------------------------------------------------------
    #---------------------------------------------------------------------------
    def set_maya_attrs_for_node(self,node,attr_filter=None):

        name = self.__get_name_from_mObject(node)
        type_ = node.get_type()
        nodeAttrs = node.get_attr_list()
        if attr_filter:
            if attr_filter.get(type_,None):
                nodeAttrs = list(set(nodeAttrs).intersection(attr_filter[type_]))


        for attr in nodeAttrs:
            #print name,attr
            if node.get_attr_key('type') == 'doubleArray':
                if mc.objExists(name+'.'+attr):
                    if not mc.getAttr(name+'.'+attr,l=True):
                        mc.setAttr(name+'.'+attr,node.get_attr_value(attr),
                            type='doubleArray')
                else:
                    print name+'.'+attr + ' not found, skipping'
            else:
                if mc.objExists(name+'.'+attr):
                    if not mc.getAttr(name+'.'+attr,l=True):
                        try:
                            mc.setAttr(name+'.'+attr,node.get_attr_value(attr))
                        except:
                            #print 'tried...',attr
                            pass
                else:
                    print name+'.'+attr + ' not found, skipping'



    def set_maya_weights_for_node(self,node,interp_maps=False):

        maps = node.get_maps()
        name = self.__get_name_from_mObject(node)
        oname = node.get_name()

        for mp in maps:
            
            mapData = self.get_data_by_key_name('map',mp)
            meshData = self.get_data_by_key_name('mesh',mapData.get_mesh(longName=True))
            mname= meshData.get_name(longName=True)
            mnameShort = meshData.get_name(longName=False)
            wList = mapData.get_value()


            #mname= maps[attr]['mesh'] 
            #wList = maps[attr]['value']
            #mnameShort = mname.split('|')[-1]

            if mc.objExists(mnameShort):
                #mesh = meshes[mname]

                if interp_maps == 'auto':
                    
                    cur_conn = mps.get_mesh_connectivity(mnameShort)

                    #print len(cur_conn['points']),len(mesh.get_point_list())
                    if len(cur_conn['points']) != len(meshData.get_point_list()):
                        interp_maps=True

                if interp_maps == True:
                    logger.info('interpolating maps...{}'.format(mp))
                    origMesh = meshData.build( )
                    wList = mps.interpolateValues(origMesh,mnameShort,wList)

                mp = mp.replace(oname,name)

                if mc.objExists('%s[0]' % (mp)):
                    if not mc.getAttr('%s[0]' % (mp),l=True):
                        tmp = []
                        for w in wList:
                            tmp.append(str(w))
                        val = ' '.join(tmp)
                        cmd = "setAttr "+'%s[0:%d] ' % (mp, len(wList)-1)+val
                        #print 'setting',cmd
                        mm.eval(cmd)

                else:
                    try:
                        mc.setAttr(mp,wList,type='doubleArray')
                    except:
                        pass
                if interp_maps == True:
                    mc.delete(origMesh)
