import zBuilder.nodes.base as base

import re
import logging

logger = logging.getLogger(__name__)

class LineOfActionNode(base.BaseNode):
    def __init__(self):
        base.BaseNode.__init__(self)
        self._zFiber = None

    def set_fiber(self,fiber):
        self._zFiber = fiber

    def get_fiber(self,longName=False):
        return self._zFiber


    def print_(self):
        super(LineOfActionNode, self).print_()
        if self.get_fiber():
            print 'zFiber: ',self.get_fiber(longName=True)

    def string_replace(self,search,replace):
        super(LineOfActionNode, self).string_replace(search,replace)

        # name replace----------------------------------------------------------
        name = self.get_fiber(longName=True)
        if name:
           newName = base.replace_longname(search,replace,name)
           self.set_fiber(newName)



