from zBuilder.nodes.base import BaseNode
import logging

logger = logging.getLogger(__name__)


class DeltaMushNode(BaseNode):
    def __init__(self, *args, **kwargs):
        BaseNode.__init__(self)
        self.create(args[0])

    def create(self,maya_node):
