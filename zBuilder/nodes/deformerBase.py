import maya.cmds as mc
import maya.mel as mm
import zBuilder.zMaya as mz

from zBuilder.nodes.base import BaseNode
import logging

logger = logging.getLogger(__name__)


class DeformerBaseNode(BaseNode):

    def __init__(self, *args, **kwargs):
        BaseNode.__init__(self, *args, **kwargs)

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
        super(DeformerBaseNode, self).populate(*args, **kwargs)

        selection = mz.parse_args_for_selection(args)

        self.association = self.get_meshes(selection[0])

        # get map component data------------------------------------------------
        mesh_names = self.association
        map_names = self.get_map_names()

        if map_names and mesh_names:
            for map_name, mesh_name in zip(map_names, mesh_names):
                map_data_object = self._setup.component_factory(map_name,
                                                                mesh_name,
                                                                type='map')
                self._setup.add_component(map_data_object)

                if not self._setup.get_component(type_filter='mesh',
                                                 name_filter=mesh_name):
                    mesh_data_object = self._setup.component_factory(mesh_name,
                                                                     type='mesh')
                    self._setup.add_component(mesh_data_object)

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
