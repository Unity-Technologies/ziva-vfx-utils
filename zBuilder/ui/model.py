from Qt import QtGui, QtWidgets, QtCore, QtCompat
from icons import get_icon_path_from_node

class SceneGraphModel(QtCore.QAbstractItemModel):

    sortRole = QtCore.Qt.UserRole
    filterRole = QtCore.Qt.UserRole + 1
    nodeRole = QtCore.Qt.UserRole + 2

    def __init__(self, root, parent=None):
        super(SceneGraphModel, self).__init__(parent)
        self.root_node = root

    def rowCount(self, parent):
        if not parent.isValid():
            parentNode = self.root_node
        else:
            parentNode = parent.internalPointer()

        return parentNode.child_count()

    def columnCount(self, parent):
        return 1

    def flags(self, index):
        return QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable

    def headerData(self, section, orientation, role):
        if role == QtCore.Qt.DisplayRole:
            return "Scene Items"

    def setData(self, index, value, role=QtCore.Qt.EditRole):

        if index.isValid():

            if role == QtCore.Qt.EditRole:

                node = index.internalPointer()
                node.name = value

                return True

        return False


    def data(self, index, role):

        if not index.isValid():
            return None

        node = index.internalPointer()

        if role == QtCore.Qt.DisplayRole or role == QtCore.Qt.EditRole:
            if index.column() == 0:
                return node.name

            if index.column() == 1:
                if hasattr(node, 'type'):
                    return node.type

        if role == QtCore.Qt.DecorationRole:
            if index.column() == 0:
                if hasattr(node, 'type'):
                    return QtGui.QIcon(QtGui.QPixmap(get_icon_path_from_node(node)))

        if role == SceneGraphModel.sortRole:
            if hasattr(node, 'type'):
                return node.type

        if role == SceneGraphModel.nodeRole:
            if index.column() == 0:
                if hasattr(node, 'type'):
                    return node

    def parent(self, index):

        node = self.getNode(index)
        parentNode = node.parent()

        if parentNode == self.root_node or parentNode == None:
            return QtCore.QModelIndex()

        return self.createIndex(parentNode.row(), 0, parentNode)

    def index(self, row, column, parent):

        parentNode = self.getNode(parent)

        childItem = parentNode.child(row)

        if childItem:
            return self.createIndex(row, column, childItem)
        else:
            return QtCore.QModelIndex()

    def getNode(self, index):
        if index.isValid():
            node = index.internalPointer()
            if node:
                return node

        return self.root_node
