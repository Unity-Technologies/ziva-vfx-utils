from .builder import Builder
from zBuilder.mayaUtils import parse_maya_node_for_selection
from zBuilder.commonUtils import time_this
from maya import cmds
import logging

logger = logging.getLogger(__name__)


class DeltaMush(Builder):
    """To capture a deltaMush
    """

    @time_this
    def retrieve_from_scene(self, *args, **kwargs):
        # parse args------------------------------------------------------------
        selection = parse_maya_node_for_selection(args)
        hist = cmds.listHistory(selection)
        delta_mushes = cmds.ls(hist, type='deltaMush')[::-1]
        assert delta_mushes, "No delta mushes found, aborting!"

        for delta_mush in delta_mushes:
            parameter = self.node_factory(delta_mush)
            self.bundle.add_parameter(parameter)
        self.stats()

    @time_this
    def build(self, *args, **kwargs):
        logger.info('Applying deltaMush....')
        attr_filter = kwargs.get('attr_filter', None)
        interp_maps = kwargs.get('interp_maps', 'auto')
        name_filter = kwargs.get('name_filter', list())

        for scene_item in self.get_scene_items(name_filter=name_filter, type_filter='deltaMush'):
            scene_item.build(attr_filter=attr_filter, interp_maps=interp_maps)
