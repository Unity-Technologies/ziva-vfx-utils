import logging

from maya import cmds
from maya import mel
from zBuilder.utils.commonUtils import none_to_empty
from zBuilder.utils.mayaUtils import safe_rename, get_type, is_type
'''
The module contains helper functions for Ziva VFX node inspection and query.
'''

logger = logging.getLogger(__name__)


def check_body_type(bodies):
    """ Checks if given bodies are either zTissue, zCloth and or zBone.  Mostly
    used to see if we can create a zAttachment before we try.  Additionally
    does a check if all objects exist in scene.

    Args:
        bodies (list):  List of bodies we want to check type of.

    Returns:
        (bool): True if all bodies pass test, else False.
    """
    sel = cmds.ls(sl=True)
    for body in bodies:
        if not cmds.objExists(body):
            return False

    cmds.select(bodies)
    bt = mel.eval('zQuery -bt')

    if len(bt) == len(bodies):
        return True
    else:
        return False


def get_zSolver(body):
    """ Gets zSolver in scene.
    Args:
        body: Maya node to find associated solver.

    Returns:
        returns long name of zSolver.
    """
    sel = cmds.ls(sl=True)
    cmds.select(body, r=True)
    solver = mel.eval('zQuery -t "zSolver" -l')
    cmds.select(sel, r=True)
    return solver


def get_zSolverTransform(body):
    """ Gets zSolverTransform in scene.
    Args:
        body: Maya node to find associated solverTransform.

    Returns:
        returns long name of zSolverTransform.
    """
    sel = cmds.ls(sl=True)
    cmds.select(body, r=True)
    solver = mel.eval('zQuery -t "zSolverTransform" -l')
    cmds.select(sel, r=True)
    return solver


def isSolver(selection):
    """ Checks if passed is zSolver or zSolverTransform.
    Args:
        selection: Item of interest.

    Returns:
        True if it is solver, else false.
    """
    isSolver = False
    for s in selection:
        if is_type(s, 'zSolver') or is_type(s, 'zSolverTransform'):
            isSolver = True
            continue
    return isSolver


def get_zAttachments(bodies):
    """ Gets zAttachments in scene.
    Args:
        body: Maya node to find associated zAttachments.

    Returns:
        string of name of zAttachments.
    """
    sel = cmds.ls(sl=True)
    cmds.select(bodies, r=True)
    attachments = mel.eval('zQuery -t zAttachment')
    cmds.select(sel, r=True)
    if attachments:
        return list(set(attachments))
    else:
        return []


def get_zBones(bodies):
    """ Gets zBones in scene.
    Args:
        body: Maya node to find associated zBones.

    Returns:
        string of name of zBones.
    """
    sel = cmds.ls(sl=True)

    if isSolver(sel):
        bones = mel.eval('zQuery -t zBone')
        if bones:
            return bones
        else:
            return []
    else:
        bones = mel.eval('zQuery -t zBone')
        if not bones:
            bones = list()

        attachments = get_zAttachments(bodies)

        if attachments:
            for attachment in attachments:
                mesh1 = mel.eval('zQuery -as -l "' + attachment + '"')
                mesh2 = mel.eval('zQuery -at -l "' + attachment + '"')
                cmds.select(mesh1, mesh2, r=True)
                tmp = mel.eval('zQuery -t "zBone"')
                if tmp:

                    bones.extend(tmp)

        cmds.select(sel, r=True)
        if len(bones) > 0:
            return list(set(bones))
        else:
            return []


def get_zTets(bodies):
    """ Gets zTets in scene.
    Args:
        body: Maya node to find associated zTets.

    Returns:
        string of name of zTets.
    """
    sel = cmds.ls(sl=True)
    cmds.select(bodies, r=True)
    zTets = mel.eval('zQuery -t "zTet"')
    cmds.select(sel, r=True)
    if zTets:
        return zTets
    else:
        return []


def get_zTissues(bodies):
    """ Gets zTissues in scene.
    Args:
        body: Maya node to find associated zTissues.

    Returns:
        string of name of zTissues.
    """
    sel = cmds.ls(sl=True)
    cmds.select(bodies, r=True)
    zTissues = mel.eval('zQuery -t "zTissue"')
    cmds.select(sel, r=True)
    if zTissues:
        return zTissues
    else:
        return []


def get_zMaterials(bodies):
    """ Gets zmaterials in scene.
    Args:
        body: Maya node to find associated zMaterials.

    Returns:
        string of name of zmaterials.
    """
    sel = cmds.ls(sl=True)
    cmds.select(bodies, r=True)
    zMaterial = mel.eval('zQuery -t "zMaterial"')
    cmds.select(sel, r=True)
    if zMaterial:
        return zMaterial
    else:
        return []


def get_zFibers(bodies):
    """ Gets zFibers in scene.
    Args:
        body: Maya node to find associated zFibers.

    Returns:
        string of name of zFibers.
    """
    sel = cmds.ls(sl=True)
    cmds.select(bodies, r=True)
    zFibers = mel.eval('zQuery -t "zFiber"')
    cmds.select(sel, r=True)
    if zFibers:
        return zFibers
    else:
        return []


def get_zCloth(bodies):
    """ Gets zCloth in scene.
    Args:
        body: Maya node to find associated zCloth.

    Returns:
        string of name of zCloth.
    """
    sel = cmds.ls(sl=True)
    cmds.select(bodies, r=True)
    zCloth = mel.eval('zQuery -t "zCloth"')
    cmds.select(sel, r=True)
    if zCloth:
        return zCloth
    else:
        return []


def get_soft_bodies(selection):
    """
    Get all the soft bodies (tissue and cloth).
    This is a wrapper around get_zCloth and get_zTissues.
    """
    soft_bodies = get_zTissues(selection)
    soft_bodies.extend(get_zCloth(selection))
    return soft_bodies


def get_zFieldAdaptors(bodies):
    """ Gets zFieldAdaptors connected into some bodies.
    Args:
        bodies: List of names of Maya zTissue or zCloth nodes to get zFieldAdaptors for.

    Returns:
        list of names of zFieldAdaptor nodes.
    """
    field_adapters = []
    for body in bodies:
        fields = cmds.listConnections(body + '.fields')
        fields = none_to_empty(fields)
        field_adapters.extend(fields)
    return field_adapters


def get_fields_on_zFieldAdaptors(adaptors):
    """ Gets Maya fields connected into some zFieldAdaptors.
    Args:
        adaptors: list of names of Maya zFieldAdaptor nodes

    Returns:
        list of names of fields plugged into the adaptors.
    """
    fields = []
    for adaptor in adaptors:
        fields.extend(cmds.listConnections(adaptor + '.field'))
    return fields


def get_zTet_user_mesh(zTet):
    """ Gets the user tet mesh hooked up to a given zTet in any.

    Args:
        zTet (string): the zTet to query.

    Returns:
        str: User tet mesh.
    """
    if cmds.objExists(zTet + '.iTet'):
        mesh = cmds.listConnections(zTet + '.iTet')
        if mesh:
            return cmds.ls(mesh[0], l=True)[0]
        else:
            return mesh
    return None


def get_fiber_lineofaction(zFiber):
    """ Gets the zLineOfAction node hooked up to a given zFiber in any.

    Args:
        zFiber (string): the zFiber to query.

    Returns:
        str: zLineOfAction
    """
    if cmds.objExists(zFiber + '.iLineOfActionData'):
        conn = cmds.listConnections(zFiber + '.iLineOfActionData')
        if conn:
            return conn[0]
        else:
            return None
    else:
        return None


def get_lineOfAction_fiber(zlineofaction):
    """ Gets the zFiber node hooked up to a given zLineOfAction in any.

    Args:
        zlineofaction (string): the zLineOfAction to query.

    Returns:
        str: Name of zFiber hooked up to lineOfAction
    """
    if cmds.objExists(zlineofaction + '.oLineOfActionData'):
        conn = cmds.listConnections(zlineofaction + '.oLineOfActionData')
        if conn:
            return conn[0]
        else:
            return None
    else:
        return None


def get_association(zNode):
    """ Gets an association of given zNode

    args:
        zNode (string): the zNode to find association of.
    """
    _type = get_type(zNode)

    if _type == 'zAttachment':
        tmp = []
        tmp.extend(mel.eval('zQuery -as -l "' + zNode + '"'))
        tmp.extend(mel.eval('zQuery -at -l "' + zNode + '"'))
        # cmds.select(sel,r=True)

        return tmp

    elif _type == 'zRestShape':
        tet = cmds.listConnections('{}.iGeo'.format(zNode))[0]
        mesh = mel.eval('zQuery -type "zTissue" -l -m {}'.format(tet))
        return mesh

    elif _type == 'zFieldAdaptor':
        return []

    elif _type == 'zLineOfAction':
        tmp = cmds.listConnections(zNode + '.curves')
        return tmp

    elif _type == 'zEmbedder':
        # empty list for embedder
        return list()

    elif _type == 'zRivetToBone':
        tmp = cmds.listConnections(zNode + '.rivetMesh')
        return tmp
    else:
        cmd = 'zQuery -t "%s" -l -m "%s"' % (_type, zNode)

        if _type in ['zSolverTransform', 'zSolver']:
            return []
        else:
            mesh = mel.eval(cmd)
            return mesh


def select_tissue_meshes():
    """ Selects all zTissues in scene
    """
    cmds.select(cl=True)
    meshes = mel.eval('zQuery -t "zTissue" -m')
    cmds.select(meshes)


def check_mesh_quality(meshes):
    """ Light wrapper around checking mesh quality.

    args:
        meshes (list): A list of meshes you want to check

    Raises:
        Exception: If any mesh does not pass mesh check
    """

    tmp = []
    for s in meshes:
        cmds.select(s, r=True)
        mel.eval('ziva -mq')
        sel2 = cmds.ls(sl=True)
        if sel2[0] != s:
            tmp.extend(sel2)

    if tmp:
        cmds.select(tmp)
        raise Exception('check meshes!')
    else:
        cmds.select(meshes)


def cull_creation_nodes(scene_items, permissive=True):
    """ To help speed up the build of a Ziva setup we are creating the bones and
    the tissues with one command.  Given a list of zBuilder nodes this checks
    if a given node needs to be created in scene.  Checks to see if it
    already exists or if associated mesh is missing.  Either case it culls
    it from list.

    Args:
        permissive (bool):
        scene_items (object): the zBuilder nodes to check.
    Returns:
        dict: Dictionary of non culled
    """

    results = dict()
    results['meshes'] = []
    results['names'] = []
    results['scene_items'] = []

    # -----------------------------------------------------------------------
    # check meshes for existing zBones or zTissue
    for i, scene_item in enumerate(scene_items):
        type_ = scene_item.type
        mesh = scene_item.nice_association[0]
        name = scene_item.name

        if cmds.objExists(mesh):
            existing = mel.eval('zQuery -t "{}" {}'.format(type_, mesh))
            if existing:
                out = safe_rename(existing, name)
            else:
                results['meshes'].append(mesh)
                results['names'].append(name)
                results['scene_items'].append(scene_item)
        else:
            if not permissive:
                raise Exception(
                    '{} does not exist in scene.  Trying to make a {}.  Please check meshes.'.
                    format(mesh, type_))
            logger.warning(mesh + ' does not exist in scene, skipping ' + type_ + ' creation')

    return results


def get_zGeo_nodes_by_solverTM(ziva_builder, solverTM):
    """ Return solver and zGeo nodes by given ziva builder and solverTransform node.
    This helpfer function is for rebuilding Scene Panel 2 zGeo tree view.
    """
    solver_name = cmds.listRelatives(solverTM, shapes=True)[0]
    all_zGeo_nodes = ziva_builder.get_scene_items(
        type_filter=["zSolverTransform", "zSolver", "zBone", "zTissue", "zCloth"])
    solver_zGeo_nodes = []
    zGeo_node_types = ("zBone", "zTissue", "zCloth")
    for node in filter(lambda node: node.solver.name == solver_name, all_zGeo_nodes):
        if node.type in zGeo_node_types:
            # The zGeo tree view stores the Maya mesh each zGeo build upon,
            # it can be get through builder.geo dict
            solver_zGeo_nodes.append(ziva_builder.geo[node.nice_association[0]])
        else:
            solver_zGeo_nodes.append(node)
    return solver_zGeo_nodes