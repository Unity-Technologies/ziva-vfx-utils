from PySide2 import QtGui, QtWidgets, QtCore
from ..uiUtils import get_icon_path_from_name


class SceneTreeView(QtWidgets.QTreeView):
    # pixel offset from the left horizontally
    offset = 20

    def __init__(self, parent=None):
        super(SceneTreeView, self).__init__(parent)

    def drawBranches(self, painter, rect, index):
        image_line = QtGui.QImage(get_icon_path_from_name('vline'))
        image_opened = QtGui.QImage(get_icon_path_from_name('branch-opened'))
        image_closed = QtGui.QImage(get_icon_path_from_name('branch-closed'))
        image_more = QtGui.QImage(get_icon_path_from_name('branch-more'))
        image_child = QtGui.QImage(get_icon_path_from_name('branch-child'))
        image_end = QtGui.QImage(get_icon_path_from_name('branch-end'))

        column_count = rect.width() // self.indentation()
        model_index = self.model().mapToSource(index)
        node = model_index.internalPointer()
        row_count = self.model().rowCount(index.parent())

        for column in range(column_count):
            # padding from the left side of widget
            pos_x = column * self.indentation()
            pos_y = rect.top()
            width = self.indentation()
            height = rect.height()
            rect = QtCore.QRect(pos_x + self.offset, pos_y, width, height)
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
