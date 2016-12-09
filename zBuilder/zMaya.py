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
        #'zShell',
        'zSolver',
        'zCache',
        'zEmbedder',
        'zAttachment',
        'zMaterial',
        'zFiber',
        'zCacheTransform']


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
    mc.select(body,r=True)
    solver = mm.eval('zQuery -t "zSolver" -l')
    return solver

def get_zSolverTransform(body):
    mc.select(body,r=True)
    solver = mm.eval('zQuery -t "zSolverTransform" -l')
    return solver

def get_zAttachments(bodies):
    mc.select(bodies,r=True)
    attachments = mm.eval('zQuery -t zAttachment')
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
    mc.select(bodies,r=True)
    zTets = mm.eval('zQuery -t "zTet"')
    if zTets:
        return zTets
    else:
        return []



def get_zTissues(bodies):
    mc.select(bodies,r=True)
    zTissues = mm.eval('zQuery -t "zTissue"')
    if zTissues:
        return zTissues
    else:
        return []

def get_zMaterials(bodies):
    '''
    Gets zMaterial nodes given a mesh
    '''
    mc.select(bodies,r=True)
    zMaterial = mm.eval('zQuery -t "zMaterial"')
    if zMaterial:
        return zMaterial
    else:
        return []

def get_zFibers(bodies):
    mc.select(bodies,r=True)
    zFibers = mm.eval('zQuery -t "zFiber"')
    if zFibers:
        return zFibers
    else:
        return []



def get_zTet_user_mesh(zNode):
    mesh = mc.listConnections(zNode+'.iTet')
    if mesh:
        return mc.ls(mesh[0],l=True)[0]
    else:
        return mesh



def get_association(zNode):
    #sel = mc.ls(sl=True)
    _type = mc.objectType(zNode)

    if _type == 'zAttachment':
        tmp=[]
        tmp.extend(mm.eval('zQuery -as -l "'+zNode+'"'))
        tmp.extend(mm.eval('zQuery -at -l "'+zNode+'"'))
        #mc.select(sel,r=True)

        return tmp

    else:
        cmd = 'zQuery -t "%s" -l -m "%s"' % (_type,zNode)

        nope = ['zSolverTransform','zSolver']
        if _type in nope:
            return None
        else:
            mesh = mm.eval(cmd)
            return mesh


def rename_ziva_nodes():
    sel = mc.ls(sl=True)
    select_tissue_meshes()
    bodies = mc.ls(sl=True)
    for body in bodies:
        tissue = get_zTissues(body)[0]
        mc.rename(tissue,body+'_zTissue')

        tet = get_zTets(body)[0]
        mc.rename(tet,body+'_zTet')

        for material in get_zMaterials(body):
            mc.rename(material,body+'_zMaterial')

        for fiber in get_zFibers(body):
            mc.rename(fiber,body+'_zFiber')

        for attachment in get_zAttachments(body):
            s = mm.eval('zQuery -as ' +attachment)
            t = mm.eval('zQuery -at ' +attachment)
            mc.rename(attachment,s+'_'+t+'_zAttachment')

    mc.select(sel,r=True)


def select_tissue_meshes():
    mc.select(cl=True)
    meshes = mm.eval('zQuery -t "zTissue" -m')
    mc.select(meshes)
    







