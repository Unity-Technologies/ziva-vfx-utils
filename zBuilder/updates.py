from collections import defaultdict
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
    obj = find_class(builder_type, type_)
    if type_ in ['zMaterial', 'zTet', 'zFiber', 'zAttachment']:
        json_object['parameters'] = defaultdict(list)
        map_names = construct_map_names(json_object['_name'], obj.MAP_LIST)
        json_object['parameters']['map'].extend(map_names)


def construct_map_names(name, map_list):
    """ This builds the map names.  maps from MAP_LIST with the object name
    in front

    For this we want to get the .name and not scene name.
    """
    map_names = []
    for map_ in map_list:
        map_names.append('{}.{}'.format(name, map_))

    return map_names


def update_builder_pre_1_0_11(builder):
    """This updates any zBuilder file saved before 1.0.11.  It adds a reference for the 
    parameters and changes an attribute name.  This change happened during 1.9 of Ziva VFX.

    Args:
        builder (obj): Builder object in need of an update.
    """

    for item in builder.get_scene_items(type_filter=['zMaterial', 'zTet', 'zFiber', 'zAttachment']):

        # add the mesh object to parameters
        for mesh_name in item.get_map_meshes():
            mesh_name = mesh_name.split('|')[-1]

            mesh = builder.get_scene_items(name_filter=mesh_name)[0]
            item.add_parameter(mesh)

        # add the map objects, first we need to construct the map names for the node

        # for map_ in item.construct_map_names():

        #     maps = builder.get_scene_items(name_filter=map_)[0]
        #     # print 'adding ', maps
        #     item.add_parameter(maps)
        #     # print 'parm ', item.parameters

        #     # if item.type == 'zAttachment':
        #     #     print 'ID : ', id(item.parameters)
        #     #     print 'check map name scene item: ', maps.name
        #     #     print 'map_name from construct: ', map_
        #     #     print 'IN LOOP keys', item.parameters.keys()

    # for item in builder.get_scene_items(type_filter='zAttachment'):
    #     print 'AFTER LOOP ID: ', id(item.parameters)

    # pre 1.0.11 the attribute was called fiber on a zLineOfAction.
    # As of 1.0.11 it is called fiber_item
    for item in builder.get_scene_items(type_filter=['zLineOfAction']):
        setattr(item, 'fiber_item', getattr(item, 'fiber'))
        delattr(item, 'fiber')

    for item in builder.get_scene_items(type_filter=['zRivetToBone']):
        item.rivet_locator = []
        item.rivet_locator_parent = []

    for item in builder.get_scene_items(type_filter=['zRestShape']):
        setattr(item, 'tissue_item', getattr(item, 'tissue_name'))
        delattr(item, 'tissue_name')
