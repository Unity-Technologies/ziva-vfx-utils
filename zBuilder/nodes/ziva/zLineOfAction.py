from zBuilder.nodes import ZivaBaseNode

import logging

from zBuilder.zMaya import replace_long_name

logger = logging.getLogger(__name__)


class LineOfActionNode(ZivaBaseNode):
    TYPE = 'zLineOfAction'

    def __init__(self, *args, **kwargs):
        ZivaBaseNode.__init__(self, *args, **kwargs)
        self._zFiber = None

    def set_fiber(self, fiber):
        self._zFiber = fiber

    def get_fiber(self, long_name=False):
        return self._zFiber

