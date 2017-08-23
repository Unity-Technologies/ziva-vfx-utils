import zBuilder.zMaya
from zBuilder.nodes.base import BaseNode
from zBuilder.main import Builder

import zBuilder.data.mesh as msh
import zBuilder.data.maps as mps

import zBuilder.zMaya as mz
import zBuilder.nodes.base as base

import maya.cmds as mc

import logging

logger = logging.getLogger(__name__)

MAPLIST = {'deltaMush': ['weightList[0].weights']}


class DeltaMushSetup(Builder):
    """
    Storing maya attributes
    """

    def __init__(self):
        Builder.__init__(self)

    @Builder.time_this
    def retrieve_from_scene(self, *args, **kwargs):
        # parse args------------------------------------------------------------
        selection = mz.parse_args_for_selection(args)

        # kwargs----------------------------------------------------------------
        get_mesh = kwargs.get('get_mesh', True)
        get_maps = kwargs.get('get_maps', True)

        hist = mc.listHistory(selection)
        delta_mushes = mc.ls(hist, type='deltaMush')[::-1]

        if not delta_mushes:
            raise StandardError, 'No delta mushes found, aborting!'

        for delta_mush in delta_mushes:

            node_attr_list = base.build_attr_list(delta_mush)
            node_attrs = zBuilder.zMaya.build_attr_key_values(delta_mush, node_attr_list)

            node = BaseNode()
            node.set_name(delta_mush)
            node.set_type('deltaMush')
            node.set_attrs(node_attrs)
            node.set_association(get_association(delta_mush))

            if get_maps:
                maps = []
                map_name = '{}.weightList[0].weights'.format(delta_mush)
                association = get_association(delta_mush)
                map_data = mps.get_map_data(delta_mush, 'weightList[0].weights',
                                            association[0])
                maps.append(map_name)
                node.set_maps(maps)
                self.add_data_object('map', map_name, data=map_data)

                if get_mesh:
                    for ass in association:
                        if not self.get_data_by_key_name('mesh', ass):
                            self.add_data_object('mesh', ass,
                                                 data=msh.get_mesh_data(ass))

            self.add_node(node)
        self.stats()

    @Builder.time_this
    def apply(self, *args, **kwargs):
        logger.info('Applying deltaMush....')
        attr_filter = kwargs.get('attr_filter', None)
        interp_maps = kwargs.get('interp_maps', 'auto')

        # get all the nodes
        b_nodes = self.get_nodes()

        for b_node in b_nodes:
            name = b_node.get_name()
            if not mc.objExists(name):
                mc.select(b_node.get_association(), r=True)
                mc.deltaMush(name=name)

            self.set_maya_attrs_for_builder_node(b_node, attr_filter=attr_filter)
            self.set_maya_weights_for_builder_node(b_node, interp_maps=interp_maps)


def get_association(delta_mush):
    hist = mc.listHistory(delta_mush)
    mesh = mc.ls(hist, type='mesh')
    parent = mc.listRelatives(mesh, p=True)[0]
    return [parent]

