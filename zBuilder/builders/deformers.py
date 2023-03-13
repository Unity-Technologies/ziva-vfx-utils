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

        # I have tried many variation of listHistory command and the way I found works is to
        # get the list with default arguments and reverse it.  Setting future to true will
        # return list in proper order but will end up analysing almost everything and hang maya
        # on large scenes.  Slicing the output of the listHistory seems to be fastest way.
        for hist in cmds.listHistory(selection)[::-1]:
            if get_type(hist) in self.acquire:
                parameter = self.node_factory(hist)

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