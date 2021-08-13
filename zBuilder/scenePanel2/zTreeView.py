import logging

from ..uiUtils import get_icon_path_from_name
from PySide2 import QtWidgets, QtGui, QtCore

logger = logging.getLogger(__name__)


class zTreeView(QtWidgets.QTreeView):
    """ Common tree view for all Scene Panel tree models.
    """
    # pixel offset from the left horizontally
    offset = 20

    image_line = QtGui.QImage(get_icon_path_from_name('vline'))
    image_opened = QtGui.QImage(get_icon_path_from_name('branch-opened'))
    image_closed = QtGui.QImage(get_icon_path_from_name('branch-closed'))
    image_more = QtGui.QImage(get_icon_path_from_name('branch-more'))
    image_child = QtGui.QImage(get_icon_path_from_name('branch-child'))
    image_end = QtGui.QImage(get_icon_path_from_name('branch-end'))

    def __init__(self, parent=None):
        super(zTreeView, self).__init__(parent)
        self.setIndentation(15)
        # changing header size
        # this used to create some space between left/top side of the tree view and it items
        # "razzle dazzle" but the only way I could handle that
        # height - defines padding from top
        # offset - defines padding from left
        # opposite value of offset should be applied in view.py in drawBranches method
        header = self.header()
        header.setOffset(-zTreeView.offset)
        header.setFixedHeight(10)
        # Apply background color
        self.setAlternatingRowColors(True)

    # override
    def drawBranches(self, painter, rect, index):
        column_count = rect.width() // self.indentation()
        tree_model = self.model()
        model_index = tree_model.mapToSource(index) if isinstance(
            tree_model, QtCore.QAbstractProxyModel) else index
        node = model_index.internalPointer()
        row_count = tree_model.rowCount(index.parent())

        for column in range(column_count):
            # padding from the left side of widget
            pos_x = column * self.indentation()
            pos_y = rect.top()
            width = self.indentation()
            height = rect.height()
            rect = QtCore.QRect(pos_x + zTreeView.offset, pos_y, width, height)

            if column == column_count - 1:
                if node.child_count():
                    if self.isExpanded(index):
                        painter.drawImage(rect, zTreeView.image_opened)
                    else:
                        painter.drawImage(rect, zTreeView.image_closed)
                else:
                    painter.drawImage(rect, zTreeView.image_child)
            elif column == column_count - 2:
                if index.row() == row_count - 1:
                    painter.drawImage(rect, zTreeView.image_end)
                else:
                    painter.drawImage(rect, zTreeView.image_more)
            else:
                all_parents = []
                parent = index.parent()
                while parent.isValid():
                    all_parents.append(parent)
                    parent = parent.parent()
                column_parent_row_count = tree_model.rowCount(all_parents[-(column + 1)])
                column_row_count = all_parents[-(column + 2)].row()
                if column_parent_row_count - 1 != column_row_count:
                    painter.drawImage(rect, zTreeView.image_line)
