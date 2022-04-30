import logging
import weakref

from maya import cmds
from PySide2 import QtGui, QtCore
from zBuilder.utils.mayaUtils import get_maya_api_version
from ..uiUtils import (get_node_by_index, get_zSolverTransform_treeitem, validate_group_node_name,
                       get_icon_path_from_node, is_zsolver_node, nodeRole, sortRole, longNameRole)
from .treeItem import (TreeItem, is_group_item, is_node_name_duplicate, fix_node_name_duplication,
                       prune_child_nodes, pick_out_node)
from .groupNode import GroupNode

logger = logging.getLogger(__name__)


class zGeoTreeModel(QtCore.QAbstractItemModel):
    """ The tree model for zGeo TreeView.
    """

    def __init__(self, parent=None):
        super(zGeoTreeModel, self).__init__(parent)
        self._parent_widget = parent
        self._builder_ref = None
        self._root_node_ref = None
        self._is_partial_view = False
        self._drop_items = []

    def reset_model(self, builder, root_node, partial_view):
        self._is_partial_view = partial_view
        self.beginResetModel()
        self._builder_ref = weakref.proxy(builder) if builder else None
        self._root_node_ref = weakref.proxy(root_node) if root_node else None
        self.endResetModel()

    def root_node(self):
        return self._root_node_ref

    # QtCore.QAbstractItemModel override functions
    def rowCount(self, parent):
        parent_node = get_node_by_index(parent, self._root_node_ref)
        return parent_node.child_count() if parent_node else 0

    def columnCount(self, parent):
        return 1

    def flags(self, index):
        if not index.isValid():
            return QtCore.Qt.NoItemFlags

        node = get_node_by_index(index, None)
        assert node, "Can't get node through QModelIndex."

        # Disable drag&drop in Maya 2020 as it causes crash.
        # TODO: Remove this logic when Maya 2020 retires.
        is_maya_2020 = (20200000 <= get_maya_api_version() < 20210000)

        if node.data.type == "zSolver":
            if is_maya_2020:
                return QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEditable
            # zSolver node is NOT pin-able, NOT drop-able but drag-able as one can re-order items.

            # Making zSolver node drag-able also allows us to visually show that it is not drop-able.
            # On the contrary, if we just make it NOT drag&drop-able, once selected and dragged, it
            # selects multiple items, which is not the expected behavior.
            return QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEditable \
                | QtCore.Qt.ItemIsDragEnabled

        if node.data.type == "zSolverTransform":
            if is_maya_2020:
                return QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEditable
            # zSolverTransform node is NOT pin-able, and drag&drop-able.
            # Making zSolverTransform node drag-able also allows us to visually show that it is not drop-able.
            # On the contrary, if we just make it NOT drag&drop-able, once selected and dragged, it
            # selects multiple items, which is not the expected behavior.
            # Making zSolverTransform node drop-able because we need to support reorder its child nodes.
            return QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEditable \
                | QtCore.Qt.ItemIsDragEnabled | QtCore.Qt.ItemIsDropEnabled

        if is_group_item(node):
            if is_maya_2020:
                return QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEditable \
                    | QtCore.Qt.ItemIsUserCheckable | QtCore.Qt.ItemIsAutoTristate

            # Group node is pinable, partially pinable and drag&drop-able
            return QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEditable \
                | QtCore.Qt.ItemIsUserCheckable | QtCore.Qt.ItemIsAutoTristate \
                | QtCore.Qt.ItemIsDragEnabled | QtCore.Qt.ItemIsDropEnabled

        # zGeo node is pinable, drag-able, NOT drop-able
        if is_maya_2020:
            return QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEditable \
                | QtCore.Qt.ItemIsUserCheckable

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
                    name = cmds.rename(node.data.long_name, value)
                    self._builder_ref.string_replace("^{}$".format(short_name), name)
                    node.data.name = name
                is_data_set = True
        elif role == nodeRole:
            node.data = value
            is_data_set = True
        elif role == QtCore.Qt.CheckStateRole:
            node.pin_state = value
            self._parent_widget._on_tvGeo_pinStateChanged(node)
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
        if role == nodeRole:
            # attached zBuilder or Group node
            return node.data
        if role == sortRole and hasattr(node.data, "type"):
            return node.data.type
        if role == longNameRole:
            if hasattr(node.data, "long_name"):
                # Return full path for Maya DGNode
                return node.data.long_name
            # Return TreeItem path for non Maya DGNode
            return node.get_tree_path()
        if role == QtCore.Qt.BackgroundRole:
            if index.row() % 2 == 0:
                return QtGui.QColor(54, 54, 54)  # gray

    def parent(self, index):
        child_node = get_node_by_index(index, self._root_node_ref)
        parent_node = child_node.parent
        if parent_node == self._root_node_ref or parent_node is None:
            return QtCore.QModelIndex()
        return self.createIndex(parent_node.row(), 0, parent_node)

    def index(self, row, column, parent=QtCore.QModelIndex()):
        if not self.hasIndex(row, column, parent):
            return QtCore.QModelIndex()

        parent_node = get_node_by_index(parent, self._root_node_ref)
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
        return ['text/plain']

    def mimeData(self, indexes):
        mimeData = QtCore.QMimeData()
        treeitem_list = [index.internalPointer() for index in indexes]
        # When both parent and child node in the drag&drop list,
        # make sure only parent nodes are pickled.
        # Otherwise the child nodes will separate from the parent node.
        self._drop_items = prune_child_nodes(treeitem_list)
        return mimeData

    def dropMimeData(self, data, action, row, column, parent):
        assert not self._is_partial_view

        drop_node_name = ",".join([item.data.name for item in self._drop_items])
        parent_node = parent.data(nodeRole)
        logger.debug("Dropping mimedata {} to parent {} at row {}".format(
            drop_node_name, parent_node.name, row))

        insertion_row = self.rowCount(parent) if (row == -1) else row
        count = 0
        if self.insertRows(insertion_row, len(self._drop_items), parent):
            # After new rows are created, copy drop item's data and its children
            for item in self._drop_items:
                child_index = self.index(insertion_row + count, 0, parent)
                child_item = get_node_by_index(child_index, None)
                # We directly set values to avoid 'setData' call (reduces execution time)
                child_item.data = item.data
                if not is_group_item(item):
                    child_item.pin_state = item.pin_state
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
        if self._is_partial_view:
            return False

        # Verify parent item
        if not parent.isValid():
            logger.debug("Can't drop because parent is not valid")
            return False
        parent_node = get_node_by_index(parent, None)
        if not parent_node:
            logger.error("Failed to get parent TreeItem through QModelIndex in canDropMimeData().")
            return False
        if parent_node.data.type is None:
            # This is the ROOT node.
            # We don't allow inserting items before first zSolverTransform item.
            logger.debug("Can't drop because it's above the first zSolverTransform.")
            return False
        if parent_node.data.type == "zSolverTransform" and row == 0:
            # Special case: no node can insert before zSolver item
            logger.debug("Can't drop because it's not group or zsolver node")
            return False

        # Verify drop data
        if not self._drop_items:
            logger.debug("Can't drop because empty drop items")
            return False

        if any(is_zsolver_node(item.data) for item in self._drop_items):
            logger.debug("Can't drop because drop data contain zsolver node")
            return False
        # Make sure all select items come from same zSolverTransform node.
        # Otherwise, do early return.
        solver_list = list(set([get_zSolverTransform_treeitem(item) for item in self._drop_items]))
        if len(solver_list) != 1:
            logger.debug("Can't drop data. Selected items come from different zSolver.")
            return False
        assert solver_list[0], "Selected items belong to different zSolverTransform nodes."\
            "There's bug in the code logic."
        parent_solverTM = get_zSolverTransform_treeitem(parent_node)
        if solver_list[0].data != parent_solverTM.data:
            logger.debug("Can't drop selected items to different zSolver.")
            return False

        # Valid drop, good to go
        drop_node_name = ",".join([item.data.name for item in self._drop_items])
        logger.debug("Can drop data {} to parent node {} at row {}".format(
            drop_node_name, parent_node.data.name, row))
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
        assert not self._is_partial_view

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

        self.beginResetModel()
        group_item = TreeItem(None, group_node)
        group_item.append_children(treeitems_to_move)
        group_parent_item.insert_children(group_item_row, group_item)
        self.endResetModel()
        return True

    def delete_group_items(self, group_index_to_delete):
        """ Given group index list, delete those items at the top level.
        """
        assert not self._is_partial_view

        group_item_to_delete = [get_node_by_index(index, None) for index in group_index_to_delete]
        if any(item is None for item in group_item_to_delete):
            logger.error(
                "Can't get group treeitem through QModelIndex, failed to delete group items.")
            return False

        self.beginResetModel()
        items_to_delete = [item for item in prune_child_nodes(group_item_to_delete)]
        for item in items_to_delete:
            pick_out_node(item, is_node_name_duplicate, fix_node_name_duplication)
        self.endResetModel()
        return True
