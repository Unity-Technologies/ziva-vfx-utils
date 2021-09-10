import logging
import pickle

from ..uiUtils import *
from .groupNode import GroupNode
from .treeItem import *

from PySide2 import QtGui, QtCore
from maya import cmds

logger = logging.getLogger(__name__)
_mimeType = 'application/x-scenepanelzgeoitemdata'


class SceneGraphModel(QtCore.QAbstractItemModel):
    """ The tree model for zGeo TreeView.
    """
    def __init__(self, parent=None):
        super(SceneGraphModel, self).__init__(parent)
        self._parent_widget = parent
        self._builder = None
        self._root_node = None

    def reset_model(self, new_builder):
        self.beginResetModel()
        self._builder = new_builder
        self._root_node = build_scene_panel_tree(
            new_builder, zGeo_UI_node_types +
            ["zSolver", "zSolverTransform"])[0] if new_builder else None
        self.endResetModel()

    def root_node(self):
        return self._root_node

    # QtCore.QAbstractItemModel override functions
    def rowCount(self, parent):
        parent_node = get_node_by_index(parent, self._root_node)
        return parent_node.child_count() if parent_node else 0

    def columnCount(self, parent):
        return 1

    def flags(self, index):
        if not index.isValid():
            return QtCore.Qt.NoItemFlags

        node = get_node_by_index(index, None)
        assert node, "Can't get node through QModelIndex."

        if node.data.type == "zSolver":
            # zSolver node is NOT pin-able, NOT drop-able but drag-able as one can re-order items.
            # Making zSolver node drag-able also allows us to visually show that it is not drop-able.
            # On the contrary, if we just make it NOT drag&drop-able, once selected and dragged, it
            # selects multiple items, which is not the expected behavior.
            return QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEditable \
                | QtCore.Qt.ItemIsDragEnabled

        if node.data.type == "zSolverTransform":
            # zSolverTransform node is NOT pin-able, and drag&drop-able.
            # Making zSolverTransform node drag-able also allows us to visually show that it is not drop-able.
            # On the contrary, if we just make it NOT drag&drop-able, once selected and dragged, it
            # selects multiple items, which is not the expected behavior.
            # Making zSolverTransform node drop-able because we need to support reorder its child nodes.
            return QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEditable \
                | QtCore.Qt.ItemIsDragEnabled | QtCore.Qt.ItemIsDropEnabled

        if is_group_item(node):
            # Group node is pinable, partially pinable and drag&drop-able
            return QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEditable \
                | QtCore.Qt.ItemIsUserCheckable |  QtCore.Qt.ItemIsAutoTristate \
                | QtCore.Qt.ItemIsDragEnabled | QtCore.Qt.ItemIsDropEnabled

        # zGeo node is pinable, drag-able, NOT drop-able
        return QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEditable \
            | QtCore.Qt.ItemIsUserCheckable \
            | QtCore.Qt.ItemIsDragEnabled

    def headerData(self, section, orientation, role):
        if role == QtCore.Qt.DisplayRole:
            return "zGeo Tree Model"

    def setData(self, index, value, role=QtCore.Qt.EditRole):
        node = get_node_by_index(index, None)
        assert node, "Can't get node through QModelIndex."
        is_data_set = False
        if role == QtCore.Qt.EditRole:
            long_name = node.data.long_name
            short_name = node.data.name
            if value and value != short_name:
                if isinstance(node.data, GroupNode):
                    if not validate_group_node_name(value):
                        logger.warning(
                            "Group name must start with alphabet and can only have alphanumeric values and underscore in it."
                        )
                        return False
                    node.data.name = value
                    sibling_nodes = node.get_siblings()
                    if is_node_name_duplicate(node, sibling_nodes):
                        fix_node_name_duplication(node, sibling_nodes)
                else:
                    name = cmds.rename(long_name, value)
                    self._builder.string_replace("^{}$".format(short_name), name)
                    node.data.name = name
                is_data_set = True
        elif role == nodeRole:
            node.data = value
            is_data_set = True
        elif role == QtCore.Qt.CheckStateRole:
            node.pin_state = value
            self._parent_widget.on_tvGeo_pinStateChanged(node)
            is_data_set = True

        if is_data_set:
            self.dataChanged.emit(index, index, role)
        return is_data_set

    def data(self, index, role):
        if not index.isValid():
            return None
        node = index.internalPointer()
        if role == QtCore.Qt.DisplayRole or role == QtCore.Qt.EditRole:
            # text
            return node.data.name
        if role == QtCore.Qt.DecorationRole and hasattr(node.data, "type"):
            # icon
            parent_name = node.parent.data.name if node.parent.data else None
            return QtGui.QIcon(QtGui.QPixmap(get_icon_path_from_node(node.data, parent_name)))
        if role == QtCore.Qt.CheckStateRole:
            # checkbox
            return node.pin_state
        if role == nodeRole and hasattr(node.data, "type"):
            # attached node, such as zBuilder node
            return node.data
        if role == sortRole and hasattr(node.data, "type"):
            return node.data.type
        if role == longNameRole:
            return node.data.long_name
        if role == QtCore.Qt.BackgroundRole:
            if index.row() % 2 == 0:
                return QtGui.QColor(54, 54, 54)  # gray

    def parent(self, index):
        child_node = get_node_by_index(index, self._root_node)
        parent_node = child_node.parent
        if parent_node == self._root_node or parent_node is None:
            return QtCore.QModelIndex()
        return self.createIndex(parent_node.row(), 0, parent_node)

    def index(self, row, column, parent=QtCore.QModelIndex()):
        if not self.hasIndex(row, column, parent):
            return QtCore.QModelIndex()

        parent_node = get_node_by_index(parent, self._root_node)
        return self.createIndex(row, column, parent_node.child(row))

    def insertRows(self, row, count, parent):
        parent_node = get_node_by_index(parent, None)
        if not parent_node:
            logger.error("Can't get parent item through QModelIndex, failed to insert rows.")
            return False

        self.beginInsertRows(parent, row, row + count - 1)
        nodes_to_insert = []
        for _ in range(count):
            nodes_to_insert.append(TreeItem(None, None))
        logger.debug("Insert {} rows to node {} at row {}.".format(count, parent_node.data.name,
                                                                   row))
        parent_node.insert_children(row, nodes_to_insert)
        self.endInsertRows()
        return True

    def removeRows(self, row, count, parent):
        """ This only for remove single or multiple consecutive rows.
        For remove rows from different parents, or non-consecutive items,
        refer to delete_group_items() and implement our own version.
        """
        parent_node = get_node_by_index(parent, None)
        if not parent_node:
            logger.error("Can't get parent item through QModelIndex, failed to remove rows.")
            return False

        self.beginRemoveRows(parent, row, row + count - 1)
        logger.debug("Remove {} rows from node {} at row {}.".format(count, parent_node.data.name,
                                                                     row))
        remove_item_name = ",".join(
            [node.data.name for node in parent_node.children[row:row + count]])
        logger.debug("Remove items: {}".format(remove_item_name))
        parent_node.remove_children(parent_node.children[row:row + count])
        self.endRemoveRows()
        return True

    def supportedDropActions(self):
        return QtCore.Qt.MoveAction

    def mimeTypes(self):
        return [_mimeType]

    def mimeData(self, indexes):
        mimeData = QtCore.QMimeData()
        treeitem_list = [index.internalPointer() for index in indexes]
        # When both parent and child node in the drag&drop list,
        # make sure only parent nodes are pickled.
        # Otherwise the child nodes will separate from the parent node.
        pruned_treeitem_list = prune_child_nodes(treeitem_list)
        mimeData.setData(_mimeType, pickle.dumps(pruned_treeitem_list))
        return mimeData

    def dropMimeData(self, data, action, row, column, parent):
        drop_items = pickle.loads(data.data(_mimeType))
        drop_node_name = ",".join([item.data.name for item in drop_items])
        parent_node = parent.data(nodeRole)
        logger.debug("Dropping mimedata {} to parent {} at row {}".format(
            drop_node_name, parent_node.name, row))

        insertion_row = self.rowCount(parent) if (row == -1) else row
        count = 0
        if self.insertRows(insertion_row, len(drop_items), parent):
            # After new rows are created, copy drop item's data and its children
            for item in drop_items:
                child_index = self.index(insertion_row + count, 0, parent)
                self.setData(child_index, item.data, nodeRole)
                child_item = get_node_by_index(child_index, None)
                child_list_copy = item.children[:]
                child_item.append_children(child_list_copy)
                count += 1
            logger.debug("Dropped mimedata {} to parent {} at row {}".format(
                drop_node_name, parent_node.name, row))
            return True

        logger.error("Failed to drop mime data {} to {} at row {}.".format(
            drop_node_name, parent_node.name, row))
        return False

    def canDropMimeData(self, data, action, row, column, parent):
        # Verify parent item
        if not parent.isValid():
            logger.debug("Can't drop because parent is not valid")
            return False
        parent_node = get_node_by_index(parent, None)
        if not parent_node:
            logger.error("Drop item contains Invalid data!")
            return False
        logger.debug("parent_node: {}, type: {}".format(parent_node.data.name,
                                                        parent_node.data.type))

        if parent_node.data.type == "zSolverTransform" and row == 0:
            # Special case: no node can insert before zSolver item
            logger.debug("Can't drop because it's not group or zsolver node")
            return False

        logger.debug("drop row = {}".format(row))
        # Verify drop data
        if not data.hasFormat(_mimeType):
            logger.debug("Can't drop because mime type mismatch")
            return False
        drop_items = pickle.loads(data.data(_mimeType))
        drop_node_name = ",".join([item.data.name for item in drop_items])
        logger.debug("Drop data: {}".format(drop_node_name))
        if any(is_zsolver_node(item.data) for item in drop_items):
            logger.debug("Can't drop because drop data contain zsolver node")
            return False
        logger.debug("Can drop data")
        return True

    # End of QtCore.QAbstractItemModel override functions

    def group_items(self, group_parent_index, group_item_row, group_node, index_list_to_move):
        """ Create a group item at given parent position, and move other items to it.
        
        Arguments:
            group_parent_index(QModelIndex): Index refers to the newly added group item's parent.
            group_item_row(int): Row position the group item will insert to.
            group_node(GroupNode): The group item's data
            index_list_to_move(list[QModelIndex]): List of model index that will be moved to the group item.

        Return:
            True if succeeded, False otherwise.
            Error message prints to logger.
        """
        group_parent_item = get_node_by_index(group_parent_index, None)
        if not group_parent_item:
            logger.error("Can't get group parent item through QModelIndex, failed to group items.")
            return False

        treeitems_to_move = [get_node_by_index(index, None) for index in index_list_to_move]
        if any(item is None for item in treeitems_to_move):
            # Do nothing if there's invalid item in the move list
            logger.error(
                "QModelIndex move list contains invalid entry that has no attached tree item, "
                "failed to group items.")
            return False

        logger.debug("Create Group item {} in parent item {} at row {}".format(
            group_node.name, group_parent_item.data.name, group_item_row))

        self.layoutAboutToBeChanged.emit()
        group_item = TreeItem(None, group_node)
        group_item.append_children(treeitems_to_move)
        group_parent_item.insert_children(group_item_row, group_item)
        self.layoutChanged.emit()
        return True

    def delete_group_items(self, group_index_to_delete):
        """ Given group index list, delete those items at the top level.
        """
        group_item_to_delete = [get_node_by_index(index, None) for index in group_index_to_delete]
        if any(item is None for item in group_item_to_delete):
            logger.error(
                "Can't get group treeitem through QModelIndex, failed to delete group items.")
            return False

        self.layoutAboutToBeChanged.emit()
        items_to_delete = [item for item in prune_child_nodes(group_item_to_delete)]
        for item in items_to_delete:
            pick_out_node(item, is_node_name_duplicate, fix_node_name_duplication)
        self.layoutChanged.emit()
        return True
