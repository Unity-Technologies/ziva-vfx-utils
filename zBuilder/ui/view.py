from PySide2 import QtGui, QtWidgets, QtCore


class SceneTreeView(QtWidgets.QTreeView):
    def __init__(self, parent=None):
        super(SceneTreeView, self).__init__(parent)

    def drawBranches(self, painter, rect, index):
        image_line = QtGui.QImage("./icons/vline.png")
        image_opened = QtGui.QImage("./icons/branch-opened.png")
        image_closed = QtGui.QImage("./icons/branch-closed.png")
        image_more = QtGui.QImage("./icons/branch-more.png")
        image_child = QtGui.QImage("./icons/branch-child.png")
        image_end = QtGui.QImage("./icons/branch-end.png")

        column_count = rect.width()/self.indentation()
        model_index = self.model().mapToSource(index)
        node = model_index.internalPointer()
        row_count = self.model().rowCount(index.parent())
        row_count_parent = self.model().rowCount(index.parent().parent())

        for column in xrange(column_count):
            rect = QtCore.QRect(column * self.indentation(), rect.top(), self.indentation(), rect.height())
            if column == column_count - 1:
                if node.child_count():
                    if self.isExpanded(index):
                        painter.drawImage(rect, image_opened)
                    else:
                        painter.drawImage(rect, image_closed)
                else:
                    painter.drawImage(rect, image_child)
            elif column == column_count - 2:
                if index.row() == row_count - 1:
                    painter.drawImage(rect, image_end)
                else:
                    painter.drawImage(rect, image_more)
            else:
                if index.parent().row() != row_count_parent - 1:
                    painter.drawImage(rect, image_line)
