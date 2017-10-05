from zBuilder.builder import Builder
import zBuilder.zMaya as mz

import maya.cmds as mc


class ConstraintsSetup(Builder):
    def __init__(self):
        super(ConstraintsSetup, self).__init__()

    @Builder.time_this
    def retrieve_from_scene(self, *args, **kwargs):
        # parse args------------------------------------------------------------
        selection = mz.parse_args_for_selection(args)

        acquire = ['pointConstraint', 'orientConstraint']
        tmp = list()
        connections = list(set(mc.listConnections(selection)))

        tmp.extend([x for x in connections if mc.objectType(x) in acquire])

        for item in tmp:
            b_node = self.node_factory(item)
            self.add_node(b_node)
        self.stats()

    def apply(self):
        pass