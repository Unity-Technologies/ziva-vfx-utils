from zBuilder.parameters.base import BaseParameter
import re

class SkinClusterParameter(BaseParameter):
    def __init__(self):
        BaseParameter.__init__(self)
        self.__influneces = []

    def set_influences(self,influences):
        self.__influneces = influences

    def get_influences(self,longName=False):
        return self.__influneces

    def print_(self):
        super(SkinClusterParameter, self).print_()
        if self.get_influences(longName=True):
            print 'influences: ', self.get_influences(longName=True)
