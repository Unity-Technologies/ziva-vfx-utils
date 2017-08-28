import maya.cmds as mc
import maya.mel as mm
import zBuilder.zMaya as mz

from zBuilder.nodes.base import BaseNode
import logging

logger = logging.getLogger(__name__)


# TODO zivabase????  change name???
class ZivaBaseNode(BaseNode):

    def __init__(self, *args, **kwargs):
        BaseNode.__init__(self, *args, **kwargs)

    def populate(self, *args, **kwargs):
        """

        Returns:
            object:
        """

        # logger.info('retrieving {}'.format(args))
        selection = mz.parse_args_for_selection(args)

        self.set_name(selection[0])
        self.set_type(mz.get_type(selection[0]))
        self.set_attr_list(mz.build_attr_list(selection[0]))
        self.populate_attrs(selection[0])
        self.set_mobject(selection[0])

        mesh = mz.get_association(selection[0])
        self.set_association(mesh)

        map_names = []
        for map_ in self.MAP_LIST:
            map_names.append('{}.{}'.format(selection[0], map_))
        self.set_maps(map_names)

        # get map component data------------------------------------------------
        mesh_names = self.get_association(long_name=True)
        if map_names and mesh_names:
            for map_name, mesh_name in zip(map_names, mesh_names):
                map_data_object = self._parent.component_factory('map',
                                                    map_name, mesh_name)
                self._parent.add_data_object(map_data_object)

                if not self._parent.get_data_by_key_name('mesh', mesh_name):
                    mesh_data_object = self._parent.component_factory('mesh',
                                                                      mesh_name)
                    self._parent.add_data_object(mesh_data_object)