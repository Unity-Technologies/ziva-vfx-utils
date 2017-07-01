import maya.cmds as mc
import maya.mel as mm
import maya.OpenMaya as om




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


def create_zBone(bodies):
    sel = mc.ls(sl=True)
    mc.select(bodies)
    tmp = mm.eval('ziva -b')
    mobjs = []
    for t in tmp:
        mobjs.append(getDependNode(t))

    mc.select(sel,r=True)
    return mobjs

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


def rename_ziva_nodes(replace=['_muscle','_bone']):
    '''
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
    '''
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

    # for now doinng an ls type for lineOfActions until with have zQuery support
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
    


def getDependNode(nodeName):
    '''
    Get an MObject (depend node) for the associated node name

    :Parameters:
        nodeName
            String representing the node
    
    :Return: depend node (MObject)

    '''
    dependNode = om.MObject()
    selList = om.MSelectionList()
    selList.add(nodeName)
    if selList.length() > 0: 
        selList.getDependNode(0, dependNode)
    return dependNode


def check_mesh_quality(meshes):
    '''
    Light wrapper around checking mesh quality.

    args:
        meshes (list): A list of meshes you want to check

     Raises:
            StandardError: If any mesh does not pass mesh check
    '''
    mc.select(meshes,add=True)
    mesh_quality = mm.eval('ziva -mq')

    sel = mc.ls(sl=True)
    if sel:
        if 'vtx[' in sel[0]:
            raise StandardError, mesh_quality
