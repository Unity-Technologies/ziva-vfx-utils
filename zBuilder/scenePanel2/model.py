import logging

from ..uiUtils import get_icon_path_from_node, get_node_by_index, zGeo_UI_node_types
from ..uiUtils import sortRole, nodeRole, longNameRole
from .treeNode import build_scene_panel_tree
from .groupNode import GroupNode
from .treeNode import TreeNode
from PySide2 import QtGui, QtCore
from maya import cmds

logger = logging.getLogger(__name__)


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
        return QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEditable

    def headerData(self, section, orientation, role):
        if role == QtCore.Qt.DisplayRole:
            return "zGeo Tree Model"

    def setData(self, index, value, role=QtCore.Qt.EditRole):
        node = get_node_by_index(index, None)
        assert node, "Can't get node through QModelIndex."
        if role == QtCore.Qt.EditRole:
            long_name = node.data.long_name
            short_name = node.data.name
            if value and value != short_name:
                name = cmds.rename(long_name, value)
                self._builder.string_replace("^{}$".format(short_name), name)
                node.data.name = name
            return True
        if role == nodeRole:
            node.data = value
            return True
        return False

    def data(self, index, role):
        if not index.isValid():
            return None
        node = index.internalPointer()
        if role == QtCore.Qt.DisplayRole or role == QtCore.Qt.EditRole:
            return node.data.name
        if role == QtCore.Qt.DecorationRole and hasattr(node.data, "type"):
            parent_name = node.parent.data.name if node.parent.data else None
            return QtGui.QIcon(QtGui.QPixmap(get_icon_path_from_node(node.data, parent_name)))
        if role == nodeRole and hasattr(node.data, "type"):
            return node
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
        self.beginInsertRows(parent, row, row+count-1)
        parent_node = get_node_by_index(parent, None)
        assert parent_node, "Could not find parent node, failed to insert child row."
        parent_node.append_children(TreeNode(None, None)) # TODO: multiple addition
        self.endInsertRows()

        return True

    # End of QtCore.QAbstractItemModel override functions
