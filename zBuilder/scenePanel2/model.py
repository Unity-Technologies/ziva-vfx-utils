from PySide2 import QtGui, QtCore
from zBuilder.uiUtils import get_icon_path_from_node, zGeo_UI_node_types
from zBuilder.uiUtils import sortRole, nodeRole, longNameRole, enableRole
from maya import cmds
import logging

logger = logging.getLogger(__name__)


def getNode(index, defaultNode):
    """
    Given QModelIndex, return zBuilder node
    """
    if index.isValid():
        node = index.internalPointer()
        if node:
            return node
    return defaultNode


class SceneGraphModel(QtCore.QAbstractItemModel):
    def __init__(self, builder, parent=None):
        super(SceneGraphModel, self).__init__(parent)
        assert builder, "Missing builder parameter in SceneGraphModel"
        self.builder = builder
        self.current_parent = None

    def rowCount(self, parent):
        if parent.isValid():
            parentNode = parent.internalPointer()
        else:
            parentNode = self.builder.root_node
        return parentNode.child_count()

    def columnCount(self, parent):
        return 1

    def flags(self, index):
        return QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEditable

    def headerData(self, section, orientation, role):
        if role == QtCore.Qt.DisplayRole:
            return "Scene Items"

    def setData(self, index, value, role=QtCore.Qt.EditRole):
        if index.isValid() and role == QtCore.Qt.EditRole:
            node = index.internalPointer()
            long_name = node.long_name
            short_name = node.name
            if value and value != short_name:
                name = cmds.rename(long_name, value)
                self.builder.string_replace("^{}$".format(short_name), name)
                node.name = name
            return True
        return False

    def data(self, index, role):
        if not index.isValid():
            return None

        node = index.internalPointer()
        '''
        logger.info("index = {}".format(index))
        logger.info("role = {}".format(role))
        logger.info("node = {}".format(node))
        '''
        if role == QtCore.Qt.DisplayRole or role == QtCore.Qt.EditRole:
            return node.name

        if role == QtCore.Qt.DecorationRole:
            if hasattr(node, 'type'):
                return QtGui.QIcon(QtGui.QPixmap(get_icon_path_from_node(node,
                                                                         self.current_parent)))

        if role == sortRole:
            if hasattr(node, 'type'):
                return node.type

        if role == nodeRole:
            if hasattr(node, 'type'):
                return node

        if role == longNameRole:
            return node.long_name

        if role == enableRole:
            enable = True
            node = index.internalPointer()

            # If node is a mesh/curve, then take enable status from it's child
            if hasattr(node, 'depends_on'):
                node = node.depends_on

            # Maya nodes have either of two attributes showing if node is enabled
            # need to check both of them
            attrs = node.attrs
            if "envelope" in attrs:
                enable = attrs["envelope"]["value"]
            elif "enable" in attrs:
                enable = attrs["enable"]["value"]
            return enable

    def parent(self, index):
        node = getNode(index, self.builder.root_node)
        parentNode = node.parent
        if parentNode == self.builder.root_node or parentNode == None:
            return QtCore.QModelIndex()
        return self.createIndex(parentNode.row(), 0, parentNode)

    def index(self, row, column, parent):
        parentNode = getNode(parent, self.builder.root_node)
        childItem = parentNode.child(row)
        if childItem:
            return self.createIndex(row, column, childItem)
        return QtCore.QModelIndex()

    def set_current_parent(self, parent):
        self.current_parent = parent


class zGeoFilterProxyModel(QtCore.QSortFilterProxyModel):
    """
    Provide zGeo nodes to connected views
    """
    def filterAcceptsRow(self, srcRow, srcParent):
        srcIndex = self.sourceModel().index(srcRow, 0, srcParent)
        srcNode = getNode(srcIndex, None)
        assert srcNode, "Invalid source index."
        return (srcNode.type in zGeo_UI_node_types) or srcNode.type.startswith('zSolver')
