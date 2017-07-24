import maya.cmds as mc
import maya.mel as mm
import maya.OpenMaya as om

import logging


logger = logging.getLogger(__name__)



ZNODES = [
        'zGeo',
        'zSolver',
        'zSolverTransform',
        'zIsoMesh',
        'zDelaunayTetMesh',
        'zTet',
        'zTissue',
        'zBone',
        'zCloth',
        'zSolver',
        'zCache',
        'zEmbedder',
        'zAttachment',
        'zMaterial',
        'zFiber',
        'zCacheTransform']


class MayaMixin(object):
    """
    A Mixin class to deal with Maya specific functionality
    """
    def __init__(self):
        self.__mobjects = list()

    def clear_mObjects(self):
        """
        Clears the mObject list associated with the nodes.
        """
        self.__mobjects = [None] * len(self.get_nodes())

    def add_mObject(self, maya_node, node):

        index = self.get_nodes().index(node)

        if mc.objExists(maya_node):
            selection_list = om.MSelectionList()
            selection_list.add(maya_node)
            mobject = om.MObject()
            selection_list.getDependNode(0, mobject)

            self.__mobjects[index] = mobject
            # logger.info(mObject)
        else:
            self.__mobjects[index] = None

    def get_scene_name_for_node(self, node, fullpath=True):
        index = self.get_nodes().index(node)
        mobject = self.__mobjects[index]

        if mobject:
            if mobject.hasFn(om.MFn.kDagNode):
                dagpath = om.MDagPath()
                om.MFnDagNode(mobject).getPath(dagpath)
                if fullpath:
                    name = dagpath.fullPathName()
                else:
                    name = dagpath.partialPathName()
            else:
                name = om.MFnDependencyNode(mobject).name()
        else:
            name = None

        if not name:
            # if we have a mObject stored for node use it.  Ir else use the name
            name = node.get_name()

        return name

    #---------------------------------------------------------------------------
    def set_maya_attrs_for_node(self, node, attr_filter=None):

        name = self.get_scene_name_for_node(node)

        type_ = node.get_type()
        nodeAttrs = node.get_attr_list()
        if attr_filter:
            if attr_filter.get(type_,None):
                nodeAttrs = list(set(nodeAttrs).intersection(attr_filter[type_]))

        for attr in nodeAttrs:
            if node.get_attr_key('type') == 'doubleArray':
                if mc.objExists(name+'.'+attr):
                    if not mc.getAttr(name+'.'+attr,l=True):
                        mc.setAttr(name+'.'+attr, node.get_attr_value(attr),
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

    def set_maya_weights_for_node(self, node, interp_maps=False):

        maps = node.get_maps()
        name = self.get_scene_name_for_node(node)
        original_name = node.get_name()

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

                    cur_conn = get_mesh_connectivity(mnameShort)

                    #print len(cur_conn['points']),len(mesh.get_point_list())
                    if len(cur_conn['points']) != len(meshData.get_point_list()):
                        interp_maps=True

                if interp_maps == True:
                    logger.info('interpolating maps...{}'.format(mp))
                    origMesh = meshData.build( )
                    wList = interpolateValues(origMesh,mnameShort,wList)

                mp = mp.replace(original_name, name)

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


#
# def create_zBone(bodies):
#     sel = mc.ls(sl=True)
#     mc.select(bodies)
#     tmp = mm.eval('ziva -b')
#     mobjs = []
#     for t in tmp:
#         mobjs.append(getDependNode(t))
#
#     mc.select(sel,r=True)
#     return mobjs

def check_body_type(bodies):
    '''
    Checks if given bodies are either zTissue, zCloth and or zBone.  Mostly
    used to see if we can create a zAttachment before we try.  Additionaly 
    does a check if all objects exist in scene.

    Args:
        bodies (list):  List of bodies we want to check type of.  

    Rerturns:
        (bool): True if all bodies pass test, else False.
    '''
    sel = mc.ls(sl=True)
    for body in bodies:
        if not mc.objExists(body):
            return False

    mc.select(bodies)
    bt = mm.eval('zQuery -bt')

    if len(bt) == len(bodies):
        return True
    else:
        return False

def get_type(body):
    try:
        return mc.objectType(body)
    except:
        pass

def clean_scene():
    for node in ZNODES:
        in_scene = mc.ls(type=node)
        if len(in_scene) > 0:
            mc.delete(in_scene)

def get_zSolver(body):
    sel = mc.ls(sl=True)
    mc.select(body,r=True)
    solver = mm.eval('zQuery -t "zSolver" -l')
    mc.select(sel,r=True)
    return solver

def get_zSolverTransform(body):
    sel = mc.ls(sl=True)
    mc.select(body,r=True)
    solver = mm.eval('zQuery -t "zSolverTransform" -l')
    mc.select(sel,r=True)
    return solver

def get_zAttachments(bodies):
    sel = mc.ls(sl=True)
    mc.select(bodies,r=True)
    attachments = mm.eval('zQuery -t zAttachment')
    mc.select(sel,r=True)
    if attachments:
        #todo remove duplicates while mainiting order
        return list(set(attachments))
    else:
        return []

def isSolver(selection):
    isSolver = False
    for s in selection:
        if mc.objectType(s) == 'zSolver' or mc.objectType(s) == 'zSolverTransform':
            isSolver = True
            continue
    return isSolver

def get_zBones(bodies):
    sel = mc.ls(sl=True)

    if isSolver(sel):
        bones = mm.eval('zQuery -t zBone')
        if bones:
            return bones
        else:
            return []
    else:
        attachments = get_zAttachments(bodies)
        bones = []
        if attachments:
            for attachment in attachments:
                mesh1 = mm.eval('zQuery -as -l "'+attachment+'"')
                mesh2 = mm.eval('zQuery -at -l "'+attachment+'"')
                mc.select(mesh1,mesh2,r=True)
                tmp = mm.eval('zQuery -t "zBone"')
                if tmp:
                    bones.extend(tmp)

        #mc.select(bodies,r=True)
        mc.select(sel,r=True)
        if len(bones) > 0:
            return list(set(bones))
        else:
            return []

def get_zTets(bodies):
    sel = mc.ls(sl=True)
    mc.select(bodies,r=True)
    zTets = mm.eval('zQuery -t "zTet"')
    mc.select(sel,r=True)
    if zTets:
        return zTets
    else:
        return []



def get_zTissues(bodies):
    sel = mc.ls(sl=True)
    mc.select(bodies,r=True)
    zTissues = mm.eval('zQuery -t "zTissue"')
    mc.select(sel,r=True)
    if zTissues:
        return zTissues
    else:
        return []

def get_zMaterials(bodies):
    '''
    Gets zMaterial nodes given a mesh
    '''
    sel = mc.ls(sl=True)
    mc.select(bodies,r=True)
    zMaterial = mm.eval('zQuery -t "zMaterial"')
    mc.select(sel,r=True)
    if zMaterial:
        return zMaterial
    else:
        return []

def get_zFibers(bodies):
    sel = mc.ls(sl=True)
    mc.select(bodies,r=True)
    zFibers = mm.eval('zQuery -t "zFiber"')
    mc.select(sel,r=True)
    if zFibers:
        return zFibers
    else:
        return []

def get_zCloth(bodies):
    sel = mc.ls(sl=True)
    mc.select(bodies,r=True)
    zCloth = mm.eval('zQuery -t "zCloth"')
    mc.select(sel,r=True)
    if zCloth:
        return zCloth
    else:
        return []

def get_zTet_user_mesh(zTet):
    '''
    Gets the user tet mesh hooked up to a given zTet in any.

    args:
        zTet (string): the zTet to query.
    '''
    if mc.objExists(zTet+'.iTet'):
        mesh = mc.listConnections(zTet+'.iTet')
        if mesh:
            return mc.ls(mesh[0],l=True)[0]
        else:
            return mesh
    return None

def get_lineOfAction_fiber(zFiber):
    '''
    Gets the zLineOfAction node hooked up to a given zFiber in any.

    args:
        zFiber (string): the zFiber to query.
    '''
    if mc.objExists(zFiber+'.oLineOfActionData'):
        conn = mc.listConnections(zFiber+'.oLineOfActionData')
        if conn:
            return conn[0]
        else:
            return None
    else:
        return None


def get_association(zNode):
    '''
    Gets an association of given zNode

    args:
        zNode (string): the zNode to find association of.
    '''
    _type = mc.objectType(zNode)

    if _type == 'zAttachment':
        tmp=[]
        tmp.extend(mm.eval('zQuery -as -l "'+zNode+'"'))
        tmp.extend(mm.eval('zQuery -at -l "'+zNode+'"'))
        #mc.select(sel,r=True)

        return tmp

    elif _type == 'zLineOfAction':
        tmp = mc.listConnections(zNode+'.curves')
        return tmp


    else:
        cmd = 'zQuery -t "%s" -l -m "%s"' % (_type,zNode)

        nope = ['zSolverTransform','zSolver']
        if _type in nope:
            return None
        else:
            mesh = mm.eval(cmd)
            return mesh


def rename_ziva_nodes(replace=['_muscle', '_bone']):
    """
    Renames zNodes based on mesh it's connected to.

    args:
        replace (list): subset of mesh name to replace with zNode name

    * zFiber: <meshName>_zFiber
    * zMaterial: <meshName>_zMaterial
    * zTet: <meshName>_zTet
    * zTissue: <meshName>_zTissue
    * zBone: <meshName>_zBone
    * zCloth: <meshName>_zCloth
    * zAttachment: <sourceMesh>__<destinationMesh>_zAttachment
    """
    sel = mc.ls(sl=True)
    solver = mm.eval('zQuery -t "zSolver"')

    zNodes = ['zTissue','zTet','zMaterial','zFiber','zBone','zCloth']

    for zNode in zNodes:
        items = mm.eval('zQuery -t "{}" {}'.format(zNode,solver[0]))
        if items:
            for item in items:
                mesh = mm.eval('zQuery -t "{}" -m "{}"'.format(zNode,item))[0]
                for r in replace:
                    mesh = mesh.replace(r,'')
                if item != '{}_{}'.format(mesh,zNode):
                    mc.rename(item,'{}_{}tmp'.format(mesh,zNode))

        # looping through this twice to get around how maya renames stuff
        items = mm.eval('zQuery -t "{}" {}'.format(zNode,solver[0]))
        if items:
            for item in items:
                mesh = mm.eval('zQuery -t "{}" -m "{}"'.format(zNode,item))[0]
                for r in replace:
                    mesh = mesh.replace(r,'')
                if item != '{}_{}'.format(mesh,zNode):
                    mc.rename(item,'{}_{}'.format(mesh,zNode))
                    print 'rename: ',item,'{}_{}'.format(mesh,zNode)

    # for now doing an ls type for lineOfActions until with have zQuery support
    loas = mc.ls(type='zLineOfAction')
    if loas:
        for loa in loas:
            crv = mc.listConnections(loa+'.oLineOfActionData')
            if crv:
                mc.rename(loa,crv[0].replace('_zFiber','_zLineOfAction'))

    attachments = mm.eval('zQuery -t "{}" {}'.format('zAttachment',solver[0]))
    if attachments:
        for attachment in attachments:
            s = mm.eval('zQuery -as {}'.format(attachment))[0]
            for r in replace:
                s = s.replace(r,'')
            t = mm.eval('zQuery -at {}'.format(attachment))[0]
            for r in replace:
                t = t.replace(r,'')
            if attachment != '{}__{}_{}'.format(s,t,'zAttachment'):
                mc.rename(attachment,'{}__{}_{}'.format(s,t,'zAttachment'))
                print 'rename: ',attachment,'{}__{}_{}'.format(s,t,'zAttachment')

    print 'finished renaming.... '



def select_tissue_meshes():
    '''
    Selects all zTissues in scene
    '''
    mc.select(cl=True)
    meshes = mm.eval('zQuery -t "zTissue" -m')
    mc.select(meshes)


def get_tissue_children(ztissue):
    """
    :param znode:
    :return:
    """
    tmp = []
    if mc.objectType(ztissue) == 'zTissue':
        child_attr = '{}.oChildTissue'.format(ztissue)
        if mc.objExists(child_attr):
            children = mc.listConnections(child_attr)

            if children:
                sel = mc.ls(sl=True)
                mc.select(children)
                tmp.extend(mm.eval('zQuery -t zTissue -m -l'))
                mc.select(sel)
                return tmp
    return None


def get_tissue_parent(ztissue):
    """
    :param znode:
    :return:
    """
    if mc.objectType(ztissue) == 'zTissue':
        parent_attr = '{}.iParentTissue'.format(ztissue)
        if mc.objExists(parent_attr):
            parent = mc.listConnections(parent_attr)
            if parent:
                parent = mm.eval('zQuery -t zTissue -m -l')
                return parent[0]
    return None


def getMDagPathFromMeshName( meshName ):
    mesh_mDagPath = om.MDagPath()
    selList = om.MSelectionList()
    selList.add( meshName )
    selList.getDagPath( 0, mesh_mDagPath )

    return mesh_mDagPath

# def getDependNode(nodeName):
#     '''
#     Get an MObject (depend node) for the associated node name
#
#     :Parameters:
#         nodeName
#             String representing the node
#
#     :Return: depend node (MObject)
#
#     '''
#     dependNode = om.MObject()
#     selList = om.MSelectionList()
#     selList.add(nodeName)
#     if selList.length() > 0:
#         selList.getDependNode(0, dependNode)
#     return dependNode


def check_mesh_quality(meshes):
    '''
    Light wrapper around checking mesh quality.

    args:
        meshes (list): A list of meshes you want to check

     Raises:
            StandardError: If any mesh does not pass mesh check
    '''

    tmp = []
    for s in meshes:
        mc.select(s,r=True)
        mm.eval('ziva -mq')
        sel2 = mc.ls(sl=True)
        if sel2[0] != s:
            tmp.extend(sel2)

    if tmp:
        mc.select(tmp)
        raise StandardError, 'check meshes!'
    else:
        mc.select(meshes)

