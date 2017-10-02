import maya.cmds as mc
import maya.mel as mm
import zBuilder.zMaya as mz

from zBuilder.nodes.base import BaseNode
import logging

logger = logging.getLogger(__name__)


class DeformerBaseNode(BaseNode):

    def __init__(self, *args, **kwargs):
        BaseNode.__init__(self, *args, **kwargs)

    def apply(self, *args, **kwargs):
        raise NotImplementedError

    def populate(self, *args, **kwargs):
        super(DeformerBaseNode, self).populate(*args, **kwargs)
        """

        Returns:
            object:
        """
        # logger.info('retrieving {}'.format(args))
        selection = mz.parse_args_for_selection(args)

        self.association = self.get_meshes(selection[0])

        # get map component data------------------------------------------------
        mesh_names = self.long_association
        map_names = self.get_map_names()

        if map_names and mesh_names:
            for map_name, mesh_name in zip(map_names, mesh_names):
                map_data_object = self._setup.component_factory(map_name,
                                                                mesh_name,
                                                                type='map')
                self._setup.add_data(map_data_object)

                if not self._setup.get_data(type_filter='mesh',
                                            name_filter=mesh_name):
                    mesh_data_object = self._setup.component_factory(mesh_name,
                                                                     type='mesh')
                    self._setup.add_data(mesh_data_object)

    @staticmethod
    def get_meshes(node):
        meshes = mc.deformer(node, query=True, g=True)
        tmp = list()
        for mesh in meshes:
            parent = mc.listRelatives(mesh, p=True)
            tmp.extend(mc.ls(parent, long=True))
        return tmp
