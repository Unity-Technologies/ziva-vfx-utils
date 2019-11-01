from PySide2 import QtGui, QtWidgets, QtCore
from icons import get_icon_path_from_node


class SceneGraphModel(QtCore.QAbstractItemModel):
    # scene_item.type ( zTissue, zBone, ... )
    sortRole = QtCore.Qt.UserRole
    # scene_item object
    nodeRole = QtCore.Qt.UserRole + 1
    # full name of scene_item object in the scene
    fullNameRole = QtCore.Qt.UserRole + 2
    # if scene_item object expanded or not
    expandedRole = QtCore.Qt.UserRole + 3

    def __init__(self, root, parent=None):
        super(SceneGraphModel, self).__init__(parent)
        """expandedRole is not supported if parent == None
        """
        # .parent() method didn't work in Linux
        # created .parent_ instead
        self.root_node = root
        self.parent_ = parent

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
            return node.name

        if role == QtCore.Qt.DecorationRole:
            if hasattr(node, 'type'):
                return QtGui.QIcon(QtGui.QPixmap(get_icon_path_from_node(node)))

        if role == SceneGraphModel.sortRole:
            if hasattr(node, 'type'):
                return node.type

        if role == SceneGraphModel.nodeRole:
            if hasattr(node, 'type'):
                return node

        if role == SceneGraphModel.fullNameRole:
            return node.long_name

        if role == SceneGraphModel.expandedRole:
            # return if index is expanded if possible
            # otherwise return None instead of False to simplify debugging
            tree = None
            if isinstance(self.parent_, QtWidgets.QTreeView):
                tree = self.parent_
            elif self.parent_:
                if isinstance(self.parent_.parent_, QtWidgets.QTreeView):
                    tree = self.parent_.parent_

            if tree:
                index = self.parent_.mapFromSource(index)
                if index.isValid():
                    return tree.isExpanded(index)
            else:
                raise Exception(
                    "Could not query expandedRole. QTreeView parent of SceneGraphModel not found.")

    def parent(self, index):

        node = self.getNode(index)
        parentNode = node.parent

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


class SceneSortFilterProxyModel(QtCore.QSortFilterProxyModel):
    # .parent() method didn't work in Linux
    # created .parent_ instead
    def __init__(self, parent=None):
        super(SceneSortFilterProxyModel, self).__init__(parent)
        self.parent_ = parent
