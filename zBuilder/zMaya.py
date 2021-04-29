from zBuilder.commonUtils import none_to_empty
from zBuilder.mayaUtils import safe_rename
from maya import cmds
from maya import mel
import logging

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


def isSolver(selection):
    """ Checks if passed is zSolver or zSolverTransform.
    Args:
        selection: Item of interest.

    Returns:
        True if it is solver, else false.
    """
    isSolver = False
    for s in selection:
        if cmds.objectType(s) == 'zSolver' or cmds.objectType(s) == 'zSolverTransform':
            isSolver = True
            continue
    return isSolver


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
    _type = cmds.objectType(zNode)

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


def strip_namespace(node):
    return node.split(':')[-1]


def znode_rename_helper(zNode, postfix, solver, replace):
    """
    Helper for cases when need to rename nodes like:
    zMaterial1, zMaterial4, zMaterial25 to
    zMaterial1, zMaterial2, zMaterial3
    And not to rename nodes like:
    zMaterial1, zMaterial2, zMaterial3 to
    zMaterial4, zMaterial5, zMaterial6
    Args:
        zNode (string): node type
        postfix (string): postfix to use for renaming
        solver (string): solver name
        replace (list): list of strings to remove from the new name

    Returns:
        tuple of lists: old names, new names
    """

    # store data to print results later
    old_names = []
    new_names = []
    items = mel.eval('zQuery -t "{}" {}'.format(zNode, solver))
    if items:
        for item in items:
            mesh = mel.eval('zQuery -t "{}" -m "{}"'.format(zNode, item))[0]
            for r in replace:
                mesh = mesh.replace(r, '')
            mesh = strip_namespace(mesh)
            new_name = '{}_{}'.format(mesh, zNode)
            if zNode in ['zMaterial', 'zFiber']:
                new_name += '1'
            if item != new_name:
                new_name = safe_rename(item, '{}{}'.format(new_name, postfix))
                if new_name:
                    old_names.append(item)
                    new_names.append(new_name)

    return old_names, new_names


def rivet_to_bone_rename_helper(rtbs, postfix, replace):
    """
    The same idea as for znode_rename_helper but for zRivetToBone
    Args:
        rtbs (list): list of zRivetToBone nodes to rename
        postfix (string): postfix to use for renaming
        replace (list): list of strings to remove from the new name

    Returns:
        tuple of lists: old names, new names
    """
    old_names = []
    new_names = []
    for rtb in rtbs:
        crv = cmds.listConnections(rtb + '.outputGeometry', shapes=True)
        # If curve has multiple zRivetToBone nodes, need to search zRivetToBone connections
        # until curve is found
        while crv:
            if cmds.nodeType(crv[0]) == 'nurbsCurve':
                break
            else:
                crv = cmds.listConnections(crv[0] + '.outputGeometry', shapes=True)
        crv = cmds.listRelatives(crv, p=True)
        if crv:
            crv = crv[0]
            for r in replace:
                crv = crv.replace(r, '')
            crv = strip_namespace(crv)
            new_name = '{}_{}'.format(crv, 'zRivetToBone1')
            if rtb != new_name:
                new_name = safe_rename(rtb, '{}{}'.format(new_name, postfix))
                if new_name:
                    old_names.append(rtb)
                    new_names.append(new_name)

    return old_names, new_names


def rename_ziva_nodes(replace=['_muscle', '_bone']):
    """ Renames zNodes based on mesh it's connected to.

    args:
        replace (list): subset of mesh name to replace with zNode name

    * zFiber: <meshName>_zFiber
    * zMaterial: <meshName>_zMaterial
    * zTet: <meshName>_zTet
    * zTissue: <meshName>_zTissue
    * zBone: <meshName>_zBone
    * zCloth: <meshName>_zCloth
    * zRestShape: <meshName>_zRestShape
    * zAttachment: <sourceMesh>__<destinationMesh>_zAttachment
    """
    solver = mel.eval('zQuery -t "zSolver"')

    if not solver:
        logger.error("No solver found for current selection !")
        return

    zNodes = ['zTissue', 'zTet', 'zMaterial', 'zFiber', 'zBone', 'zCloth', 'zRestShape']

    for zNode in zNodes:
        old_names, _ = znode_rename_helper(zNode, '_tmp', solver[0], replace)
        # looping through this twice to get around how maya renames stuff
        _, new_names = znode_rename_helper(zNode, '', solver[0], replace)
        for i, item in enumerate(old_names):
            logger.info('rename: {} to {}'.format(item, new_names[i]))

    # rename zLineOfAction nodes
    loas = mel.eval('zQuery -loa {}'.format(solver[0]))
    if loas:
        for loa in loas:
            crv = cmds.listConnections(loa + '.oLineOfActionData')
            if crv:
                crv = strip_namespace(crv[0])
                new_name = crv.replace('_zFiber', '_zLineOfAction')
                new_name = safe_rename(loa, new_name)
                if new_name:
                    logger.info('rename: {} to {}'.format(loa, new_name))

    # rename zRivetToBone nodes
    rtbs = mel.eval('zQuery -rtb {}'.format(solver[0]))
    if rtbs:
        old_names, new_names = rivet_to_bone_rename_helper(rtbs, '_tmp', replace)
        _, new_names = rivet_to_bone_rename_helper(new_names, '', replace)

        for i, item in enumerate(old_names):
            logger.info('rename: {} to {}'.format(item, new_names[i]))

    attachments = mel.eval('zQuery -t "{}" {}'.format('zAttachment', solver[0]))
    if attachments:
        for attachment in attachments:
            s = mel.eval('zQuery -as {}'.format(attachment))[0]
            for r in replace:
                s = s.replace(r, '')
            s = strip_namespace(s)
            t = mel.eval('zQuery -at {}'.format(attachment))[0]
            for r in replace:
                t = t.replace(r, '')
            # remove namespace from target mesh
            t = strip_namespace(t)
            new_name = '{}__{}_{}'.format(s, t, 'zAttachment')
            new_name = safe_rename(attachment, new_name)
            if new_name:
                logger.info('rename: {} to {}'.format(attachment, new_name))

    logger.info('finished renaming.... ')


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


def check_map_validity(map_parameters):
    """
    This checks the map validity for zAttachments and zFibers.  For zAttachments
    it checks if all the values are zero.  If so it failed and turns off the
    associated zTissue node.  For zFibers it checks to make sure there are at least
    1 value of 0 and 1 value of .5 within a .1 threshold.  If not that fails and
    turns off the zTissue

    Args:
        map_parameters: map parameters to check.
    Returns:
        list of offending maps
    """
    sel = cmds.ls(sl=True)

    report = []
    for parameter in map_parameters:
        if cmds.objExists(parameter.name):
            map_type = cmds.objectType(parameter.name)
            if map_type == 'zAttachment':
                values = parameter.values
                if all(v == 0 for v in values):
                    report.append(parameter.name)
                    dg_node = parameter.name.split('.')[0]
                    tissue = mel.eval('zQuery -type zTissue {}'.format(dg_node))
                    cmds.setAttr('{}.enable'.format(tissue[0]), 0)

            if map_type == 'zFiber' and 'endPoints' in parameter.name:
                values = parameter.values
                upper = False
                lower = False

                if any(0 <= v <= .1 for v in values):
                    lower = True
                if any(.9 <= v <= 1 for v in values):
                    upper = True

                if not upper or not lower:
                    report.append(parameter.name)
                    dg_node = parameter.name.split('.')[0]
                    tissue = mel.eval('zQuery -type zTissue {}'.format(dg_node))
                    cmds.setAttr('{}.enable'.format(tissue[0]), 0)

    if report:
        logger.info('Check these maps: {}'.format(report))
    cmds.select(sel)
    return report
