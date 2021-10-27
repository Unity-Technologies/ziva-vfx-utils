import logging

from ..uiUtils import get_icon_path_from_name
from PySide2 import QtWidgets, QtGui, QtCore

logger = logging.getLogger(__name__)


class zTreeView(QtWidgets.QTreeView):
    """ Common tree view for all Scene Panel 2 tree models.
    """
    # pixel offset from the left
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
        # Changing header size
        # This used to create some space between left/top side of the tree view.
        # It seems "razzle dazzle" but is the only way I could handle that
        header = self.header()
        header.setOffset(-zTreeView.offset)  # padding from left
        header.setFixedHeight(10)  # padding from top

        # Apply background color
        self.setAlternatingRowColors(True)

    # override
    def drawBranches(self, painter, rect, index):
        tree_model = self.model()
        node = index.internalPointer()
        row_count = tree_model.rowCount(index.parent())

        cur_index = None
        cur_parent_index = index
        column_count = rect.width() // self.indentation()
        # Visit column from innermost so cur_index and cur_parent_index
        # keep track of correct index
        for column in reversed(range(column_count)):
            pos_x = column * self.indentation() + zTreeView.offset
            pos_y = rect.top()
            width = self.indentation()
            height = rect.height()
            rect = QtCore.QRect(pos_x, pos_y, width, height)

            if column == column_count - 1:
                # Innermost column
                # Show the item status:
                # - expanded
                # - folded
                # - child
                if node.child_count():
                    if self.isExpanded(index):
                        painter.drawImage(rect, zTreeView.image_opened)
                    else:
                        painter.drawImage(rect, zTreeView.image_closed)
                else:
                    painter.drawImage(rect, zTreeView.image_child)
            elif column == column_count - 2:
                # Column next to innermost
                # Display current parent status:
                # - has more children
                # - no more children
                if index.row() == row_count - 1:
                    painter.drawImage(rect, zTreeView.image_end)
                else:
                    painter.drawImage(rect, zTreeView.image_more)
            else:
                # Column not relate to current item.
                # Only 2 choice:
                # - draw extension line
                # - leave blank
                cur_parent_row_count = tree_model.rowCount(cur_parent_index)
                cur_index_row = cur_index.row()
                if cur_parent_row_count - 1 > cur_index_row:
                    # Draw extension line when current index row number < its parent row count
                    painter.drawImage(rect, zTreeView.image_line)
            # Iterate to next parent
            cur_index = cur_parent_index
            cur_parent_index = cur_index.parent()
