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
        self.set_mesh(newName)

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
    #TODO break down setting of weights to not use base.node
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




def get_mesh_connectivity(mesh_name):
    
    space = om.MSpace.kWorld
    meshToRebuild_mDagPath = getMDagPathFromMeshName( mesh_name )
    meshToRebuild_mDagPath.extendToShape()
    
    meshToRebuild_polyIter = om.MItMeshPolygon( meshToRebuild_mDagPath )
    meshToRebuild_vertIter = om.MItMeshVertex( meshToRebuild_mDagPath )
    
    numPolygons = 0
    numVertices = 0
    # vertexArray_mFloatPointArray = om.MFloatPointArray()
    #polygonCounts_mIntArray = om.MIntArray()
    polygonCountsList = list()
    polygonConnectsList = list()
    pointList = list()
    
    while not meshToRebuild_vertIter.isDone(): 
        numVertices += 1
        pos_mPoint = meshToRebuild_vertIter.position(space)
        pos_mFloatPoint = om.MFloatPoint( pos_mPoint.x,pos_mPoint.y,pos_mPoint.z )

        pointList.append( [ 
                pos_mFloatPoint[0], 
                pos_mFloatPoint[1], 
                pos_mFloatPoint[2]
                ] )
        meshToRebuild_vertIter.next()
      
    while not meshToRebuild_polyIter.isDone(): 
        numPolygons += 1
        polygonVertices_mIntArray = om.MIntArray()
        meshToRebuild_polyIter.getVertices( polygonVertices_mIntArray )
        for vertexIndex in polygonVertices_mIntArray: 
            polygonConnectsList.append( vertexIndex )
        
        polygonCountsList.append( polygonVertices_mIntArray.length() )

        meshToRebuild_polyIter.next()
    tmp = {}
    tmp['polygonCounts'] = polygonCountsList
    tmp['polygonConnects'] = polygonConnectsList
    tmp['points'] = pointList

    return tmp


def get_weights(node,mesh,attr):
    tmp = {}

    vc = mc.polyEvaluate(mesh,v=True)

    try:
        value = mc.getAttr('%s.%s[0:%d]' % (node,attr, vc-1))
    except:
        value = mc.getAttr('%s.%s' % (node,attr))

    return value



def interpolateValues( sourceMeshName, destinationMeshName,wList ): 
    '''
    Description: 
        Will transfer values between similar meshes with differing topology. 
        Lerps values from triangleIndex of closest point on mesh. 
      
    Accepts: 
        sourceMeshName, destinationMeshName - strings for each mesh transform
      
    Returns: 
      
    '''
    sourceMesh_mDagPath = getMDagPathFromMeshName( sourceMeshName )
    destinationMesh_mDagPath = getMDagPathFromMeshName( destinationMeshName )
    sourceMeshShape_mDagPath = om.MDagPath( sourceMesh_mDagPath )
    sourceMeshShape_mDagPath.extendToShape()
    
    sourceMesh_mMeshIntersector = om.MMeshIntersector()
    sourceMesh_mMeshIntersector.create( sourceMeshShape_mDagPath.node()  )
    
    destinationMesh_mItMeshVertex = om.MItMeshVertex( destinationMesh_mDagPath )
    sourceMesh_mItMeshPolygon = om.MItMeshPolygon( sourceMesh_mDagPath )
    
    u_util = om.MScriptUtil()
    v_util = om.MScriptUtil()
    u_util_ptr = u_util.asFloatPtr()
    v_util_ptr = v_util.asFloatPtr()  
    
    int_util = om.MScriptUtil()
    
    interpolatedWeights = list()
  
    while not destinationMesh_mItMeshVertex.isDone(): 
    
        closest_mPointOnMesh = om.MPointOnMesh()
        sourceMesh_mMeshIntersector.getClosestPoint( 
                    destinationMesh_mItMeshVertex.position(om.MSpace.kWorld ), 
                    closest_mPointOnMesh
                    )
      
        sourceMesh_mItMeshPolygon.setIndex( 
                    closest_mPointOnMesh.faceIndex(), 
                    int_util.asIntPtr() 
                    ) 
        vertices_mIntArray = om.MIntArray()
      
        triangle_mPointArray = om.MPointArray()
        triangle_mIntArray = om.MIntArray()
      
        sourceMesh_mItMeshPolygon.getTriangle( 
                    closest_mPointOnMesh.triangleIndex(), 
                    triangle_mPointArray, 
                    triangle_mIntArray,
                    om.MSpace.kWorld
                    )
                                             
        closest_mPointOnMesh.getBarycentricCoords( 
                    u_util_ptr, 
                    v_util_ptr 
                    )                                        
    

        #-----  COLOUR PER VERTEX STUFF - CHANGE TO WEIGHT MAP --------------- #
        weights = list()
        for i in xrange( 3 ): 
            vertexId_int = triangle_mIntArray[i]
            weights.append( wList[vertexId_int] )
        #--------- COLOUR PER VERTEX STUFF - CHANGE TO WEIGHT MAP ------------ #
        #print 'weights',weights
        
        bary_u = u_util.getFloat( u_util_ptr )                                  
        bary_v = v_util.getFloat( v_util_ptr )
        bary_w = 1 - bary_u - bary_v
        
        interp_weight = (bary_u*weights[0]) + (bary_v*weights[1]) + (bary_w*weights[2])
        
        interpolatedWeights.append( interp_weight )
        

        
        destinationMesh_mItMeshVertex.next()
    
    
    return interpolatedWeights  

def getMDagPathFromMeshName( meshName ): 
    mesh_mDagPath = om.MDagPath()
    selList = om.MSelectionList()
    selList.add( meshName )
    selList.getDagPath( 0, mesh_mDagPath )
    
    return mesh_mDagPath

def get_map_data( node,attr,mesh ):
    mapName = '{}.{}'.format(node,attr)
    value = get_weights(node,mesh,attr)
    m = Map()
    m.set_name(mapName)
    m.set_mesh(mesh)
    m.set_value(value)
    return m