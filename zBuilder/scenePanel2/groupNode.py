import logging
import re

logger = logging.getLogger(__name__)

class GroupNode(object):
    """ Class for representing group abstraction in ScenePanel 2
    """
    type = 'group'
    def __init__(self, name):
        super(GroupNode, self).__init__()
        self.name = name
