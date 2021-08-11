class GroupNode(object):
    """ Class for representing group abstraction in ScenePanel 2
    """
    type = "group"

    def __init__(self, name):
        super(GroupNode, self).__init__()
        self._name = name

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, new_val):
        self._name = new_val
