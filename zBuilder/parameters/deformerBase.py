import maya.cmds as mc
import maya.mel as mm
import zBuilder.zMaya as mz

from zBuilder.parameters.base import BaseParameter
import logging

logger = logging.getLogger(__name__)


class DeformerBaseParameter(BaseParameter):

    def __init__(self, *args, **kwargs):
        BaseParameter.__init__(self, *args, **kwargs)

    def test(self):
        objs = {}

        mesh_names = self.get_map_meshes()
        map_names = self.get_map_names()
        if map_names and mesh_names:
            objs['map'] = []
            objs['mesh'] = []
            for map_name, mesh_name in zip(map_names, mesh_names):
                objs['map'].append([map_name, mesh_name])
                objs['mesh'].append(mesh_name)

        return objs

    def build(self, *args, **kwargs):
        """ Builds the node in maya.  mean to be overwritten.
        """
        raise NotImplementedError

    def populate(self, *args, **kwargs):
        """ Populates the node with the info from the passed maya node in args.

        This is deals with basic stuff including attributes.  For other things it
        is meant to be overridden in inherited node.

        This is inherited from Base and extended to deal with maps and meshes.
        Args:
            *args (str): The maya node to populate it with.

        """
        super(DeformerBaseParameter, self).populate(*args, **kwargs)

        selection = mz.parse_args_for_selection(args)

        self.association = self.get_meshes(selection[0])

        # # get map component data------------------------------------------------
        # mesh_names = self.association
        # map_names = self.get_map_names()
        #
        # if map_names and mesh_names:
        #     for map_name, mesh_name in zip(map_names, mesh_names):
        #         map_data_object = self._setup.component_factory(map_name,
        #                                                         mesh_name,
        #                                                         type='map')
        #         self._setup.add_component(map_data_object)
        #
        #         if not self._setup.get_components(type_filter='mesh',
        #                                          name_filter=mesh_name):
        #             mesh_data_object = self._setup.component_factory(mesh_name,
        #                                                              type='mesh')
        #             self._setup.add_component(mesh_data_object)

    # TODO instead of get_map* and get_mesh* should be more generic.
    # get_component*(type_filter)
    def get_map_meshes(self):
        """
        This is the mesh associated with each map in obj.MAP_LIST.  Typically
        it seems to coincide with mesh store in get_association.  Sometimes
        it deviates, so you can override this method to define your own
        list of meshes against the map list.

        Returns:
            list: List of long mesh names.
        """
        return self.association

    def get_mesh_objects(self):
        """

        Returns:

        """
        meshes = list()
        for mesh_name in self.get_map_meshes():
            meshes.extend(self._setup.get_parameters(type_filter='mesh',
                                                     name_filter=mesh_name))
        return meshes

    def get_map_objects(self):
        """

        Returns:

        """
        maps_ = list()
        for map_name in self.get_map_names():
            maps_.extend(self._setup.bundle.get_parameters(type_filter='map',
                                                           name_filter=map_name))
        return maps_

    def get_map_names(self):
        """
        This builds the map names.  maps from MAP_LIST with the object name
        in front

        """
        map_names = []
        for map_ in self.MAP_LIST:
            map_names.append('{}.{}'.format(self.get_scene_name(), map_))

        return map_names

    @staticmethod
    def get_meshes(node):
        """ Queries the deformer and returns the meshes associated with it.

        Args:
            node: Maya node to query.

        Returns:
            list od strings: list of strings of mesh names.
        """
        meshes = mc.deformer(node, query=True, g=True)
        tmp = list()
        for mesh in meshes:
            parent = mc.listRelatives(mesh, p=True)
            tmp.extend(mc.ls(parent, long=True))
        return tmp

    def set_maya_weights(self, interp_maps=False):
        """
        Given a Builder node this set the map values of the object in the maya
        scene.  It first does a mObject check to see if it has been tracked, if
        it has it uses that instead of stored scene_name.

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

        for map_ in maps:
            map_data = self._setup.bundle.get_parameters(type_filter='map',
                                                         name_filter=map_)[0]
            self.interpolate_maps(interp_maps)
            weight_list = map_data.values

            map_ = map_.replace(original_name, scene_name)

            if mc.objExists('%s[0]' % map_):
                if not mc.getAttr('%s[0]' % map_, l=True):
                    tmp = []
                    for w in weight_list:
                        tmp.append(str(w))
                    val = ' '.join(tmp)
                    cmd = "setAttr " + '%s[0:%d] ' % (
                        map_, len(weight_list) - 1) + val
                    mm.eval(cmd)

            else:
                try:
                    mc.setAttr(map_, weight_list, type='doubleArray')
                except:
                    pass

    # TODO this level????  pass a false?  seriously??
    def interpolate_maps(self, interp_maps):
        """ Interpolates maps in node.

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