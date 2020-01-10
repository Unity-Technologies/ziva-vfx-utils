from zBuilder.builder import Builder
import zBuilder.zMaya as mz

from maya import cmds

import logging

logger = logging.getLogger(__name__)


class SkinCluster(Builder):
    """Capturing Maya skinClusters
    """
    @Builder.time_this
    def retrieve_from_scene(self, *args, **kwargs):
        # parse args------------------------------------------------------------
        selection = mz.parse_maya_node_for_selection(args)

        history = cmds.listHistory(selection)
        skin_clusters = cmds.ls(history, type='skinCluster')[::-1]

        if not skin_clusters:
            raise Exception('No skinClusters found, aborting!')

        for skin_cluster in skin_clusters:
            scene_item = self.node_factory(skin_cluster)
            self.bundle.extend_scene_items(scene_item)
        self.stats()

    @Builder.time_this
    def build(self, *args, **kwargs):
        logger.info('Applying skinCluster....')
        attr_filter = kwargs.get('attr_filter', None)
        interp_maps = kwargs.get('interp_maps', 'auto')
        name_filter = kwargs.get('name_filter', list())

        scene_items = self.get_scene_items(name_filter=name_filter, type_filter='skinCluster')
        for scene_item in scene_items:
            scene_item.build(attr_filter=attr_filter, interp_maps=interp_maps)
