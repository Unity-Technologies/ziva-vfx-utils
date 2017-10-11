from zBuilder.builder import Builder
import zBuilder.zMaya as mz

import maya.cmds as mc

import logging

logger = logging.getLogger(__name__)


class TestSetup(Builder):
    """
    Test setup to play with deformers and how they are ordered on a mesh.
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

        acquire = ['deltaMush', 'zRelaxer', 'zWrap', 'zItto', 'zPolyCombine',
                   'blendShape', 'wrap']
        tmp = list()
        history = mc.listHistory(selection, f=True)
        history.extend(mc.listHistory(selection))
        history = list(set(history))[::-1]

        for hist in history:
            if mc.objectType(hist) in acquire:
                tmp.append(hist)

        for item in tmp:
            b_node = self.node_factory(item)
            self.add_node(b_node)
        self.stats()

    @Builder.time_this
    def build(self, *args, **kwargs):
        logger.info('Applying....')
        attr_filter = kwargs.get('attr_filter', None)
        interp_maps = kwargs.get('interp_maps', 'auto')
        name_filter = kwargs.get('name_filter', None)

        b_nodes = self.get_nodes(name_filter=name_filter)
        for b_node in b_nodes:
            b_node.build(attr_filter=attr_filter, interp_maps=interp_maps)
