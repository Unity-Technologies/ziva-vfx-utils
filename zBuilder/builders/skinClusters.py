import logging

from maya import cmds
from zBuilder.utils.commonUtils import time_this
from zBuilder.utils.mayaUtils import parse_maya_node_for_selection
from .builder import Builder

logger = logging.getLogger(__name__)


class SkinCluster(Builder):
    """ Capturing Maya skinClusters
    """

    @time_this
    def retrieve_from_scene(self, *args, **kwargs):
        selection = parse_maya_node_for_selection(args)
        history = cmds.listHistory(selection)
        skin_clusters = cmds.ls(history, type='skinCluster')[::-1]
        assert skin_clusters, 'No skinClusters found, aborting!'

        for skin_cluster in skin_clusters:
            scene_item = self.node_factory(skin_cluster)
            self._extend_scene_items(scene_item)

            for item in self.get_scene_items(type_filter=['mesh']):
                item.retrieve_values()
        self.stats()

    @time_this
    def build(self, *args, **kwargs):
        logger.info('Applying skinCluster....')
        interp_maps = kwargs.get('interp_maps', 'auto')

        scene_items = self.get_scene_items(type_filter='skinCluster')
        for scene_item in scene_items:
            scene_item.do_build(interp_maps=interp_maps)
