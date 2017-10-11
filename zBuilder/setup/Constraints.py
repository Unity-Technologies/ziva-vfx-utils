from zBuilder.builder import Builder
import zBuilder.zMaya as mz

import maya.cmds as mc
import logging

logger = logging.getLogger(__name__)

class ConstraintsSetup(Builder):
    def __init__(self):
        super(ConstraintsSetup, self).__init__()

        self.acquire = ['pointConstraint',
                        'orientConstraint',
                        'parentConstraint']

    @Builder.time_this
    def retrieve_from_scene(self, *args, **kwargs):
        # parse args------------------------------------------------------------
        selection = mz.parse_args_for_selection(args)


        tmp = list()
        connections = list(set(mc.listConnections(selection)))

        tmp.extend([x for x in connections if mc.objectType(x) in self.acquire])

        for item in tmp:
            b_node = self.node_factory(item)
            self.add_node(b_node)
        self.stats()

    @Builder.time_this
    def build(self, *args, **kwargs):
        logger.info('Applying constraints....')
        attr_filter = kwargs.get('attr_filter', None)
        name_filter = kwargs.get('name_filter', list())

        b_nodes = self.get_nodes(name_filter=name_filter,
                                 type_filter=self.acquire)
        for b_node in b_nodes:
            b_node.build(attr_filter=attr_filter)