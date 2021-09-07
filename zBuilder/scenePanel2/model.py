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

        if is_zsolver_node(node.data):
            # zSolver* nodes are NOT pin-able, NOT drop-able but drag-able as one can re-order items.
            # Making "zSolver" node drag-able also allows us to visually show that it is not drop-able.
            # On the contrary, if we just make it NOT drag&drop-able, once selected and dragged, it
            # selects multiple items, which is not the expected behavior.
            return QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEditable \
                | QtCore.Qt.ItemIsDragEnabled

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
        self.beginInsertRows(parent, row, row + count - 1)
        parent_node = get_node_by_index(parent, None)
        assert parent_node, "Could not find parent node, failed to insert child row."
        nodes_to_insert = []
        for _ in range(count):
            nodes_to_insert.append(TreeItem(None, None))
        parent_node.insert_children(row, nodes_to_insert)
        self.endInsertRows()
        return True

    def removeRows(self, row, count, parent):
        """ This only for remove single or multiple consecutive rows.
        For remove rows from different parents, or non-consecutive items,
        refer to delete_group_items() and implement our own version.
        """
        self.beginRemoveRows(parent, row, row + count - 1)
        parent_node = get_node_by_index(parent, None)
        assert parent_node, "Could not find parent node, failed to delete child row."
        parent_node.remove_children(parent_node.children[row:row + count])
        self.endRemoveRows()
        return True

    def supportedDropActions(self):
        return QtCore.Qt.MoveAction

    def mimeTypes(self):
        return [_mimeType]

    def mimeData(self, indexes):
        mimeData = QtCore.QMimeData()
        data = [index.data(nodeRole) for index in indexes]
        mimeData.setData(_mimeType, pickle.dumps(data))
        return mimeData

    def dropMimeData(self, data, action, row, column, parent):
        dest_node = parent.data(nodeRole)
        # TODO: add support for multiple move, currently doesn't work'
        moved_node_data = pickle.loads(data.data(_mimeType))[0]

        logger.info("Moving {} into {}".format(moved_node_data.name, dest_node.name))
        row_count = self.rowCount(parent)
        if self.insertRow(row_count, parent):
            child_index = self.index(row_count, 0, parent)
            self.setData(child_index, moved_node_data, nodeRole)
        else:
            logger.error("Failed to move {} into {}!".format(node.name, dest_node.name))
            return False
        return True

    def canDropMimeData(self, data, action, row, column, parent):
        if not parent.isValid():
            return False
        elif not data.hasFormat(_mimeType):
            return False

        drop_candidate_data = pickle.loads(data.data(_mimeType))
        parent_node = get_node_by_index(parent, None)

        if not parent_node:
            logger.error("Drop item contains Invalid data!")
            return False
        elif parent_node.data.type != "group":
            return False
        elif len(drop_candidate_data
                 ) > 1:  #TODO: Remove this condition when multiple drop bug is fixed
            return False

        for i in range(0, len(drop_candidate_data)):
            if is_zsolver_node(drop_candidate_data[i]):
                return False

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

    def move_items(self, index_list_to_move, dst_parent_index, dst_row):
        """ Move specified item to the destination parent at destination row.
        The Qt moveRows() API can't handle complex move items logic.
        After reading https://doc.qt.io/qt-5/model-view-programming.html#resizable-models,
        we choose to manage the index change by ourselves.

        Arguments:
            index_list_to_move (list[QModelIndex]): List of model index. Can be any row at any parent.
            dst_parent_index (QModelIndex): Model index to move to
            dst_row (int): Row position of the destination parent

        Return:
            True if succeeded, False otherwise.
            Error message prints to logger.
        """
        dst_treeitem = get_node_by_index(dst_parent_index, None)
        if dst_treeitem is None:
            # Do nothing if destination parent is None
            logger.error(
                "Can't get destination parent tree item through QModelIndex, failed to move items.")
            return False

        treeitems_to_move = [get_node_by_index(index, None) for index in index_list_to_move]
        if any(item is None for item in treeitems_to_move):
            # Do nothing if there's invalid item in the move list
            logger.error(
                "QModelIndex move list contains invalid entry that has no attached tree item, failed to move items."
            )
            return False

        self.layoutAboutToBeChanged.emit()
        # Move items
        dst_treeitem.insert_children(dst_row, treeitems_to_move)
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
