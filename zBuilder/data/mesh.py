import re
import maya.cmds as mc
import maya.mel as mm
import maya.OpenMaya as om



class Mesh(object):
    def __init__(self):
        self._class = (self.__class__.__module__,self.__class__.__name__)

        self._name = None
        self._pCountList = []
        self._pConnectList = []
        self._pointList = []

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

    def string_replace(self,search,replace):
        # name replace----------------------------------------------------------
        name = self.get_name(longName=True)
        newName = replace_longname(search,replace,name)
        self.set_name(newName)


    def set_polygon_counts(self,pCountList): 
        self._pCountList = pCountList

    def set_polygon_connects(self,pConnectList): 
        self._pConnectList = pConnectList

    def set_point_list(self,pointList): 
        self._pointList = pointList

    def get_polygon_counts(self): 
        return self._pCountList

    def get_polygon_connects(self): 
        return self._pConnectList

    def get_point_list(self): 
        return self._pointList

    def build(self):
        buildMesh(
            self.get_name(),
            self.get_polygon_counts(),
            self.get_polygon_connects(),
            self.get_point_list(),
            )


    # def __str__(self):
    #     if self.get_name():
    #         return '<%s.%s "%s">' % (self.__class__.__module__,self.__class__.__name__, self.get_name())
    #     return '<%s.%s>' % (self.__class__.__module__,self.__class__.__name__)

    # def __repr__(self):
    #     return self.__str__()

def replace_longname(search,replace,longName):
    items = longName.split('|')
    newName = ''
    for i in items:
        if i:
            i = re.sub(search, replace,i)
            newName+='|'+i

    return newName

def buildMesh( name,polygonCounts,polygonConnects,vertexArray ): 
    
    polygonCounts_mIntArray = om.MIntArray()
    polygonConnects_mIntArray = om.MIntArray()
    vertexArray_mFloatPointArray = vertexArray
    
    for i in polygonCounts:
        polygonCounts_mIntArray.append(i)

    for i in polygonConnects:
        polygonConnects_mIntArray.append(i)

    # back
    newPointArray = om.MPointArray()
    for point in vertexArray_mFloatPointArray:
        newPoint = om.MPoint(point[0],point[1],point[2],1.0)
        newPointArray.append(newPoint)

    newMesh_mfnMesh = om.MFnMesh()
    returned = newMesh_mfnMesh.create(  newPointArray.length(), 
                                        polygonCounts_mIntArray.length(), 
                                        newPointArray, 
                                        polygonCounts_mIntArray, 
                                        polygonConnects_mIntArray  )
    
    returned_mfnDependencyNode = om.MFnDependencyNode( returned )
    
    # do housekeeping. 
    returnedName = returned_mfnDependencyNode.name()

    rebuiltMesh = mc.rename( returnedName, name + '_rebuilt' )
    
    #mc.sets( rebuiltMesh, e=True, addElement='initialShadingGroup' )
    
    return rebuiltMesh

def set_weights(nodes,meshes,interp_maps=False):
    #TODO break down setting of weights to not use base.node
    for node in nodes:
        maps = node.get_maps()
        name = node.get_name()

        for attr in maps:
            #print 'OOOMMMGGG',attr
            mname= maps[attr]['mesh']
            wList = maps[attr]['value']
            mnameShort = mname.split('|')[-1]

            if mc.objExists(mnameShort):
                mesh = meshes[mname]

                if interp_maps == 'auto':
                    
                    cur_conn = get_mesh_connectivity(mnameShort)

                    #print len(cur_conn['points']),len(mesh.get_point_list())
                    if len(cur_conn['points']) != len(mesh.get_point_list()):
                        interp_maps=True

                if interp_maps == True:
                    print 'interpolating maps...',mnameShort
                    polygonCounts = mesh.get_polygon_counts()
                    polygonConnects = mesh.get_polygon_connects()
                    vertexArray = mesh.get_point_list()

                    origMesh = buildMesh( mnameShort,polygonCounts,polygonConnects,vertexArray )

                    wList = interpolateValues(origMesh,mnameShort,wList)

                if mc.objExists('%s.%s[0]' % (name,attr)):
                    if not mc.getAttr('%s.%s[0]' % (name,attr),l=True):
                        tmp = []
                        for w in wList:
                            tmp.append(str(w))
                        val = ' '.join(tmp)
                        cmd = "setAttr "+'%s.%s[0:%d] ' % (name,attr, len(wList)-1)+val
                        #print 'setting',name,attr
                        mm.eval(cmd)

                else:
                    try:
                        #print 'here we go',name,attr,wList
                        mc.setAttr('%s.%s' % (name,attr),wList,type='doubleArray')
                    except:
                        pass
                if interp_maps == True:
                    mc.delete(origMesh)




def get_weights(node,meshes,attrs):
    tmp = {}
    #print 'BARG: ',node,meshes,attrs
    for attr,mesh in zip(attrs,meshes):
        #pList = getPointList(mesh)
        vc = mc.polyEvaluate(mesh,v=True)
        tmp[attr] = {}
        try:
            tmp[attr]['value'] = mc.getAttr('%s.%s[0:%d]' % (node,attr, vc-1))
        except:
            tmp[attr]['value'] = mc.getAttr('%s.%s' % (node,attr))

        tmp[attr]['mesh'] = mesh


    return tmp

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

