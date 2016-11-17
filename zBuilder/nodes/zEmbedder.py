
from base import BaseNode


class EmbedderNode(BaseNode):
    def __init__(self):
        BaseNode.__init__(self)
        self._association = {}

    def string_replace(self,search,replace,name=True,association=True):
        print 'zEmbedder:string_replace'
        #print self.get_association()
        pass

    def get_association(self,longName=False):
        return self._association