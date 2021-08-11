import logging
import re

from zBuilder.nodes.base import Base
from zBuilder.builder import Builder
from zBuilder.commonUtils import is_sequence

logger = logging.getLogger(__name__)


class TreeItem(object):
    """ Data structure for tree models in Scene Panel 2.
    It stores zBuilder nodes, GroupNode and other Scene Panel nodes as a tree structure.
    Its interface is similar to zBuilder Base class.
    The main difference is the Base class is derived by Maya scene nodes and contains ZivaVFX nodes info.
    """
    def __init__(self, parent=None, data=None):
        super(TreeItem, self).__init__()
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
        """ Return child node according to specified index.
        This is for QtCore.QAbstractItemModel.index() function.
        """
        return self._children[row]

    @property
    def children(self):
        return self._children

    def child_count(self):
        return len(self._children)

    def append_children(self, new_children):
        """ Append children to children list
        Args:
            new_children (list[TreeItem]): nodes to append
        """
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

    def insert_children(self, index, new_children):
        """ Insert children to index position
        Args:
            index(int): insertion point
            new_children (list[TreeItem]): nodes to append
        """
        if not new_children:
            return

        if not is_sequence(new_children):
            new_children = [new_children]

        offset = 0  # to keep the new_children's insertion order
        for new_child in new_children:
            if new_child._parent is self:
                # Skip self assignment
                continue

            if new_child._parent:
                new_child._parent._children.remove(new_child)
            new_child._parent = self
            self._children.insert(index + offset, new_child)
            offset += 1

    def remove_children(self, children):
        """Remove child from children list
        Args:
            children (list[TreeItem]): nodes to remove
        """
        assert children, "Children to remove is None."
        if not is_sequence(children):
            children = [children]

        for child in children:
            assert child._parent is self, "Node {} is not node {} child"
            child._parent._children.remove(child)
            child._parent = None

    def row(self):
        """ Return the index of the node from parent view.
        Return 0 if parent is None.
        This is required by Qt tree view.
        """
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
        """ Return tree node data with give column index.
        This is required by Qt tree view.
        """
        raise NotImplementedError

    def column_count(self):
        """ Return number of column to display for the tree node data.
        This is required by Qt tree view.
        """
        raise NotImplementedError


def build_scene_panel_tree(input_node, node_type_filter=None):
    """ Create and return the corresponding Scene Panel tree structure by given node.
    Args:
        input_node(:obj:`Base, Builder`): Either Base or Builder class instance.
        node_type_filer (:obj:`list[str]`): List of node type names.
            If provide, only node type in this list  will be created.
            If None, all nodes are created.
    Returns:
        1. If input_node is a valid node, return list contains single TreeItem element
           correspond to input_node, with all its valid descendants.
        2. If input node is an invalid node, return list of all its valid descendants.
        3. Empty list if none valid node is found.
    """
    assert isinstance(
        input_node,
        (Base,
         Builder)), "Input node: {} must be Base or Builder class instance.".format(input_node)

    if node_type_filter:
        assert is_sequence(node_type_filter), "node_type_filter needs to be sequence type."

    builder_node = input_node.root_node if isinstance(input_node, Builder) else input_node
    # Following node is valid:
    # 1. When node filter is empty, all nodes are valid
    # 2. Root node is always valid
    # 3. Nodes that matches node type filter
    is_valid_node = lambda node: (not node_type_filter) or (node.name is "ROOT") or (
        node.type in node_type_filter)

    # If input node is invalid type, skip it.
    # Instead, go through its children and find valid nodes. Group them as a list
    return_nodes = TreeItem(None, builder_node) if is_valid_node(builder_node) else []

    if builder_node and builder_node.child_count() > 0:
        # Recursive create child TreeItem
        for builder_child_node in builder_node.children:
            child_node = build_scene_panel_tree(builder_child_node, node_type_filter)
            if child_node:
                if is_sequence(return_nodes):
                    return_nodes.extend(child_node)
                else:
                    return_nodes.append_children(child_node)

    if return_nodes and not is_sequence(return_nodes):
        return_nodes = [return_nodes]
    return return_nodes


def prune_child_nodes(nodes):
    """ Given TreeItem list, prune the child nodes whose parent node also in the list.
    """
    pruned_node_list = []
    for node in nodes:
        cur_node = node
        find_duplicate = False
        # Recursively check each node till root node
        while not cur_node.parent.is_root_node():
            if cur_node.parent in nodes:
                find_duplicate = True
                break
            cur_node = cur_node.parent
        if not find_duplicate:
            pruned_node_list.append(node)
    return pruned_node_list


def create_subtree(child_nodes, new_node_data=None):
    """ Given TreeItem list, return a new TreeItem that contains them.
    The child_nodes may contain parent-child relation nodes,
    their relationship will be kept.
    Only the out most nodes will be attached to the new node.
    """
    new_node = TreeItem(None, new_node_data)
    new_node.append_children(prune_child_nodes(child_nodes))
    return new_node


# Helper functions for pick_out_node()
def is_node_name_duplicate(node_to_check, node_list):
    for node in node_list:
        if node.data.name == node_to_check.data.name:
            return True
    return False


def fix_node_name_duplication(node_to_fix, node_list):
    # Find ending digits, if any
    pattern = re.compile(r".*?(\d+)$")
    new_node_name = node_to_fix.data.name
    result = re.match(pattern, new_node_name)
    base_name = new_node_name.rstrip(result.group(1)) if result else new_node_name
    index = 1
    while True:
        find_conflict = False
        for node in node_list:
            if node.data.name == new_node_name:
                find_conflict = True
                break
        if find_conflict:
            new_node_name = "{}{}".format(base_name, index)
            index += 1
        else:
            break
    node_to_fix.data.name = new_node_name


def pick_out_node(node_to_pick_out, is_node_duplicated_pred, fix_duplication_proc):
    """ Delete the given node, move its decendants to its parent node.
    Args:
        node_to_pick_out(TreeItem): The TreeItem to pick out
        node_duplicate_proc(function): A predicate that check whether
            the pick out node's children conflicts with the sibling nodes.
        fix_duplication_proc(function): A procedure that fixes the node duplication
    """
    parent_node = node_to_pick_out.parent
    assert parent_node, "Pick out node has no parent."
    insert_point = node_to_pick_out.row()
    sibling_nodes = [node for node in parent_node.children if node is not node_to_pick_out]
    child_nodes_to_move = node_to_pick_out.children
    parent_node.remove_children(node_to_pick_out)

    for child in child_nodes_to_move:
        # Check child nodes against its sibling node
        if is_node_duplicated_pred(child, sibling_nodes):
            fix_duplication_proc(child, sibling_nodes)
        # Ready to insert
        parent_node.insert_children(insert_point, child)
