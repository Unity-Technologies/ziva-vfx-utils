import logging

from collections import defaultdict
from maya import cmds
from zBuilder.utils.mayaUtils import construct_map_names
from .dg_node import DGNode

logger = logging.getLogger(__name__)


class Deformer(DGNode):

    def __init__(self, parent=None, builder=None):
        super(Deformer, self).__init__(parent=parent, builder=builder)
        self.parameters = defaultdict(list)

    def add_parameter(self, parameter):
        """ This takes a zBuilder parameter and adds it to the node.
        This is effectively a pointer to original parameter for later retrieval.

        Args:
            parameter: obj the parameter to add to node
        """
        self.parameters[parameter.type].append(parameter)

    def spawn_parameters(self):
        """
        This outputs a dictionary formatted to feed to the parameter factory so
        the parameter factory knows what parameters to build.  The third value in maps 
        is either 'endPoints' or 'barycentric'.  endPoints is an interpolation method 
        exclusive for endPoint fiber maps.
        dict['map'] = [node_name_dot_attr, mesh_name, 'barycentric']
        dict['mesh'] = [mesh_name]
        """
        objs = {}
        if self.nice_association:
            objs['mesh'] = self.nice_association

        mesh_names = self.get_map_meshes()
        map_names = construct_map_names(self.name, self.MAP_LIST)
        if map_names and mesh_names:
            objs['map'] = []
            for map_name, mesh_name in zip(map_names, mesh_names):
                objs['map'].append([map_name, mesh_name, "barycentric"])
        return objs

    def populate(self, maya_node=None):
        """ Populates the node with the info from the passed maya node in args.

        This is deals with basic stuff including attributes.
        For other things it is meant to be overridden in inherited node.
        This is inherited from Base and extended to deal with maps and meshes.

        Args:
            maya_node (str): The maya node to populate parameter with.
        """
        super(Deformer, self).populate(maya_node=maya_node)
        meshes = cmds.deformer(maya_node, query=True, g=True)
        self.association = cmds.listRelatives(meshes, p=True, fullPath=True)

    def get_map_meshes(self):
        """ This is the mesh associated with each map in obj.map_list.
        Typically it seems to coincide with mesh store in get_association.
        Sometimes it deviates, so you can override this method 
        to define your own list of meshes against the map list.

        Returns:
            list: List of long mesh names.
        """
        return self.nice_association

    def set_maya_weights(self, interp_maps=False):
        """ This loops through and internal map on a node stored in 
        self.parameters['map'] then applies weight.

        Args:
            interp_maps (str): Do you want maps interpolated?
                True forces interpolation.
                False cancels it.
                auto checks if it needs to.  Default = "auto"
        """
        self.check_map_interpolation(interp_maps)
        for map_ in self.parameters['map']:
            if cmds.objExists(self.name):
                map_.apply_weights()
            else:
                logger.warning('Missing {} from scene. Not applying map.'.format(self.name))

    def check_map_interpolation(self, interp_maps):
        """ For each map it checks if it is topologically corresponding and if
        it isn't it will interpolate the map if the flag is True.  Once the map
        has been interpolated it updates the stored value before it gets applied
        in Maya.

        Args:
            interp_maps (bool): Do you want to do it?
        """
        map_objects = self.parameters['map']
        if interp_maps == 'auto':
            for map_object in map_objects:
                if not map_object.is_topologically_corresponding():
                    interp_maps = True

        if interp_maps in [True, 'True', 'true']:
            for map_object in map_objects:
                map_object.interpolate()
