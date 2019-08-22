from PySide2 import QtGui, QtWidgets, QtCore
from icons import get_icon_path_from_node
import maya.cmds as mc
import maya.mel as mm


class RadioButtonsWidget(QtWidgets.QWidget):

    def __init__(self, buttons, checked_button=None, parent=None):
        super(RadioButtonsWidget, self).__init__(parent)
        self.layout = QtWidgets.QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.v_layout = QtWidgets.QVBoxLayout()
        self.group_box = QtWidgets.QGroupBox(self)
        self.buttons = []
        for i, button in enumerate(buttons):
            radio_button = QtWidgets.QRadioButton(self)
            radio_button.setText(button)
            self.buttons.append(radio_button)
            if i == checked_button:
                radio_button.setChecked(True)
            self.v_layout.addWidget(radio_button)
        self.group_box.setLayout(self.v_layout)
        self.layout.addWidget(self.group_box)


class GroupedLineEdit(QtWidgets.QLineEdit):

    def __init__(self, parent=None):
        super(GroupedLineEdit, self).__init__(parent)
        self.sibling = None

    def event(self, event):
        if event.type() == QtCore.QEvent.KeyPress and event.key() == QtCore.Qt.Key_Tab:
            if self.sibling:
                self.sibling.setFocus()
                return True

        return super(GroupedLineEdit, self).event(event)


class CustomMenu(QtWidgets.QMenu):

    def __init__(self, parent=None):
        super(CustomMenu, self).__init__(parent)
        self.setWindowFlags(self.windowFlags() | QtCore.Qt.FramelessWindowHint | QtCore.Qt.NoDropShadowWindowHint)
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground)

    def addMenu(self, *args, **kwargs):
        menu = super(CustomMenu, self).addMenu(*args, **kwargs)
        if isinstance(menu, QtWidgets.QMenu):
            menu.setWindowFlags(menu.windowFlags() | QtCore.Qt.FramelessWindowHint | QtCore.Qt.NoDropShadowWindowHint)
            menu.setAttribute(QtCore.Qt.WA_TranslucentBackground)
        return menu

    def addLabel(self, text):
        widget = QtWidgets.QWidget()
        layout = QtWidgets.QHBoxLayout(widget)
        label_text = QtWidgets.QLabel(text)
        line = QtWidgets.QFrame()
        line.setObjectName("line")
        line.setFrameShape(QtWidgets.QFrame.HLine)
        line.setFixedHeight(1)
        size_policy = QtWidgets.QSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
        size_policy.setHorizontalStretch(0)
        size_policy.setVerticalStretch(0)
        size_policy.setHeightForWidth(line.sizePolicy().hasHeightForWidth())
        line.setSizePolicy(size_policy)
        layout.addWidget(label_text)
        layout.addWidget(line)
        action = QtWidgets.QWidgetAction(self)
        action.setDefaultWidget(widget)
        self.addAction(action)

    def eventFilter(self, obj, event):
        if event.type() == QtCore.QEvent.MouseButtonRelease:
            if isinstance(obj, QtWidgets.QMenu):
                if obj.activeAction():
                    if not obj.activeAction().menu():
                        if obj.activeAction().isCheckable():
                            obj.activeAction().trigger()
                            return True

        return super(CustomMenu, self).eventFilter(obj, event)


class ProximityWidget(QtWidgets.QWidget):

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

    def paintByProx(self):
        """Paints attachment map by proximity.
        """

        mm.eval('zPaintAttachmentsByProximity -min {} -max {}'.format(self.from_edit.text(), self.to_edit.text()))


class SceneGraphModel(QtCore.QAbstractItemModel):
    sortRole = QtCore.Qt.UserRole
    filterRole = QtCore.Qt.UserRole + 1
    nodeRole = QtCore.Qt.UserRole + 2
    envRole = QtCore.Qt.UserRole + 3
    fullNameRole = QtCore.Qt.UserRole + 4
    expandedRole = QtCore.Qt.UserRole + 5

    def __init__(self, root, parent=None):
        super(SceneGraphModel, self).__init__(parent)
        '''
        expandedRole is not supported if parent == None
        '''
        self.root_node = root
        self.parent_ = parent

    def rowCount(self, parent):
        if not parent.isValid():
            parentNode = self.root_node
        else:
            parentNode = parent.internalPointer()

        return parentNode.child_count()

    def columnCount(self, parent):
        return 1

    def flags(self, index):
        return QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEditable

    def headerData(self, section, orientation, role):
        if role == QtCore.Qt.DisplayRole:
            return "Scene Items"

    def setData(self, index, value, role=QtCore.Qt.EditRole):
        if role == QtCore.Qt.EditRole:
            node = index.internalPointer()
            long_name = node.long_name
            if value and value != long_name.split('|')[-1]:
                name = mc.rename(long_name, value)
                node.name = name
        return super(SceneGraphModel, self).setData(index, value, role)

    def data(self, index, role):

        if not index.isValid():
            return None

        node = index.internalPointer()

        if role == QtCore.Qt.DisplayRole or role == QtCore.Qt.EditRole:
            if index.column() == 0:
                return node.name

            if index.column() == 1:
                if hasattr(node, 'type'):
                    return node.type

        if role == QtCore.Qt.DecorationRole:
            if index.column() == 0:
                if hasattr(node, 'type'):
                    return QtGui.QIcon(QtGui.QPixmap(get_icon_path_from_node(node)))

        if role == SceneGraphModel.sortRole:
            if hasattr(node, 'type'):
                return node.type

        if role == SceneGraphModel.nodeRole:
            if index.column() == 0:
                if hasattr(node, 'type'):
                    return node

        if role == SceneGraphModel.envRole:
            env = True
            if index.column() == 0:
                node = index.internalPointer()
                if hasattr(node, 'depends_on'):
                    node = node.depends_on
                if hasattr(node, 'attrs'):
                    attrs = node.attrs
                    if "envelope" in attrs:
                        if not attrs["envelope"]["value"]:
                            env = False
                    elif "enable" in attrs:
                        if not attrs["enable"]["value"]:
                            env = False
            return env

        if role == SceneGraphModel.fullNameRole:
            return node.long_name

        if role == SceneGraphModel.expandedRole:
            # return if index is expanded if possible
            # otherwise return None instead of False to simplify debugging
            tree = None
            if isinstance(self.parent_, QtWidgets.QTreeView):
                tree = self.parent_
            elif self.parent_:
                if isinstance(self.parent_.parent(), QtWidgets.QTreeView):
                    tree = self.parent_.parent()

            if tree:
                index = self.parent_.mapFromSource(index)
                if index.isValid():
                    return tree.isExpanded(index)
            else:
                raise Exception(
                    "Could not query expandedRole. QTreeView parent of SceneGraphModel not found.")

    def parent(self, index):

        node = self.getNode(index)
        parentNode = node.parent()

        if parentNode in (self.root_node, None):
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


class SceneSortFilterProxyModel(QtCore.QSortFilterProxyModel):
    def __init__(self, parent=None):
        super(SceneSortFilterProxyModel, self).__init__(parent)


class TreeItemDelegate(QtWidgets.QStyledItemDelegate):
    def __init__(self, parent=None):
        super(TreeItemDelegate, self).__init__(parent)

    def paint(self, painter, option, index):
        proxy_model = index.model()
        index_model = proxy_model.mapToSource(index)

        if index_model.isValid():
            model = index_model.model()
            env = model.data(index_model, model.envRole)
            if not env:
                if option.state & QtWidgets.QStyle.State_Selected:
                    option.state &= ~QtWidgets.QStyle.State_Selected
                    option.palette.setColor(QtGui.QPalette.Text, QtGui.QColor(28, 96, 164))
                else:
                    option.palette.setColor(QtGui.QPalette.Text, QtGui.QColor(100, 100, 100))
        QtWidgets.QStyledItemDelegate.paint(self, painter, option, index)
