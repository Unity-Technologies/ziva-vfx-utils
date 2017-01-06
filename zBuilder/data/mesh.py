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
        mesh = buildMesh(
            self.get_name(),
            self.get_polygon_counts(),
            self.get_polygon_connects(),
            self.get_point_list(),
            )
        return mesh


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




def getMDagPathFromMeshName( meshName ): 
  
    mesh_mDagPath = om.MDagPath()
    selList = om.MSelectionList()
    selList.add( meshName )
    selList.getDagPath( 0, mesh_mDagPath )
    
    return mesh_mDagPath

def get_mesh_data( meshName ):
    connectivity = get_mesh_connectivity(meshName)
    m = Mesh()
    m.set_name(meshName)
    m.set_polygon_counts(connectivity['polygonCounts'])
    m.set_polygon_connects(connectivity['polygonConnects'])
    m.set_point_list(connectivity['points'])

    return m