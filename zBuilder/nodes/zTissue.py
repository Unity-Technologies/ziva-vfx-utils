import zBuilder.nodes.base as base
import logging

logger = logging.getLogger(__name__)


class TissueNode(base.BaseNode):
    def __init__(self):
        base.BaseNode.__init__(self)
        self._children_tissues = None
        self._parent_tissue = None

    def set_children_tissues(self, children):
        self._children_tissues = children

    def get_children_tissues(self):
        return self._children_tissues

    def set_parent_tissue(self, parent):
        self._parent_tissue = parent

    def get_parent_tissue(self):
        return self._parent_tissue

    def print_(self):
        super(TissueNode, self).print_()
        if self.get_children_tissues():
            print 'children: ', self.get_children_tissues()
        if self.get_parent_tissue():
            print 'parent: ', self.get_parent_tissue()

    def string_replace(self, search, replace):
        super(TissueNode, self).string_replace(search, replace)







