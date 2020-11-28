from collections import defaultdict
import zBuilder.builder

from zBuilder.nodes.deformer import construct_map_names
from zBuilder.builder import get_node_types_with_maps
import zBuilder.mayaUtils as mu


def update_json_pre_1_0_11(json_object):
    type_ = json_object.get('type', 'Base')
    builder_type = json_object['_builder_type']
    obj = zBuilder.builder.find_class(builder_type, type_)

    if type_ in get_node_types_with_maps():
        json_object['parameters'] = defaultdict(list)
        map_names = construct_map_names(json_object['_name'], obj.MAP_LIST)
        json_object['parameters']['map'].extend(map_names)

        # the association holds the mesh name associated with node.  Currently the only
        # use for meshes in zBuilder is for interpolating weight maps if needed.
        # this means that a mesh is only stored for a node if it has a map.

        # first we need to use short name for mesh
        meshes = [mu.get_short_name(x) for x in json_object['_association']]
        json_object['parameters']['mesh'] = meshes

    # pre 1.0.11 the attribute was called fiber on a zLineOfAction.
    # As of 1.0.11 it is called fiber_item
    if type_ == 'zLineOfAction':
        json_object['fiber_item'] = json_object['fiber']
        json_object.pop('fiber', None)
    if type_ == 'zRivetToBone':
        json_object['rivet_locator'] = []
        json_object['rivet_locator_parent'] = []
    if type_ == 'zRestShape':
        json_object['tissue_item'] = json_object['tissue_name']
        json_object.pop('tissue_name', None)
