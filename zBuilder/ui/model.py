from PySide2 import QtGui, QtWidgets, QtCore
from icons import get_icon_path_from_node
import zBuilder.zMaya as mz


class SceneGraphModel(QtCore.QAbstractItemModel):
    # scene_item.type ( zTissue, zBone, ... )
    sortRole = QtCore.Qt.UserRole
    # scene_item object
    nodeRole = QtCore.Qt.UserRole + 1
    # long name of scene_item object in the scene
    longNameRole = QtCore.Qt.UserRole + 2
    # is node enabled
    enableRole = QtCore.Qt.UserRole + 3

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

        if role == SceneGraphModel.longNameRole:
            return node.long_name

        if role == SceneGraphModel.enableRole:
            enable = True
            node = index.internalPointer()
            # If node is a mesh, then take enable status from it's child
            if hasattr(node, 'depends_on'):
                mobject = node.depends_on
                # Get associated node name with a mesh
                # e.g. for the tissue mesh find zTissue node name
                name = mz.get_name_from_m_object(mobject)
                # search through the children for the expected node.
                for child in node.children:
                    if child.name == name:
                        node = child
                        break

            # Maya nodes have either of two attributes showing if node is enabled
            # need to check both of them
            attrs = node.attrs
            if "envelope" in attrs:
                enable = attrs["envelope"]["value"]
            elif "enable" in attrs:
                enable = attrs["enable"]["value"]

            return enable

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


class TreeItemDelegate(QtWidgets.QStyledItemDelegate):
    def __init__(self, parent=None):
        super(TreeItemDelegate, self).__init__(parent)

    def paint(self, painter, option, index):
        proxy_model = index.model()
        index_model = proxy_model.mapToSource(index)

        if index_model.isValid():
            model = index_model.model()
            enable = model.data(index_model, model.enableRole)
            if not enable:
                if option.state & QtWidgets.QStyle.State_Selected:
                    option.state &= ~QtWidgets.QStyle.State_Selected
                    option.palette.setColor(QtGui.QPalette.Text, QtGui.QColor(28, 96, 164))
                else:
                    option.palette.setColor(QtGui.QPalette.Text, QtGui.QColor(100, 100, 100))
        QtWidgets.QStyledItemDelegate.paint(self, painter, option, index)
