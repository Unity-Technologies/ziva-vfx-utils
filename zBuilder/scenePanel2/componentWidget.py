from zBuilder.uiUtils import nodeRole
from PySide2 import QtCore, QtGui


class SelectedGeoListModel(QtCore.QAbstractListModel):
    """
    List model for Component view.
    It stores selected zGeo items from zGeoTreeView.
    """
    def __init__(self, parent=None):
        super(SelectedGeoListModel, self).__init__(parent)
        self._selectedNodeList = []

    def rowCount(self, parent):
        return len(self._selectedNodeList)

    def columnCount(self, parent):
        return 1

    def flags(self, index):
        return QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable

    def headerData(self, section, orientation, role):
        if role == QtCore.Qt.DisplayRole:
            return "Component List"

    def data(self, index, role):
        if not index.isValid():
            return None

        node = self._selectedNodeList[index.row()]
        if role == QtCore.Qt.DisplayRole or role == QtCore.Qt.EditRole:
            return node.long_name

        if role == nodeRole and hasattr(node, 'type'):
            return node

        if role == QtCore.Qt.BackgroundRole:
            if (index.row() % 2 == 0):
                return QtGui.QColor(54, 54, 54) # gray


    def index(self, row, column, parent):
        node = self._selectedNodeList[row]
        return self.createIndex(row, column, node)

    def setNewSelection(self, newSelection):
        # refill the model data
        del self._selectedNodeList[:]
        for item in newSelection:
            self._selectedNodeList.append(item)
        self.layoutChanged.emit()