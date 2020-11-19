from collections import defaultdict
import zBuilder.builder
# def update_builder_pre_1_0_11(builder):
#     """This updates any zBuilder file saved before 1.0.11.  It adds a reference for the
#     parameters and changes an attribute name.  This change happened during 1.9 of Ziva VFX.

#     Args:
#         builder (obj): Builder object in need of an update.
#     """

#     for item in builder.get_scene_items(type_filter=['zMaterial', 'zTet', 'zFiber', 'zAttachment']):
#         item.parameters = defaultdict(list)

#         # add the mesh object to parameters
#         for mesh_name in item.get_map_meshes():
#             mesh_name = mesh_name.split('|')[-1]

#             mesh = builder.get_scene_items(name_filter=mesh_name)[0]
#             item.add_parameter(mesh)

#         # add the map objects, first we need to construct the map names for the node
#         for map_ in item.construct_map_names():
#             item.add_parameter(builder.get_scene_items(name_filter=map_)[0])

#     # pre 1.0.11 the attribute was called fiber on a zLineOfAction.
#     # As of 1.0.11 it is called fiber_item
#     for item in builder.get_scene_items(type_filter=['zLineOfAction']):
#         setattr(item, 'fiber_item', getattr(item, 'fiber'))
#         delattr(item, 'fiber')

#     for item in builder.get_scene_items(type_filter=['zRivetToBone']):
#         item.rivet_locator = []
#         item.rivet_locator_parent = []


def update_json_pre_1_0_11(json_object):
    type_ = json_object.get('type', 'Base')
    builder_type = json_object['_builder_type']
    obj = zBuilder.builder.find_class(builder_type, type_)
    if type_ in ['zMaterial', 'zTet', 'zFiber', 'zAttachment']:
        json_object['parameters'] = defaultdict(list)
        map_names = construct_map_names(json_object['_name'], obj.MAP_LIST)
        json_object['parameters']['map'].extend(map_names)

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
