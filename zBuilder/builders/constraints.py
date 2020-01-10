from zBuilder.builder import Builder
import zBuilder.zMaya as mz

from maya import cmds
import logging

logger = logging.getLogger(__name__)


class Constraints(Builder):
    """To capture Maya constraints.  Supports point, orient and parent constraints.
    """

    def __init__(self):
        Builder.__init__(self)

        self.acquire = ['pointConstraint', 'orientConstraint', 'parentConstraint']

    @Builder.time_this
    def retrieve_from_scene(self, *args, **kwargs):
        # parse args------------------------------------------------------------
        selection = mz.parse_maya_node_for_selection(args)

        tmp = list()
        connections = list(set(cmds.listConnections(selection)))

        tmp.extend([x for x in connections if cmds.objectType(x) in self.acquire])

        for item in tmp:
            parameter = self.node_factory(item)
            self.bundle.extend_scene_items(parameter)
        self.stats()

    @Builder.time_this
    def build(self, *args, **kwargs):
        logger.info('Applying constraints....')
        attr_filter = kwargs.get('attr_filter', None)
        name_filter = kwargs.get('name_filter', list())

        for scene_item in self.get_scene_items(name_filter=name_filter, type_filter=self.acquire):
            scene_item.build(attr_filter=attr_filter)
