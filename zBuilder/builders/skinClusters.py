from zBuilder.builder import Builder
import zBuilder.zMaya as mz

import maya.cmds as mc

import logging

logger = logging.getLogger(__name__)


class SkinCluster(Builder):
    """Capturing Maya skinClusters
    """

    def __init__(self):
        Builder.__init__(self)

    @Builder.time_this
    def retrieve_from_scene(self, *args, **kwargs):
        # parse args------------------------------------------------------------
        selection = mz.parse_maya_node_for_selection(args)

        hist = mc.listHistory(selection)
        skinClusters = mc.ls(hist, type='skinCluster')[::-1]

        if not skinClusters:
            raise StandardError('No skinClusters found, aborting!')

        for skinCluster in skinClusters:
            scene_item = self.node_factory(skinCluster)
            self.bundle.extend_scene_items(scene_item)
        self.stats()

    @Builder.time_this
    def build(self, *args, **kwargs):
        logger.info('Applying skinCluster....')
        attr_filter = kwargs.get('attr_filter', None)
        interp_maps = kwargs.get('interp_maps', 'auto')
        name_filter = kwargs.get('name_filter', list())

        parameters = self.get_scene_items(name_filter=name_filter, type_filter='skinCluster')
        for parameter in parameters:
            parameter.mobject = None
            parameter.build(attr_filter=attr_filter, interp_maps=interp_maps)
