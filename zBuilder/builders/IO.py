import inspect
import json
import logging
import sys

from collections import defaultdict
from zBuilder.utils.commonUtils import parse_version_info
from zBuilder.utils.mayaUtils import get_short_name, construct_map_names
from .builder import find_class

logger = logging.getLogger(__name__)


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


def _update_json_pre_1_0_11(json_object):
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


class BaseNodeEncoder(json.JSONEncoder):

    def default(self, obj):
        if hasattr(obj, '_class'):
            if hasattr(obj, 'serialize'):
                return obj.serialize()
            return obj.__dict__

        return super(BaseNodeEncoder, self).default(obj)


def pack_zbuilder_contents(builder, type_filter, invert_match):
    """ Utility to package the data in a dictionary.
    """
    logger.info("packing zBuilder contents for json.")

    node_data = dict()
    node_data['d_type'] = 'node_data'
    node_data['data'] = builder.get_scene_items(type_filter=type_filter, invert_match=invert_match)

    info = dict()
    info['d_type'] = 'info'
    info['data'] = builder.info

    return [node_data, info]


def unpack_zbuilder_contents(builder, json_data):
    """ Gets data out of json serialization and assigns it to node collection
    object.

    Args:
        json_data: Data to assign to builder object.
    """
    for d in json_data:
        if d['d_type'] == 'node_data':
            builder.bundle.extend_scene_items(d['data'])
            logger.info("Reading scene items. {} nodes".format(len(d['data'])))

        if d['d_type'] == 'info':
            builder.info = d['data']
            logger.info("Reading info.")

    logger.info("Assigning builder.")
    for item in builder.bundle:
        if item:
            item.builder = builder


def load_base_node(json_object):
    """
    Loads json objects into proper classes.  Serves as object hook for loading
    json.

    Args:
        json_object (obj): json obj to perform action on

    Returns:
        obj:  Result of operation
    """
    if '_class' in json_object:
        major, minor, patch, _ = parse_version_info(json_object['info']['version'])
        # For pre zBuilder 1.0.11 file format, we need to parameter reference to each node
        if (major, minor, patch) < (1, 0, 11):
            _update_json_pre_1_0_11(json_object)

        obj = find_class(json_object['_builder_type'], json_object.get('type', 'Base'))
        try:
            scene_item = obj()
            scene_item.deserialize(json_object)
            return scene_item
        except TypeError:
            # Catches the scene items for ui that slip in.
            return json_object

    return json_object
