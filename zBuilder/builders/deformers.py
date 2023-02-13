import logging

from maya import cmds

from zBuilder.utils.commonUtils import time_this
from zBuilder.utils.mayaUtils import parse_maya_node_for_selection, get_type
from .builder import Builder

logger = logging.getLogger(__name__)


class Deformers(Builder):
    """Test setup to play with deformers and how they are ordered on a mesh.
    """

    def __init__(self, *args, **kwargs):
        super(Deformers, self).__init__(*args, **kwargs)

        self.acquire = ['deltaMush', 'blendShape', 'wrap']

    @time_this
    def retrieve_from_scene(self, *args, **kwargs):
        # parse args-----------------------------------------------------------
        selection = parse_maya_node_for_selection(args)

        tmp = list()
        # we are traversing through the history breadth first because we need to make sure we are
        # adding these to zBuilder in the proper order.  zBuilder is first in first out.
        for hist in cmds.listHistory(selection, breadthFirst=True, allFuture=True):
            if get_type(hist) in self.acquire:
                tmp.append(hist)

        for item in tmp:

            parameter = self.node_factory(item)

            self.bundle.extend_scene_items(parameter)
            for parm in parameter:
                if parm.type in ['mesh', 'map']:
                    parm.retrieve_values()
        self.stats()

    @time_this
    def build(self, *args, **kwargs):
        logger.info('Applying....')
        attr_filter = kwargs.get('attr_filter', None)
        interp_maps = kwargs.get('interp_maps', 'auto')
        name_filter = kwargs.get('name_filter', list())

        for scene_item in self.get_scene_items(name_filter=name_filter, type_filter=self.acquire):
            scene_item.build(attr_filter=attr_filter, interp_maps=interp_maps)