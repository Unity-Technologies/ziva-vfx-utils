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
    solver = mm.eval('zQuery -t "zSolver"')

    tissues = mm.eval('zQuery -t "zTissue" {}'.format(solver[0]))
    tets = mm.eval('zQuery -t "zTet" {}'.format(solver[0]))
    materials = mm.eval('zQuery -t "zMaterial" {}'.format(solver[0]))
    fibers = mm.eval('zQuery -t "zFiber" {}'.format(solver[0]))
    attachments = mm.eval('zQuery -t "zAttachment" {}'.format(solver[0]))

    for tissue in tissues:
        mc.select(tissue,r=True)
        mesh = mm.eval('zQuery -t "zTissue" -m')[0]
        if tissue != '{}_zTissue'.format(mesh):
            mc.rename(tissue,'{}_zTissue'.format(mesh))
            print 'rename: ',tissue,'{}_zTissue'.format(mesh)

    for tet in tets:
        mc.select(tet,r=True)
        mesh = mm.eval('zQuery -t "zTet" -m')[0]
        if tet != '{}_zTet'.format(mesh):
            mc.rename(tet,'{}_zTet'.format(mesh))
            print 'rename: ',tet,'{}_zTet'.format(mesh)

    for material in materials:
        mc.select(material,r=True)
        mesh = mm.eval('zQuery -t "zMaterial" -m')[0]
        if material != '{}_zMaterial'.format(mesh):
            mc.rename(material,'{}_zMaterial'.format(mesh))
            print 'rename: ',material,'{}_zMaterial'.format(mesh)

    for fiber in fibers:
        mc.select(fiber,r=True)
        mesh = mm.eval('zQuery -t "zFiber" -m')[0]
        if fiber != '{}_zFiber'.format(mesh):
            mc.rename(fiber,'{}_zFiber'.format(mesh))
            print 'rename: ',fiber,'{}_zFiber'.format(mesh)

    for attachment in attachments:
        s = mm.eval('zQuery -as ' +attachment)[0]
        t = mm.eval('zQuery -at ' +attachment)[0]
        if attachment != s+'__'+t+'_zAttachment':
            mc.rename(attachment,s+'__'+t+'_zAttachment')


    print 'finished renaming.... '
    mc.select(sel,r=True)



def select_tissue_meshes():
    mc.select(cl=True)
    meshes = mm.eval('zQuery -t "zTissue" -m')
    mc.select(meshes)
    


def getDependNode(nodeName):
    """Get an MObject (depend node) for the associated node name

    :Parameters:
        nodeName
            String representing the node
    
    :Return: depend node (MObject)

    """
    dependNode = om.MObject()
    selList = om.MSelectionList()
    selList.add(nodeName)
    if selList.length() > 0: 
        selList.getDependNode(0, dependNode)
    return dependNode




