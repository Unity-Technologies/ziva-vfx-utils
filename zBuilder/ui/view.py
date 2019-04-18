from PySide2 import QtGui, QtWidgets, QtCore


class SceneTreeView(QtWidgets.QTreeView):
    def __init__(self, parent=None):
        super(SceneTreeView, self).__init__(parent)
