from PySide2 import QtGui, QtWidgets, QtCore
import icons
import maya.mel as mm


class GroupedLineEdit(QtWidgets.QLineEdit):
    """
    Groups LineEdits together so after you press Tab it switch focus to sibling
    Sends acceptSignal when Enter or Return buttons pressed
    """
    acceptSignal = QtCore.Signal()

    def __init__(self, parent=None):
        super(GroupedLineEdit, self).__init__(parent)
        self.sibling = None

    def event(self, event):
        if event.type() == QtCore.QEvent.KeyPress and event.key() == QtCore.Qt.Key_Tab:
            if self.sibling:
                self.sibling.setFocus()
                return True

        if event.type() == QtCore.QEvent.KeyPress and event.key() in [
                QtCore.Qt.Key_Enter, QtCore.Qt.Key_Return
        ]:
            self.acceptSignal.emit()
            return True

        return super(GroupedLineEdit, self).event(event)


class MenuWithLabelSeparator(QtWidgets.QMenu):
    def __init__(self, parent=None):
        super(MenuWithLabelSeparator, self).__init__(parent)
        self.setWindowFlags(self.windowFlags() | QtCore.Qt.FramelessWindowHint
                            | QtCore.Qt.NoDropShadowWindowHint)
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground)

    def addMenu(self, *args, **kwargs):
        menu = super(MenuWithLabelSeparator, self).addMenu(*args, **kwargs)
        if isinstance(menu, QtWidgets.QMenu):
            # making widget accepting transparency parameter from stylesheet
            menu.setWindowFlags(menu.windowFlags() | QtCore.Qt.FramelessWindowHint
                                | QtCore.Qt.NoDropShadowWindowHint)
            menu.setAttribute(QtCore.Qt.WA_TranslucentBackground)
        return menu

    # Separator with text, looks like: Text---------
    def addLabel(self, text):
        widget = QtWidgets.QWidget()
        layout = QtWidgets.QHBoxLayout(widget)
        label_text = QtWidgets.QLabel(text)
        line = QtWidgets.QFrame()
        line.setObjectName("line")
        line.setFrameShape(QtWidgets.QFrame.HLine)
        line.setFixedHeight(1)
        size_policy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding,
                                            QtWidgets.QSizePolicy.Fixed)
        size_policy.setHorizontalStretch(0)
        size_policy.setVerticalStretch(0)
        size_policy.setHeightForWidth(line.sizePolicy().hasHeightForWidth())
        line.setSizePolicy(size_policy)
        layout.addWidget(label_text)
        layout.addWidget(line)
        action = QtWidgets.QWidgetAction(self)
        action.setDefaultWidget(widget)
        self.addAction(action)


class ProximityWidget(QtWidgets.QWidget):
    """
    Widget in right-click menu to change map weights for attachments
    """
    def __init__(self, parent=None):
        super(ProximityWidget, self).__init__(parent)
        self.h_layout = QtWidgets.QHBoxLayout(self)
        self.h_layout.setContentsMargins(15, 15, 15, 15)
        self.from_edit = GroupedLineEdit()
        self.from_edit.setFixedHeight(24)
        self.from_edit.setPlaceholderText("From")
        self.from_edit.setText("0.1")
        self.from_edit.setFixedWidth(40)
        self.to_edit = GroupedLineEdit()
        self.to_edit.setFixedHeight(24)
        self.to_edit.setPlaceholderText("To")
        self.to_edit.setText("0.2")
        self.to_edit.setFixedWidth(40)
        self.from_edit.sibling = self.to_edit
        self.to_edit.sibling = self.from_edit
        self.ok_button = QtWidgets.QPushButton()
        self.ok_button.setText("Ok")
        self.h_layout.addWidget(self.from_edit)
        self.h_layout.addWidget(self.to_edit)
        self.h_layout.addWidget(self.ok_button)
        self.ok_button.clicked.connect(self.paintByProx)
        self.from_edit.acceptSignal.connect(self.paintByProx)
        self.to_edit.acceptSignal.connect(self.paintByProx)

    def paintByProx(self):
        """Paints attachment map by proximity.
        """
        mm.eval('zPaintAttachmentsByProximity -min {} -max {}'.format(self.from_edit.text(),
                                                                      self.to_edit.text()))


class SceneTreeView(QtWidgets.QTreeView):
    def __init__(self, parent=None):
        super(SceneTreeView, self).__init__(parent)

    def drawBranches(self, painter, rect, index):
        image_line = QtGui.QImage(icons.get_icon_path_from_name('vline'))
        image_opened = QtGui.QImage(icons.get_icon_path_from_name('branch-opened'))
        image_closed = QtGui.QImage(icons.get_icon_path_from_name('branch-closed'))
        image_more = QtGui.QImage(icons.get_icon_path_from_name('branch-more'))
        image_child = QtGui.QImage(icons.get_icon_path_from_name('branch-child'))
        image_end = QtGui.QImage(icons.get_icon_path_from_name('branch-end'))

        column_count = rect.width() / self.indentation()
        model_index = self.model().mapToSource(index)
        node = model_index.internalPointer()
        row_count = self.model().rowCount(index.parent())

        for column in xrange(column_count):
            # padding from the left side of widget
            offset = 20
            pos_x = column * self.indentation()
            pos_y = rect.top()
            width = self.indentation()
            height = rect.height()
            rect = QtCore.QRect(pos_x + offset, pos_y, width, height)
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
