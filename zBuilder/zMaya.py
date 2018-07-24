import re

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
    'zCacheTransform',
    'zFieldAdaptor']
""" All available ziva nodes to be able to cleanup. """


def get_mesh_connectivity(mesh_name):
    """ Gets mesh connectivity for given mesh.

    Args:
        mesh_name: Name of mesh to process.

    Returns:
        dict: Dictionary of polygonCounts, polygonConnects, and points.
    """
    space = om.MSpace.kWorld
    mesh_to_rebuild_m_dag_path = get_mdagpath_from_mesh(mesh_name)
    mesh_to_rebuild_m_dag_path.extendToShape()

    mesh_to_rebuild_poly_iter = om.MItMeshPolygon(mesh_to_rebuild_m_dag_path)
    mesh_to_rebuild_vert_iter = om.MItMeshVertex(mesh_to_rebuild_m_dag_path)

    num_polygons = 0
    num_vertices = 0
    # vertexArray_mFloatPointArray = om.MFloatPointArray()
    # polygonCounts_mIntArray = om.MIntArray()
    polygon_counts_list = list()
    polygon_connects_list = list()
    point_list = list()

    while not mesh_to_rebuild_vert_iter.isDone():
        num_vertices += 1
        pos_m_point = mesh_to_rebuild_vert_iter.position(space)
        pos_m_float_point = om.MFloatPoint(pos_m_point.x, pos_m_point.y,
                                         pos_m_point.z)

        point_list.append([
            pos_m_float_point[0],
            pos_m_float_point[1],
            pos_m_float_point[2]
        ])
        mesh_to_rebuild_vert_iter.next()

    while not mesh_to_rebuild_poly_iter.isDone():
        num_polygons += 1
        polygon_vertices_m_int_array = om.MIntArray()
        mesh_to_rebuild_poly_iter.getVertices(polygon_vertices_m_int_array)
        for vertexIndex in polygon_vertices_m_int_array:
            polygon_connects_list.append(vertexIndex)

        polygon_counts_list.append(polygon_vertices_m_int_array.length())

        mesh_to_rebuild_poly_iter.next()
    tmp = dict()
    tmp['polygonCounts'] = polygon_counts_list
    tmp['polygonConnects'] = polygon_connects_list
    tmp['points'] = point_list

    return tmp


def check_body_type(bodies):
    """ Checks if given bodies are either zTissue, zCloth and or zBone.  Mostly
    used to see if we can create a zAttachment before we try.  Additionally
    does a check if all objects exist in scene.

    Args:
        bodies (list):  List of bodies we want to check type of.  

    Returns:
        (bool): True if all bodies pass test, else False.
    """
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
    """ Really light wrapper for getting type of maya node.  Ya, I know.

    Args:
        body (str): Maya node to get type of

    Returns:
        str: String of node type.

    """
    try:
        return mc.objectType(body)
    except:
        pass


def clean_scene():
    """ Deletes all ziva nodes in scene.  Effectively cleaning it up.
    """
    for node in ZNODES:
        in_scene = mc.ls(type=node)
        if len(in_scene) > 0:
            mc.delete(in_scene)


def get_zSolver(body):
    """ Gets zSolver in scene.
    Args:
        body: Maya node to find associated solver.

    Returns:
        returns long name of zSolver.
    """
    sel = mc.ls(sl=True)
    mc.select(body, r=True)
    solver = mm.eval('zQuery -t "zSolver" -l')
    mc.select(sel, r=True)
    return solver


def get_zSolverTransform(body):
    """ Gets zSolverTransform in scene.
    Args:
        body: Maya node to find associated solverTransform.

    Returns:
        returns long name of zSolverTransform.
    """
    sel = mc.ls(sl=True)
    mc.select(body, r=True)
    solver = mm.eval('zQuery -t "zSolverTransform" -l')
    mc.select(sel, r=True)
    return solver


def get_zAttachments(bodies):
    """ Gets zAttachments in scene.
    Args:
        body: Maya node to find associated zAttachments.

    Returns:
        string of name of zAttachments.
    """
    sel = mc.ls(sl=True)
    mc.select(bodies, r=True)
    attachments = mm.eval('zQuery -t zAttachment')
    mc.select(sel, r=True)
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
        if mc.objectType(s) == 'zSolver' or mc.objectType(
                s) == 'zSolverTransform':
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
                mesh1 = mm.eval('zQuery -as -l "' + attachment + '"')
                mesh2 = mm.eval('zQuery -at -l "' + attachment + '"')
                mc.select(mesh1, mesh2, r=True)
                tmp = mm.eval('zQuery -t "zBone"')
                if tmp:
                    bones.extend(tmp)

        # mc.select(bodies,r=True)
        mc.select(sel, r=True)
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
    sel = mc.ls(sl=True)
    mc.select(bodies, r=True)
    zTets = mm.eval('zQuery -t "zTet"')
    mc.select(sel, r=True)
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
    sel = mc.ls(sl=True)
    mc.select(bodies, r=True)
    zTissues = mm.eval('zQuery -t "zTissue"')
    mc.select(sel, r=True)
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
    sel = mc.ls(sl=True)
    mc.select(bodies, r=True)
    zMaterial = mm.eval('zQuery -t "zMaterial"')
    mc.select(sel, r=True)
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
    sel = mc.ls(sl=True)
    mc.select(bodies, r=True)
    zFibers = mm.eval('zQuery -t "zFiber"')
    mc.select(sel, r=True)
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
    sel = mc.ls(sl=True)
    mc.select(bodies, r=True)
    zCloth = mm.eval('zQuery -t "zCloth"')
    mc.select(sel, r=True)
    if zCloth:
        return zCloth
    else:
        return []


def get_zTet_user_mesh(zTet):
    """ Gets the user tet mesh hooked up to a given zTet in any.

    Args:
        zTet (string): the zTet to query.

    Returns:
        str: User tet mesh.
    """
    if mc.objExists(zTet + '.iTet'):
        mesh = mc.listConnections(zTet + '.iTet')
        if mesh:
            return mc.ls(mesh[0], l=True)[0]
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
    if mc.objExists(zFiber + '.iLineOfActionData'):
        conn = mc.listConnections(zFiber + '.iLineOfActionData')
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
    if mc.objExists(zlineofaction + '.oLineOfActionData'):
        conn = mc.listConnections(zlineofaction + '.oLineOfActionData')
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
    _type = mc.objectType(zNode)

    if _type == 'zAttachment':
        tmp = []
        tmp.extend(mm.eval('zQuery -as -l "' + zNode + '"'))
        tmp.extend(mm.eval('zQuery -at -l "' + zNode + '"'))
        # mc.select(sel,r=True)

        return tmp

    elif _type == 'zFieldAdaptor':
        return []

    elif _type == 'zLineOfAction':
        tmp = mc.listConnections(zNode + '.curves')
        return tmp

    elif _type == 'zEmbedder':
        # empty list for embedder
        return list()

    else:
        cmd = 'zQuery -t "%s" -l -m "%s"' % (_type, zNode)

        if _type in ['zSolverTransform', 'zSolver']:
            return []
        else:
            mesh = mm.eval(cmd)
            return mesh


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
    * zAttachment: <sourceMesh>__<destinationMesh>_zAttachment
    """
    sel = mc.ls(sl=True)
    solver = mm.eval('zQuery -t "zSolver"')

    zNodes = ['zTissue', 'zTet', 'zMaterial', 'zFiber', 'zBone', 'zCloth']

    for zNode in zNodes:
        items = mm.eval('zQuery -t "{}" {}'.format(zNode, solver[0]))
        if items:
            for item in items:
                mesh = mm.eval('zQuery -t "{}" -m "{}"'.format(zNode, item))[0]
                for r in replace:
                    mesh = mesh.replace(r, '')
                if item != '{}_{}'.format(mesh, zNode):
                    mc.rename(item, '{}_{}tmp'.format(mesh, zNode))

        # looping through this twice to get around how maya renames stuff
        items = mm.eval('zQuery -t "{}" {}'.format(zNode, solver[0]))
        if items:
            for item in items:
                mesh = mm.eval('zQuery -t "{}" -m "{}"'.format(zNode, item))[0]
                for r in replace:
                    mesh = mesh.replace(r, '')
                if item != '{}_{}'.format(mesh, zNode):
                    mc.rename(item, '{}_{}'.format(mesh, zNode))
                    print 'rename: ', item, '{}_{}'.format(mesh, zNode)

    # for now doing an ls type for lineOfActions until with have zQuery support
    loas = mc.ls(type='zLineOfAction')
    if loas:
        for loa in loas:
            crv = mc.listConnections(loa + '.oLineOfActionData')
            if crv:
                mc.rename(loa, crv[0].replace('_zFiber', '_zLineOfAction'))

    attachments = mm.eval('zQuery -t "{}" {}'.format('zAttachment', solver[0]))
    if attachments:
        for attachment in attachments:
            s = mm.eval('zQuery -as {}'.format(attachment))[0]
            for r in replace:
                s = s.replace(r, '')
            t = mm.eval('zQuery -at {}'.format(attachment))[0]
            for r in replace:
                t = t.replace(r, '')
            if attachment != '{}__{}_{}'.format(s, t, 'zAttachment'):
                mc.rename(attachment, '{}__{}_{}'.format(s, t, 'zAttachment'))
                print 'rename: ', attachment, '{}__{}_{}'.format(s, t,
                                                                 'zAttachment')

    logger.info('finished renaming.... ')


def select_tissue_meshes():
    """ Selects all zTissues in scene
    """
    mc.select(cl=True)
    meshes = mm.eval('zQuery -t "zTissue" -m')
    mc.select(meshes)


def get_mdagpath_from_mesh(mesh_name):
    """ Maya stuff, getting the dagpath from a mesh name

    Args:
        mesh_name: The mesh to get dagpath from.
    """
    mesh_m_dag_path = om.MDagPath()
    sel_list = om.MSelectionList()
    sel_list.add(mesh_name)
    sel_list.getDagPath(0, mesh_m_dag_path)

    return mesh_m_dag_path


def get_name_from_m_object(m_object, long_name=True):
    """ Gets maya scene name from given mObject.
    Args:
        m_object: The m_object to get name from.
        long_name: Returns long name. Default = ``True``

    Returns:
        str: Maya object name.

    """
    if m_object.hasFn(om.MFn.kDagNode):
        dagpath = om.MDagPath()
        om.MFnDagNode(m_object).getPath(dagpath)
        if long_name:
            name = dagpath.fullPathName()
        else:
            name = dagpath.partialPathName()
    else:
        name = om.MFnDependencyNode(m_object).name()
    return name


def check_mesh_quality(meshes):
    """ Light wrapper around checking mesh quality.

    args:
        meshes (list): A list of meshes you want to check

    Raises:
        StandardError: If any mesh does not pass mesh check
    """

    tmp = []
    for s in meshes:
        mc.select(s, r=True)
        mm.eval('ziva -mq')
        sel2 = mc.ls(sl=True)
        if sel2[0] != s:
            tmp.extend(sel2)

    if tmp:
        mc.select(tmp)
        raise StandardError, 'check meshes!'
    else:
        mc.select(meshes)


def check_maya_node(maya_node):
    """

    Args:
        maya_node:

    Returns:

    """
    if isinstance(maya_node, list):
        return maya_node[0]
    else:
        return maya_node


def parse_maya_node_for_selection(args):
    """
    This is used to check passed args in a function to see if they are valid
    maya objects in the current scene.  If any of the passed names are not in
    the  it raises a StandardError.  If nothing is passed it looks at what is
    actively selected in scene to get selection.  This way it functions like a
    lot of the maya tools, uses what is passed OR it uses what is selected.

    Args:
        args: The args to test

    Returns:
        (list) maya selection

    """
    selection = None
    if len(args) > 0:
        if isinstance(args[0], (list, tuple)):
            selection = args[0]
        else:
            selection = [args[0]]

        tmp = []
        # check if it exists and get long name----------------------------------
        for sel in selection:
            if mc.objExists(sel):
                tmp.extend(mc.ls(sel, l=True))
            else:
                raise StandardError, '{} does not exist in scene, stopping!'.format(
                    sel)
        selection = tmp

    # if nothing valid has been passed then we check out active selection in
    # maya.
    if not selection:
        selection = mc.ls(sl=True, l=True)
        # if still nothing is selected then we raise an error
        if not selection:
            raise StandardError, 'Nothing selected or passed, please select something and try again.'
    return selection


def build_attr_list(selection, attr_filter=None):
    """
    Builds a list of attributes to store values for.  It is looking at keyable
    attributes and if they are in channelBox.

    Args:
        attr_filter:
        selection (str): maya object to find attributes

    returns:
        list: list of attributes names
    """
    attributes = []
    keyable = mc.listAttr(selection, k=True)
    channel_box = mc.listAttr(selection, cb=True)
    if channel_box:
        attributes.extend(channel_box)
    if keyable:
        attributes.extend(keyable)
 
    attribute_names = []
    for attr in attributes:
        obj = '{}.{}'.format(selection, attr)
        if mc.objExists(obj):
            type_ = mc.getAttr(obj, type=True)
            if not type_ == 'TdataCompound':
                attribute_names.append(attr)

    if attr_filter:
        attrs = attr_filter

    return attribute_names


def build_attr_key_values(selection, attr_list):
    """ Builds a dictionary of attribute key/values.  Stores the value, type, and
    locked status.
    Args:
        selection: Items to save attrbutes for.
        attr_list: List of attributes to save.

    Returns:
        dict: of attribute values.

    """
    attr_dict = {}
    for attr in attr_list:
        obj = '{}.{}'.format(selection, attr)
        for item in mc.ls(obj):
            type_ = mc.getAttr(item, type=True)
            if not type_ == 'TdataCompound':
                attr_dict[attr] = {}
                attr_dict[attr]['type'] = type_
                attr_dict[attr]['value'] = mc.getAttr(item)
                attr_dict[attr]['locked'] = mc.getAttr(item, lock=True)
                attr_dict[attr]['alias'] = mc.aliasAttr(obj, q=True)

    return attr_dict


def replace_long_name(search, replace, long_name):
    """ does a search and replace on a long name.  It splits it up by ('|') then
    performs it on each piece

    Args:
        search (str): search term
        replace (str): replace term
        long_name (str): the long name to perform action on

    returns:
        str: result of search and replace
    """
    items = long_name.split('|')
    new_name = ''
    for i in items:
        if i:
            i = re.sub(search, replace, i)
            if '|' in long_name:
                new_name += '|' + i
            else:
                new_name += i

    #if new_name != long_name:
    #    logger.info('replacing name: {}  {}'.format(long_name, new_name))

    return new_name


def replace_dict_keys(search, replace, dictionary):
    """
    Does a search and replace on dictionary keys

    Args:
        search (:obj:`str`): search term
        replace (:obj:`str`): replace term
        dictionary (:obj:`dict`): the dictionary to do search on

    Returns:
        :obj:`dict`: result of search and replace
    """
    tmp = {}
    for key in dictionary:
        new = replace_long_name(search, replace, key)
        tmp[new] = dictionary[key]

    return tmp


def cull_creation_nodes(parameters, permissive=True):
    """ To help speed up the build of a Ziva setup we are creating the bones and
    the tissues with one command.  Given a list of zBuilder nodes this checks
    if a given node needs to be created in scene.  Checks to see if it
    already exists or if associated mesh is missing.  Either case it culls
    it from list.

    Args:
        permissive (bool):
        parameters (object): the zBuilder nodes to check.
    Returns:
        dict: Dictionary of non culled
    """

    results = dict()
    results['meshes'] = []
    results['names'] = []
    results['parameters'] = []

    # -----------------------------------------------------------------------
    # check meshes for existing zBones or zTissue
    for i, parameter in enumerate(parameters):
        type_ = parameter.type
        mesh = parameter.association[0]
        name = parameter.name

        if mc.objExists(mesh):
            existing = mm.eval('zQuery -t "{}" {}'.format(type_, mesh))
            if existing:
                out = mc.rename(existing, name)
                parameter.mobject = out
            else:
                results['meshes'].append(mesh)
                results['names'].append(name)
                results['parameters'].append(parameter)
        else:
            if not permissive:
                raise StandardError('{} does not exist in scene.  Trying to make a {}.  Please check meshes.'.format(mesh, type_))
            logger.warning(
                mesh + ' does not exist in scene, skipping ' + type_ + ' creation')

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
    sel = mc.ls(sl=True)

    report = []
    for parameter in map_parameters:
        if mc.objExists(parameter.name):
            map_type = mc.objectType(parameter.name)
            if map_type == 'zAttachment':
                values = parameter.values
                if all(v == 0 for v in values):
                    report.append(parameter.name)
                    dg_node = parameter.name.split('.')[0]
                    tissue = mm.eval('zQuery -type zTissue {}'.format(dg_node))
                    mc.setAttr('{}.enable'.format(tissue[0]), 0)

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
                    tissue = mm.eval('zQuery -type zTissue {}'.format(dg_node))
                    mc.setAttr('{}.enable'.format(tissue[0]), 0)

    if report:
        logger.info('Check these maps: {}'.format(report))
    mc.select(sel)
    return report

