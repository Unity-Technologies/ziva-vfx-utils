from zBuilder.nodes.base import BaseNode
import re

class SkinClusterNode(BaseNode):
    def __init__(self):
        BaseNode.__init__(self)
        self.__influneces = []

    def set_influences(self,influences):
        self.__influneces = influences

    def get_influences(self,longName=False):
        return self.__influneces

    def print_(self):
        super(SkinClusterNode, self).print_()
        if self.get_influences(longName=True):
            print 'influences: ', self.get_influences(longName=True)
