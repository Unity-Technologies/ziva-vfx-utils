from collections import defaultdict

from maya import cmds
from maya import mel
import zBuilder.zMaya as mz

from zBuilder.nodes.dg_node import DGNode
import logging

logger = logging.getLogger(__name__)


class Deformer(DGNode):
    def __init__(self, parent=None, builder=None):
        super(Deformer, self).__init__(parent=parent, builder=builder)

        self.parameters = defaultdict(list)

    def add_parameter(self, parameter):
        """ This takes a zBuilder parameter and adds it to the node.  This is effectively
        a pointer to original parameter for later retrieval

        args: 
            parameter: obj the parameter to add to node
        """
        self.parameters[parameter.type].append(parameter)

    def spawn_parameters(self):
        """

        Returns:

        """
        objs = {}
        if self.long_association:
            objs['mesh'] = self.long_association

        mesh_names = self.get_map_meshes()
        map_names = self.get_map_names()
        if map_names and mesh_names:
            objs['map'] = []
            for map_name, mesh_name in zip(map_names, mesh_names):
                objs['map'].append([map_name, mesh_name])
        return objs

    def build(self, *args, **kwargs):
        """ Builds the node in maya.  mean to be overwritten.
        """
        raise NotImplementedError

    def populate(self, maya_node=None):
        """ Populates the node with the info from the passed maya node in args.

        This is deals with basic stuff including attributes.  For other things it
        is meant to be overridden in inherited node.

        This is inherited from Base and extended to deal with maps and meshes.
        Args:
            maya_node (str): The maya node to populate parameter with.

        """

        super(Deformer, self).populate(maya_node=maya_node)

        self.association = self.get_meshes(maya_node)

    def get_map_meshes(self):
        """ This is the mesh associated with each map in obj.MAP_LIST.  Typically
        it seems to coincide with mesh store in get_association.  Sometimes
        it deviates, so you can override this method to define your own
        list of meshes against the map list.

        Returns:
            list: List of long mesh names.
        """
        return self.long_association

    def get_mesh_objects(self):
        """

        Returns:

        """
        meshes = list()
        for mesh_name in self.get_map_meshes():
            meshes.extend(self.builder.get_scene_items(type_filter='mesh', name_filter=mesh_name))
        return meshes

    def get_map_objects(self):
        """

        Returns:

        """
        maps_ = list()
        for map_name in self.get_map_names():
            maps_.extend(
                self.builder.bundle.get_scene_items(type_filter='map', name_filter=map_name))
        return maps_

    def get_map_names(self):
        """ This builds the map names.  maps from MAP_LIST with the object name
        in front

        For this we want to get the .name and not scene name.
        """
        map_names = []
        for map_ in self.MAP_LIST:
            map_names.extend(cmds.ls('{}.{}'.format(self.name, map_)))

        return map_names

    @staticmethod
    def get_meshes(node):
        """ Queries the deformer and returns the meshes associated with it.

        Args:
            node: Maya node to query.

        Returns:
            list od strings: list of strings of mesh names.
        """
        meshes = cmds.deformer(node, query=True, g=True)
        tmp = list()
        for mesh in meshes:
            parent = cmds.listRelatives(mesh, p=True)
            tmp.extend(cmds.ls(parent, long=True))
        return tmp

    def set_maya_weights(self, interp_maps=False):
        """ Given a Builder node this set the map values of the object in the maya
        scene.

        Args:
            interp_maps (str): Do you want maps interpolated?
                True forces interpolation.
                False cancels it.
                auto checks if it needs to.  Default = "auto"

        Returns:
            nothing.
        """
        maps = self.get_map_names()
        scene_name = self.get_scene_name()
        original_name = self.name

        self.check_map_interpolation(interp_maps)
        for map_ in maps:
            map_data = self.builder.bundle.get_scene_items(type_filter='map', name_filter=map_)
            if map_data:
                map_data[0].string_replace(original_name, scene_name)
                map_data[0].apply_weights()

    def check_map_interpolation(self, interp_maps):
        """ For each map it checks if it is topologically corresponding and if
        it isn't it will interpolate the map if the flag is True.  Once the map
        has been interpolated it updates the stored value before it gets applied
        in Maya.

        Args:
            interp_maps (bool): Do you want to do it?
        """

        map_objects = self.get_map_objects()
        if interp_maps == 'auto':
            for map_object in map_objects:
                if not map_object.is_topologically_corresponding():
                    interp_maps = True

        if interp_maps in [True, 'True', 'true']:
            for map_object in map_objects:
                map_object.interpolate()
