from zBuilder.nodes import ZivaBaseNode
import logging
import maya.mel as mm

from zBuilder.zMaya import replace_long_name

logger = logging.getLogger(__name__)


class TissueNode(ZivaBaseNode):
    def __init__(self, *args, **kwargs):
        ZivaBaseNode.__init__(self, *args, **kwargs)
        self._children_tissues = None
        self._parent_tissue = None

    def set_children_tissues(self, children):
        self._children_tissues = children

    def set_parent_tissue(self, parent):
        self._parent_tissue = parent

    def get_children_tissues(self, long_name=False):
        if not long_name:
            tmp = []
            if self._children_tissues:
                for item in self._children_tissues:
                    tmp.append(item.split('|')[-1])
                return tmp
            else:
                return None
        else:
            return self._children_tissues

    def get_parent_tissue(self, long_name=False):
        if self._parent_tissue:
            if long_name:
                return self._parent_tissue
            else:
                return self._parent_tissue.split('|')[-1]
        else:
            return None

    def print_(self):
        super(TissueNode, self).print_()
        if self.get_children_tissues():
            print 'children: ', self.get_children_tissues(long_name=True)
        if self.get_parent_tissue():
            print 'parent: ', self.get_parent_tissue(long_name=True)

    def string_replace(self, search, replace):
        super(TissueNode, self).string_replace(search, replace)

        # name replace----------------------------------------------------------
        parent = self.get_parent_tissue(long_name=True)
        if parent:
            newName = replace_long_name(search, replace, parent)
            self.set_parent_tissue(newName)

        children = self.get_children_tissues(long_name=True)
        if children:
            new_names = list()
            for child in children:
                new_names.append(replace_long_name(search, replace, child))
            self.set_children_tissues(new_names)

    # def create(self, *args, **kwargs):
    #     super(TissueNode, self).create(*args, **kwargs)
    #
    #     cmd = 'zQuery -t "{}" -l -m "{}"'.format('zTissue', args[0])
    #     association = mm.eval(cmd)
    #     self.set_association(association)
