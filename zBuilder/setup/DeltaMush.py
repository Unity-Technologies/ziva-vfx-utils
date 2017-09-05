import zBuilder.zMaya

import zBuilder.data as dta
import zBuilder.data.mesh as msh
import zBuilder.nodes as nds
from zBuilder.main import Builder
import zBuilder.zMaya as mz


import maya.cmds as mc

import logging

logger = logging.getLogger(__name__)

MAPLIST = {'deltaMush': ['weightList[0].weights']}


class DeltaMushSetup(Builder):
    """
    To capture a ziva setup
    """

    def __init__(self):
        Builder.__init__(self)

    @Builder.time_this
    def retrieve_from_scene(self, *args, **kwargs):
        # parse args------------------------------------------------------------
        selection = mz.parse_args_for_selection(args)

        # kwargs----------------------------------------------------------------
        get_mesh = kwargs.get('get_mesh', True)
        get_maps = kwargs.get('get_map_names', True)

        hist = mc.listHistory(selection)
        delta_mushes = mc.ls(hist, type='deltaMush')[::-1]

        if not delta_mushes:
            raise StandardError, 'No delta mushes found, aborting!'

        for delta_mush in delta_mushes:
            b_node = self.node_factory(delta_mush)
            self.add_node(b_node)
        self.stats()

    @Builder.time_this
    def apply(self, *args, **kwargs):
        logger.info('Applying deltaMush....')
        attr_filter = kwargs.get('attr_filter', None)
        interp_maps = kwargs.get('interp_maps', 'auto')
        name_filter = kwargs.get('name_filter', None)

        b_nodes = self.get_nodes(name_filter=name_filter,
                                 type_filter='deltaMush')
        for b_node in b_nodes:
            b_node.apply(attr_filter=attr_filter, interp_maps=interp_maps)


def get_association(delta_mush):
    hist = mc.listHistory(delta_mush)
    mesh = mc.ls(hist, type='mesh')
    parent = mc.listRelatives(mesh, p=True)[0]
    return [parent]

