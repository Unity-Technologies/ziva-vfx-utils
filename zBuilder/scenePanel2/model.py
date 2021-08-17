import logging
import pickle

from ..uiUtils import get_icon_path_from_node, get_node_by_index, zGeo_UI_node_types
from ..uiUtils import sortRole, nodeRole, longNameRole
from .groupNode import GroupNode
from .treeItem import *

from PySide2 import QtGui, QtCore
from maya import cmds

logger = logging.getLogger(__name__)
_mimeType = 'application/x-scenepanelzgeoitemdata'


class SceneGraphModel(QtCore.QAbstractItemModel):
    """ The tree model for zGeo TreeView.
    """
    def __init__(self, builder, parent=None):
        super(SceneGraphModel, self).__init__(parent)
        assert builder, "Missing builder parameter in SceneGraphModel"
        self.reset_model(builder)

    def reset_model(self, new_builder):
        self.beginResetModel()
        self._builder = new_builder
        self._root_node = build_scene_panel_tree(
            new_builder, zGeo_UI_node_types + ["zSolver", "zSolverTransform"])[0]
        self.endResetModel()

    # QtCore.QAbstractItemModel override functions
    def rowCount(self, parent):
        parent_node = get_node_by_index(parent, self._root_node)
        return parent_node.child_count()

    def columnCount(self, parent):
        return 1

    def flags(self, index):
        if not index.isValid():
            return QtCore.Qt.NoItemFlags
        return QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEditable | \
               QtCore.Qt.ItemIsDragEnabled | QtCore.Qt.ItemIsDropEnabled

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
        if role == nodeRole and hasattr(node.data, "type"):
            # node
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
        parent_node.append_children(TreeItem(None, None))  # TODO: multiple addition
        self.endInsertRows()

        return True

    def removeRows(self, row, count, parent):
        self.beginRemoveRows(parent, row, row + count - 1)
        parent_node = get_node_by_index(parent, None)
        assert parent_node, "Could not find parent node, failed to delete child row."
        for i in range(row, row + count):
            try:
                node_to_pick_out = parent_node.child(i)
            except:
                logger.error("The {}'s {}th child doesn't exist.".format(parent_node, i))
                continue

            if isinstance(node_to_pick_out, GroupNode):
                pick_out_node(node_to_pick_out, is_node_name_duplicate, fix_node_name_duplication)
            else:
                parent_node.remove_children(node_to_pick_out)
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

        if dest_node.type != "group":
            logger.warning("Cannot move {} into {}".format(moved_node_data.type, dest_node.type))
            return False

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
        elif len(pickle.loads(data.data(_mimeType))) > 1:  # Only allowing 1 node drop at the moment
            return False
        return True

    # End of QtCore.QAbstractItemModel override functions
