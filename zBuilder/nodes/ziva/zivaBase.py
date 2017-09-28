import zBuilder.zMaya as mz
import maya.cmds as mc

from zBuilder.nodes.base import BaseNode
import logging

logger = logging.getLogger(__name__)


class ZivaBaseNode(BaseNode):

    def __init__(self, *args, **kwargs):
        BaseNode.__init__(self, *args, **kwargs)

    def apply(self, *args, **kwargs):
        pass

    def populate(self, *args, **kwargs):
        """

        Returns:
            object:
        """

        # logger.info('retrieving {}'.format(args))
        selection = mz.parse_args_for_selection(args)

        self.name = selection[0]
        self.type = mz.get_type(selection[0])
        self.set_attr_list(mz.build_attr_list(selection[0]))
        self.populate_attrs(selection[0])
        self.set_mobject(selection[0])

        mesh = mz.get_association(selection[0])
        self.set_association(mesh)

        map_names = []
        for map_ in self.MAP_LIST:
            map_names.append('{}.{}'.format(selection[0], map_))
        self.set_map_names(map_names)

        # get map component data------------------------------------------------
        mesh_names = self.get_map_meshes()

        if map_names and mesh_names:
            for map_name, mesh_name in zip(map_names, mesh_names):
                map_data_object = self._setup.component_factory(map_name,
                                                                mesh_name,
                                                                type='map')
                self._setup.add_data_object(map_data_object)

                if not self._setup.get_data_by_key_name('mesh', mesh_name):
                    mesh_data_object = self._setup.component_factory(mesh_name,
                                                                     type='mesh'
                                                                    )
                    self._setup.add_data_object(mesh_data_object)
