from PySide2 import QtGui, QtWidgets, QtCore
import icons


class SceneTreeView(QtWidgets.QTreeView):
    def __init__(self, parent=None):
        super(SceneTreeView, self).__init__(parent)

    def drawBranches(self, painter, rect, index):
        image_line = QtGui.QImage(icons.get_icon_path_from_name('vline-2'))
        image_opened = QtGui.QImage(icons.get_icon_path_from_name('branch-opened-2'))
        image_closed = QtGui.QImage(icons.get_icon_path_from_name('branch-closed-2'))
        image_more = QtGui.QImage(icons.get_icon_path_from_name('branch-more-2'))
        image_child = QtGui.QImage(icons.get_icon_path_from_name('branch-child-2'))
        image_end = QtGui.QImage(icons.get_icon_path_from_name('branch-end-2'))

        column_count = rect.width() / self.indentation()
        model_index = self.model().mapToSource(index)
        node = model_index.internalPointer()
        row_count = self.model().rowCount(index.parent())

        for column in xrange(column_count):
            x_1 = column * self.indentation()
            x_2 = self.indentation()

            rect = QtCore.QRect(x_1 + 20, rect.top(), x_2,
                                rect.height())
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
                all_parents = []
                parent = index.parent()
                while parent.isValid():
                    all_parents.append(parent)
                    parent = parent.parent()
                column_parent_row_count = self.model().rowCount(all_parents[-(column + 1)])
                column_row_count = all_parents[-(column + 2)].row()
                if column_parent_row_count - 1 != column_row_count:
                    painter.drawImage(rect, image_line)
