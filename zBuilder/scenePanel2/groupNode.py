import logging
import re

logger = logging.getLogger(__name__)

class GroupNode(object):
    """ Class for representing group abstraction in ScenePanel 2
    """
    def __init__(self, name=None):
        super(GroupNode, self).__init__()
        self.name = name
        type = "Group"

    def child_count(self):
        return 0 # temporary implementation
