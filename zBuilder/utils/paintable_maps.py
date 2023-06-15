import re

from maya import cmds
from maya import mel
# TODO: Use Maya Python API 2.0 after Maya 2020 retires
from maya import OpenMaya as om
from maya import OpenMayaAnim as oma
from zBuilder.utils.mayaUtils import get_maya_api_version

def split_map_name(map_name):
    ''' Split map_name to node and attr, e.g.,
        u'l_tissue_1_zFiber.weightList[0].weights' -> 
        [u'l_tissue_1_zFiber', u'weightList[0].weights']

    Args:
        map_name(str): full name of a map node

    Returns:
        list of string, first one is node name, second one is attribute name
    '''
    return map_name.split('.', 1)

# TODO: Delete this helper function once Maya 2020 retires.
def _get_component(node_name, attr_name, index, deformerFn):
    if get_maya_api_version() >= 20220000:
        return deformerFn.getComponentAtIndex(index)
    
    dagPath = om.MDagPath()
    deformerFn.getPathAtIndex(index, dagPath)
    # Now find the components for that mesh.
    # This assumes that each mesh is in the deformer only once.
    # All this DagPath stuff is also assuming that the mesh is in the Dag.
    deformerSetObj = deformerFn.deformerSet()
    deformerSetFn = om.MFnSet(deformerSetObj)
    deformerSetSel = om.MSelectionList()
    deformerSetFn.getMembers(deformerSetSel, False)
    node_dot_attr = '{}.{}'.format(node_name, attr_name)
    assert deformerSetSel.length() > 0, "{} has no deformer set.".format(node_dot_attr)
    deformerSetPath = om.MDagPath()
    component = om.MObject()
    for i in range(deformerSetSel.length()):
        deformerSetSel.getDagPath(i, deformerSetPath, component)
        if deformerSetPath == dagPath:
            break
    assert deformerSetPath.isValid(), "Can't find deformer set in {}".format(node_dot_attr)
    assert (deformerSetPath == dagPath)  # This shouldn't be possible.
    return component
    
def _get_paintable_map_by_MFnWeightGeometryFilter_fallback_impl(mesh_name, node_name, attr_name):
    """ Maya 2022 introduced the "component Tag" feature.
    But it causes deformerSet() constructor to throw exception and following Maya releases haven't fix this issue.
    This helper function fallbacks to a slower version.
    """
    map_name = '{}.{}'.format(node_name, attr_name)
    if mesh_name:
        try:
            vert_count = cmds.polyEvaluate(mesh_name, v=True)
            value = cmds.getAttr('{}[0:{}]'.format(map_name, vert_count - 1))
        except Exception:
            value = cmds.getAttr(map_name)
    else:
        value = cmds.getAttr(map_name)
    return value

def get_paintable_map(node_name, attr_name, mesh_name=None):
    # type: (str, str, str) -> list[float]
    """
    Get an array of paintable weights on some node.
    This will work for array plugs (e.g. Deformer.weightList[7].weights),
    and for typed attributes with array type (e.g. zFiber.endPoints).

    For deformer weightLists, this code requires that the deformed mesh has a DagPath.
    It's also generally assumed that the weights are not sparse, even though
    that's the way Maya's weightLists generally work, because that's not the way
    ZivaVFX generally works.

    This function inspects the attribute to figure out what type it is,
    and uses the fastest method we've found for each type.

    Example inputs (node_name, attr_name) values:
        - (zTet1, weightList[0].weights)
        - (zAttachment2, weightList[1].weights)
        - (zFiber1, endPoints)
        - (zBoneWarp1, landmarkList[0].landmarks)
    """
    # There are 3 cases we need to distinguish between:
    # 1) attribute is a kFooArray
    # 2) attribute is deformer weightList[i].weights
    # 3) attribute is a another multi-array (with UseArrayBuilder=true)
    # Multi-arrays with UseArrayBuilder=False are a mistake and we are okay to fail.
    # These are all of the array-like paintable things.

    # Attribute query is a natural way to find out if something is a multi,
    # but this syntax doesn't work: <<attributeQuery -node "zFiber1" -m "weightList[0].weights">>
    # So we need to pull out the child-most part.
    child_attr = attr_name.split('.')[-1]  # 'weightList[0].weights' --> 'weights'
    is_multi = cmds.attributeQuery(child_attr, node=node_name, multi=True)
    if not is_multi:
        # case 1
        return get_paintable_map_by_getAttr_numericArray(node_name, attr_name)

    is_deformer = 'weightGeometryFilter' in cmds.nodeType(node_name, inherited=True)
    if is_deformer and child_attr == 'weights':
        # case 2
        try:
            return get_paintable_map_by_MFnWeightGeometryFilter(node_name, attr_name)
        except RuntimeError:
            # TODO: revisit after Maya 2022 retires
            return _get_paintable_map_by_MFnWeightGeometryFilter_fallback_impl(mesh_name, node_name, attr_name)
    # case 3
    return get_paintable_map_by_ArrayDataBuilder(node_name, attr_name)

def get_paintable_map_by_MFnWeightGeometryFilter(node_name, attr_name):
    """ 
    This only works for deformer weightList attributes,
    e.g., zTet.weightList[i].weights, or zAttachment, etc.
    """
    # To use MFnWeightGeometryFilter.getWeights is the fastest way we've found to
    # get weights from Python. To call that function we need the DagPath
    # and Components for the mesh we're getting the weights for.
    # Unfortunately, there's no easy way to get that information.
    # The deformerSetFn.getMembers can get be used to get all of the meshes and
    # components that a deformer is deforming, but they don't come out in the
    # same order as the deformer index. The solution used here is to search through
    # this list, looking for the expected DagPath. This is O(numMeshes) instead of O(1) :(

    # Get the index in the weightList
    m = re.search(r'^weightList\[(\d+)\].weights$', attr_name)
    if not m:
        raise Exception(
            'MFnWeightGeometryFilter only works on deformer weight lists, but {} does not appear to be a weights attribute'
            .format(attr_name))
    index = int(m.group(1))  # group(0) is the whole match. group(1) is the index

    # Which DagPath of the thing we're _supposed_ to be getting weights for
    deformerObj = _get_mobject(node_name)
    deformerFn = oma.MFnWeightGeometryFilter(deformerObj)
    comp = _get_component(node_name, attr_name, index, deformerFn)
    
    weightList = om.MFloatArray()    
    deformerFn.getWeights(index, comp, weightList)
    # Convert and return Python list type data to align with other get weightmap methods.
    return list(weightList)


def get_paintable_map_by_ArrayDataBuilder(node_name, attr_name):
    """ 
    This only works for multi/array attributes,
    e.g. zTet.weightList[i].weights and zBoneWarp.landmarkList[i].landmarks.
    Note that weightList.weights can also be set with ``get_paintable_map_by_MFnWeightGeometryFilter``,
    which is faster in benchmarks.
    """
    get_func_lookup = {
        om.MFnNumericData.kFloat: (lambda handle: handle.asFloat()),
        om.MFnNumericData.kDouble: (lambda handle: handle.asDouble()),
        om.MFnNumericData.kInt: (lambda handle: handle.asInt())
    }  # add other types as needed

    weights_plug = _get_MPlug(node_name, attr_name)
    mfnattr = om.MFnNumericAttribute(weights_plug.attribute())
    get_value = get_func_lookup[mfnattr.unitType()]

    dataHandle = weights_plug.asMDataHandle()
    weightList = []
    try:
        arrayDataHandle = om.MArrayDataHandle(dataHandle)
        nCount = arrayDataHandle.elementCount()
        while nCount > 0:
            dataHandle_i = arrayDataHandle.outputValue()
            weightList.append(get_value(dataHandle_i))
            # According to OpenMaya.MArrayDataHandle.next() doc,
            # it should return True if there was a next element and False if there wasn't.
            # But actually it returns None!
            # What's worse, the last element call raise exception:
            #   # Error: RuntimeError: file <maya console> line 1: (kFailure): Unexpected Internal Failure #
            # So here we add an extra check to prevent it raise exception.
            if nCount > 1:
                arrayDataHandle.next()
            nCount -= 1
    finally:
        weights_plug.destructHandle(dataHandle)

    return weightList


def get_paintable_map_by_getAttr_numericArray(node_name, attr_name):
    """ 
    This only works for attributes of type kFooArray (e.g. kFloatArray, etc), 
    e.g., zFiber.endPoints.
    """
    node_dot_attr = '{}.{}'.format(node_name, attr_name)
    datatype = cmds.getAttr(node_dot_attr, type=True)
    if not datatype.endswith('Array'):
        raise AttributeError('Unsupported: {} is type {}, not some sort of array'.format(
            node_dot_attr, datatype))
    return cmds.getAttr(node_dot_attr)


def _set_paintable_map_by_MFnWeightGeometryFilter_fallback_impl(node_name, attr_name, map_value):
    """ Maya 2022 introduced the "component Tag" feature.
    But it causes deformerSet() constructor to throw exception and following Maya releases haven't fix this issue.
    This helper function fallbacks to a slower version.
    """
    map_name = '{}.{}'.format(node_name, attr_name)
    weight_map = '{}[0]'.format(map_name)
    if cmds.objExists(weight_map):
        if not cmds.getAttr(weight_map, l=True):
            tmp = []
            for w in map_value:
                tmp.append(str(w))
            val = ' '.join(tmp)
            cmd = "setAttr {}[0:{}] {}".format(map_name, len(map_value) - 1, val)
            mel.eval(cmd)
    else:
        # applying doubleArray maps
        if cmds.objExists(map_name):
            cmds.setAttr(map_name, map_value, type='doubleArray')


def set_paintable_map(node_name, attr_name, new_weights):
    # type: (str, str, List[float]) -> None
    """
    Set an array of paintable weights on some node.
    This will work for array plugs (e.g. Deformer.weightList[7].weights),
    and for typed attributes with array type (e.g. zFiber.endPoints).

    For deformer weightLists, this code requires that the deformed mesh has a DagPath.
    It's also generally assumed that the weights are not sparse, even though
    that's the way Maya's weightLists generally work, because that's not the way
    ZivaVFX generally works.

    This function inspects the attribute to figure out what type it is,
    and uses the fastest method we've found for each type.

    The _real_ reason this is important is that on referenced nodes,
    some of obvious methods for setting weights take time O(N^2) in the length of the array.
    For example, using mel: "setAttr node.weightList[0].weights[0:1] 1 2 0 1 2 1 1 1 2 2 2 ...".
    These O(N^2) routines can easily take tens of minutes on a few 100k vertices.

    Example inputs (node_name, attr_name) values:
        - (zTet1, weightList[0].weights)
        - (zAttachment2, weightList[1].weights)
        - (zFiber1, endPoints)
        - (zBoneWarp1, landmarkList[0].landmarks)
    """
    # There are 3 cases we need to distinguish between:
    # 1) attribute is a kFooArray
    # 2) attribute is deformer weightList[i].weights
    # 3) attribute is a another multi-array (with UseArrayBuilder=true)
    # Multi-arrays with UseArrayBuilder=False are a mistake and we are okay to fail.
    # These are all of the array-like paintable things.

    # Attribute query is a natural way to find out if something is a multi,
    # but this syntax doesn't work: <<attributeQuery -node "zFiber1" -m "weightList[0].weights">>
    # So we need to pull out the child-most part.
    child_attr = attr_name.split('.')[-1]  # 'weightList[0].weights' --> 'weights'
    is_multi = cmds.attributeQuery(child_attr, node=node_name, multi=True)
    if not is_multi:
        # case 1
        set_paintable_map_by_setAttr_numericArray(node_name, attr_name, new_weights)
        return
    
    is_deformer = 'weightGeometryFilter' in cmds.nodeType(node_name, inherited=True)
    if is_deformer and child_attr == 'weights':
        # case 2
        try:
            set_paintable_map_by_MFnWeightGeometryFilter(node_name, attr_name, new_weights)
        except RuntimeError:
            # TODO: revisit after Maya 2022 retires
            _set_paintable_map_by_MFnWeightGeometryFilter_fallback_impl(node_name, attr_name, new_weights)
        return
    
    # case 3
    set_paintable_map_by_ArrayDataBuilder(node_name, attr_name, new_weights)
    
def set_paintable_map_by_MFnWeightGeometryFilter(node_name, attr_name, new_weights):
    """ 
    This only works for deformer weightList attributes,
    e.g., zTet.weightList[i].weights, or zAttachment, etc.
    """
    # To use MFnWeightGeometryFilter.setWeight is the fastest way we've found to
    # set weights from Python. To call that function we need the DagPath
    # and Components for the mesh we're setting the weights for.
    # Unfortunately, there's no easy way to get that information.
    # The deformerSetFn.getMembers can get be used to get all of the meshes and
    # components that a deformer is deforming, but they don't come out in the
    # same order as the deformer index. The solution used here is to search through
    # this list, looking for the expected DagPath. This is O(numMeshes) instead of O(1) :(

    # Get the index in the weightList
    m = re.search(r'^weightList\[(\d+)\].weights$', attr_name)
    if not m:
        raise Exception(
            'MFnWeightGeometryFilter only works on deformer weight lists, but {} does not appear to be a weights attribute'
            .format(attr_name))
    index = int(m.group(1))  # group(0) is the whole match. group(1) is the index

    # Convert the Python list to an MFloatArray
    weightList = om.MFloatArray()
    weightList.setLength(len(new_weights))
    for i, w in enumerate(new_weights):
        weightList[i] = w

    # Which DagPath of the thing we're _supposed_ to be setting weights for
    deformerObj = _get_mobject(node_name)
    deformerFn = oma.MFnWeightGeometryFilter(deformerObj)
    dagPath = om.MDagPath()
    deformerFn.getPathAtIndex(index, dagPath)
    comp = _get_component(node_name, attr_name, index, deformerFn)
    deformerFn.setWeight(dagPath, index, comp, weightList)


def set_paintable_map_by_ArrayDataBuilder(node_name, attr_name, new_weights):
    """ 
    This only works for multi/array attributes,
    e.g., zTet.weightList[i].weights and zBoneWarp.landmarkList[i].landmarks.
    Note that weightList.weights can also be set with ``set_paintable_map_by_MFnWeightGeometryFilter``,
    which is faster in benchmarks.
    """
    set_func_lookup = {
        om.MFnNumericData.kFloat: om.MDataHandle.setFloat,
        om.MFnNumericData.kDouble: om.MDataHandle.setDouble,
        om.MFnNumericData.kInt: om.MDataHandle.setInt
    }  # add other types as needed

    weights_plug = _get_MPlug(node_name, attr_name)
    mfnattr = om.MFnNumericAttribute(weights_plug.attribute())
    set_value = set_func_lookup[mfnattr.unitType()]

    dataHandle = weights_plug.asMDataHandle()
    try:
        arrayDataHandle = om.MArrayDataHandle(dataHandle)
        builder = arrayDataHandle.builder()

        current_size = builder.elementCount()
        builder.growArray(max(0, len(new_weights) - current_size))

        for i in range(len(new_weights)):
            dataHandle_i = builder.addElement(i)
            set_value(dataHandle_i, new_weights[i])

        arrayDataHandle.set(builder)
        weights_plug.setMDataHandle(dataHandle)
    finally:
        weights_plug.destructHandle(dataHandle)


def set_paintable_map_by_setAttr_numericArray(node_name, attr_name, new_weights):
    """ 
    This only works for attributes of type kFooArray (e.g. kFloatArray, etc),
    e.g., zFiber.endPoints.
    """
    node_dot_attr = '{}.{}'.format(node_name, attr_name)
    datatype = cmds.getAttr(node_dot_attr, type=True)
    if not datatype.endswith('Array'):
        raise AttributeError('Unsupported: {} is type {}, not some sort of array'.format(
            node_dot_attr, datatype))
    cmds.setAttr(node_dot_attr, new_weights, type=datatype)


def _get_mobject(node_name):
    sel = om.MSelectionList()
    sel.add(node_name)
    node_obj = om.MObject()
    sel.getDependNode(0, node_obj)
    return node_obj


def _get_MPlug(node_name, attr_name):
    """
    Given a node name (e.g. "zBoneWarp1") and 
    a plug name (e.g. "weightList[0].weights"), 
    get on om.MPlug for that plug
    (e.g for "zBoneWarp1.weightList[0].weights")
    """
    sel = om.MSelectionList()
    sel.add(node_name + '.' + attr_name)
    plug = om.MPlug()
    sel.getPlug(0, plug)
    return plug
