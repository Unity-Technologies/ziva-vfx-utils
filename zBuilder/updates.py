import inspect
import sys

from collections import defaultdict
from zBuilder.nodes.deformer import construct_map_names
from zBuilder.builders.builder import find_class
from zBuilder.mayaUtils import get_short_name


def update_json_pre_1_0_11(json_object):
    class_type_name = json_object.get('type', 'Base')
    class_type = find_class(json_object['_builder_type'], class_type_name)

    if class_type_name in _get_node_types_with_maps():
        json_object['parameters'] = defaultdict(list)
        map_names = construct_map_names(json_object['_name'], class_type.MAP_LIST)
        json_object['parameters']['map'].extend(map_names)

        # the association holds the mesh name associated with node.  Currently the only
        # use for meshes in zBuilder is for interpolating weight maps if needed.
        # this means that a mesh is only stored for a node if it has a map.

        # first we need to use short name for mesh
        meshes = [get_short_name(x) for x in json_object['_association']]
        json_object['parameters']['mesh'] = meshes

    # pre 1.0.11 the attribute was called fiber on a zLineOfAction.
    # As of 1.0.11 it is called fiber_item
    if class_type_name == 'zLineOfAction':
        json_object['fiber_item'] = json_object['fiber']
        json_object.pop('fiber', None)
    elif class_type_name == 'zRivetToBone':
        json_object['rivet_locator'] = []
        json_object['rivet_locator_parent'] = []
    elif class_type_name == 'zRestShape':
        json_object['tissue_item'] = json_object['tissue_name']
        json_object.pop('tissue_name', None)


def _get_node_types_with_maps():
    """ Searches through the modules for existing node type objects and 
    returns the ones that have maps associated with it.
    Useful for performing actions on node types with maps.
    MAP_LIST is a class attr so it is not being instantiated here.
    """
    map_class_type_list = []
    for _, obj in inspect.getmembers(sys.modules['zBuilder.nodes']):
        if inspect.isclass(obj) and hasattr(obj, 'MAP_LIST') and obj.MAP_LIST:
            map_class_type_list.append(obj.type)
    return map_class_type_list
