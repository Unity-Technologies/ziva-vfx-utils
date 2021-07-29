import logging

from zBuilder.commonUtils import is_sequence

logger = logging.getLogger(__name__)


class TreeNode(object):
    ''' Tree data structure for tree views in Scene Panel 2.
    It organizes zBuilder nodes, and other Scene Panel nodes as a tree structure.
    Its interface is similar to zBuilder Base class. 
    The main difference is the Base class is derived by Maya scene nodes and contains ZivaVFX nodes info.
    The TreeNode class serves for Qt model/view paradigm, it accepts any data types that can be shown in the Scene Panel.
    '''
    def __init__(self, parent=None, data=None):
        super(TreeNode, self).__init__()
        if parent:
            parent._children.append(self)
        self._parent = parent

        self._children = []
        # Union of zBuilder node type, or Scene Panel related data types, such as Group node.
        self._data = data

    @property
    def parent(self):
        return self._parent

    @parent.setter
    def parent(self, new_parent):
        if self._parent is new_parent:
            # Skip self assignment
            return

        if self._parent:
            # Remove self from old parent
            self._parent._children.remove(self)

        self._parent = new_parent
        if new_parent:
            new_parent._children.append(self)

    def is_root_node(self):
        return self._parent is None

    def child(self, row):
        ''' Return child node according to specified index.
        This is for QtCore.QAbstractItemModel.index() function.
        '''
        return self._children[row]

    @property
    def children(self):
        return self._children

    def child_count(self):
        return len(self._children)

    def append_children(self, new_children):
        '''Append children to children list
        Args:
            new_children (:obj:`list[TreeNode]`): nodes to append
        '''
        if not new_children:
            return

        if not is_sequence(new_children):
            new_children = [new_children]

        for new_child in new_children:
            if new_child._parent is self:
                # Skip self assignment
                continue

            if new_child._parent:
                new_child._parent._children.remove(new_child)
            new_child._parent = self
            self._children.append(new_child)

    def remove_children(self, children):
        '''Remove child from children list
        Args:
            children (:obj:`list[TreeNode]`): nodes to remove
        '''
        assert children, "Children to remove is None."
        if not is_sequence(children):
            children = [children]

        for child in children:
            assert child._parent is self, "Node {} is not node {} child"
            child._parent._children.remove(child)
            child._parent = None

    def row(self):
        ''' Return the index of the node from parent view.
        Return 0 if parent is None.
        This is required by Qt tree view.
        '''
        if self.parent:
            return self.parent.children.index(self)
        return 0

    @property
    def data(self):
        return self._data

    @data.setter
    def data(self, new_data):
        self._data = new_data

    def data_by_column(self, column):
        ''' Return tree node data with give columen index.
        This is required by Qt tree view.
        '''
        raise NotImplementedError

    def column_count(self):
        ''' Return number of column to display for the tree node data.
        This is required by Qt tree view.
        '''
        raise NotImplementedError
