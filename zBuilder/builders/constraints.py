from zBuilder.builder import Builder
import zBuilder.zMaya as mz

import maya.cmds as mc
import logging

logger = logging.getLogger(__name__)


class Constraints(Builder):
    def __init__(self):
        Builder.__init__(self)

        self.acquire = ['pointConstraint',
                        'orientConstraint',
                        'parentConstraint']

    @Builder.time_this
    def retrieve_from_scene(self, *args, **kwargs):
        # parse args------------------------------------------------------------
        selection = mz.parse_maya_node_for_selection(args)
        
        tmp = list()
        connections = list(set(mc.listConnections(selection)))

        tmp.extend([x for x in connections if mc.objectType(x) in self.acquire])

        for item in tmp:
            parameter = self.parameter_factory(item)
            self.add_parameter(parameter)
        self.stats()

    @Builder.time_this
    def build(self, *args, **kwargs):
        logger.info('Applying constraints....')
        attr_filter = kwargs.get('attr_filter', None)
        name_filter = kwargs.get('name_filter', list())

        parameters = self.get_parameters(name_filter=name_filter,
                                      type_filter=self.acquire)
        for parameter in parameters:
            parameter.build(attr_filter=attr_filter)