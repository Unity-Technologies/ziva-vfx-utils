from collections import defaultdict
from maya import cmds
from PySide2 import QtCore, QtGui
from ..uiUtils import get_icon_path_from_node, get_node_by_index, nodeRole
from .treeItem import TreeItem


class ComponentTreeModel(QtCore.QAbstractItemModel):
    """ Tree model for component
    """

    def __init__(self, builder, root_node=None, parent=None):
        super(ComponentTreeModel, self).__init__(parent)
        self._builder = builder
        self._root_node = root_node if root_node else TreeItem()
        self._component_nodes_dict = defaultdict(list)

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
            return "ComponentTreeModel"

    def setData(self, index, value, role=QtCore.Qt.EditRole):
        node = get_node_by_index(index, None)
        assert node, "Can't get node through QModelIndex."

        is_data_set = False
        if role == QtCore.Qt.EditRole:
            long_name = node.data.long_name
            short_name = node.data.name
            if value and value != short_name:
                name = cmds.rename(long_name, value)
                self._builder.string_replace("^{}$".format(short_name), name)
                node.data.name = name
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
        if role == QtCore.Qt.DecorationRole:
            # icon
            if hasattr(node.data, "type"):
                parent_name = node.parent.data.name if node.parent.data else None
                return QtGui.QIcon(QtGui.QPixmap(get_icon_path_from_node(node.data, parent_name)))
        if role == nodeRole and hasattr(node.data, "type"):
            # attached node, such as zBuilder node
            return node.data
        if role == QtCore.Qt.BackgroundRole:
            if index.row() % 2 == 0:
                return QtGui.QColor(54, 54, 54)  # gray

    def parent(self, index):
        child_node = get_node_by_index(index, self._root_node)
        parent_node = child_node.parent
        if parent_node == self._root_node or parent_node is None:
            return QtCore.QModelIndex()
        return self.createIndex(parent_node.row(), 0, parent_node)

    def index(self, row, column, parent):
        if not self.hasIndex(row, column, parent):
            return QtCore.QModelIndex()

        parent_node = get_node_by_index(parent, self._root_node)
        return self.createIndex(row, column, parent_node.child(row))

    # End of QtCore.QAbstractItemModel override functions
