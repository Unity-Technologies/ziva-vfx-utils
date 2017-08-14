from zBuilder.nodes import ZivaBaseNode

import logging

from zBuilder.zMaya import replace_long_name

logger = logging.getLogger(__name__)


class LineOfActionNode(ZivaBaseNode):
    def __init__(self):
        ZivaBaseNode.__init__(self)
        self._zFiber = None
        self._type = 'zLineOfAction'

    def set_fiber(self, fiber):
        self._zFiber = fiber

    def get_fiber(self, long_name=False):
        return self._zFiber

    def string_replace(self, search, replace):
        super(LineOfActionNode, self).string_replace(search, replace)

        # name replace----------------------------------------------------------
        name = self.get_fiber(long_name=True)
        if name:
            newName = replace_long_name(search, replace, name)
            self.set_fiber(newName)



