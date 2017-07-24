from zBuilder.nodes.base import BaseNode
import logging

logger = logging.getLogger(__name__)


class TissueNode(BaseNode):
    def __init__(self):
        BaseNode.__init__(self)
        self._children_tissues = None
        self._parent_tissue = None

    def set_children_tissues(self, children):
        self._children_tissues = children

    def set_parent_tissue(self, parent):
        self._parent_tissue = parent

    def get_children_tissues(self, longName=False):
        if not longName:
            tmp = []
            if self._children_tissues:
                for item in self._children_tissues:
                    tmp.append(item.split('|')[-1])
                return tmp
            else:
                return None
        else:
            return self._children_tissues

    def get_parent_tissue(self, longName=False):
        if self._parent_tissue:
            if longName:
                return self._parent_tissue
            else:
                return self._parent_tissue.split('|')[-1]
        else:
            return None

    def print_(self):
        super(TissueNode, self).print_()
        if self.get_children_tissues():
            print 'children: ', self.get_children_tissues(longName=True)
        if self.get_parent_tissue():
            print 'parent: ', self.get_parent_tissue(longName=True)

    def string_replace(self, search, replace):
        super(TissueNode, self).string_replace(search, replace)

        # name replace----------------------------------------------------------
        parent = self.get_parent_tissue(longName=True)
        if parent:
            newName = self.replace_longname(search, replace, parent)
            self.set_parent_tissue(newName)

        children = self.get_children_tissues(longName=True)
        if children:
            new_names = list()
            for child in children:
                new_names.append(self.replace_longname(search, replace, child))
            self.set_children_tissues(new_names)




