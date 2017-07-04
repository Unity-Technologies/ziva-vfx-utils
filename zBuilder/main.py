from zBuilder.nodeCollection import NodeCollection
from zBuilder.zMaya import MayaMixin



class Builder(NodeCollection,MayaMixin):

    def __init__(self):
        NodeCollection.__init__(self)
        MayaMixin.__init__(self)

