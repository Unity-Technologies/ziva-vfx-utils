import logging

from ..uiUtils import nodeRole, get_icon_path_from_name, get_icon_path_from_node
from .model import getNode
from .zGeoView import zGeoTreeView
from .treeNode import TreeNode, build_scene_panel_tree
from PySide2 import QtCore, QtGui, QtWidgets
from collections import defaultdict

logger = logging.getLogger(__name__)

# Component for each zGeo node
component_type_dict = {
    "ui_zBone_body": ["zAttachment", "zBone", "zRivetToBone"],
    "ui_zTissue_body":
    ["zAttachment", "zTissue", "zTet", "zMaterial", "zFiber", "zLineOfAction", "zRestShape"],
    "ui_zCloth_body": ["zAttachment", "zCloth", "zMaterial"]
}


class ComponentTreeModel(QtCore.QAbstractItemModel):
    """ Tree model for each component
    """
    def __init__(self, root_node=None, parent=None):
        super(ComponentTreeModel, self).__init__(parent)
        self.root_node = root_node if root_node else TreeNode()
        self._component_nodes_dict = defaultdict(list)

    # QtCore.QAbstractItemModel override functions
    def rowCount(self, parent):
        parent_node = getNode(parent, self.root_node)
        return parent_node.child_count()

    def columnCount(self, parent):
        return 1

    def flags(self, index):
        if not index.isValid():
            return QtCore.Qt.NoItemFlags
        return QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable | QtCore.Qt.ItemIsEditable

    def headerData(self, section, orientation, role):
        if role == QtCore.Qt.DisplayRole:
            return "ComponentTreeModel"

    def data(self, index, role):
        if not index.isValid():
            return None

        node = index.internalPointer()
        if role == QtCore.Qt.DisplayRole or role == QtCore.Qt.EditRole:
            return node.data.name
        if role == QtCore.Qt.DecorationRole:
            if hasattr(node.data, "type"):
                parent_name = node.parent.data.name if node.parent.data else None
                return QtGui.QIcon(QtGui.QPixmap(get_icon_path_from_node(node.data, parent_name)))
        if role == nodeRole and hasattr(node.data, "type"):
            return node
        if role == QtCore.Qt.BackgroundRole:
            if (index.row() % 2 == 0):
                return QtGui.QColor(54, 54, 54)  # gray

    def parent(self, index):
        child_node = getNode(index, self.root_node)
        parent_node = child_node.parent
        if parent_node == self.root_node or parent_node is None:
            return QtCore.QModelIndex()
        return self.createIndex(parent_node.row(), 0, parent_node)

    def index(self, row, column, parent):
        if not self.hasIndex(row, column, parent):
            return QtCore.QModelIndex()

        parent_node = getNode(parent, self.root_node)
        return self.createIndex(row, column, parent_node.child(row))

    # End of QtCore.QAbstractItemModel override functions


class ComponentSectionWidget(QtWidgets.QWidget):
    """ Widget contains component tree view and affiliated title bar
    """
    def __init__(self, component_type, tree_model, parent=None):
        super(ComponentSectionWidget, self).__init__(parent)

        lblTitle = QtWidgets.QLabel(component_type)
        btnIcon = QtWidgets.QPushButton()
        btnIcon.setIcon(QtGui.QIcon(QtGui.QPixmap(get_icon_path_from_name(component_type))))
        btnIcon.setCheckable(True)
        btnIcon.setChecked(True)
        lytTitle = QtWidgets.QHBoxLayout()
        lytTitle.addWidget(lblTitle)
        lytTitle.addWidget(btnIcon)
        lytTitle.setAlignment(btnIcon, QtCore.Qt.AlignRight)

        self._tvComponent = zGeoTreeView()
        self._tvComponent.setModel(tree_model)
        self._tvComponent.expandAll()
        lytSection = QtWidgets.QVBoxLayout()
        lytSection.addLayout(lytTitle)
        lytSection.addWidget(self._tvComponent)
        self.setLayout(lytSection)

        btnIcon.toggled.connect(self.on_btnIcon_toggled)

    def on_btnIcon_toggled(self, checked):
        self._tvComponent.setVisible(checked)


class ComponentWidget(QtWidgets.QWidget):
    """ The Comopnent tree view widget.
    It contains a ComponentSectionWidget list, which include each component of current selected nodes.
    """
    def __init__(self, parent=None):
        super(ComponentWidget, self).__init__(parent)
        # setup data
        self._component_nodes_dict = defaultdict(list)
        self._component_tree_model_dict = dict()
        # setup ui
        self._lytAllSections = QtWidgets.QVBoxLayout(self)
        self.setLayout(self._lytAllSections)

    def reset_model(self, new_selection):
        self._component_nodes_dict.clear()
        self._component_tree_model_dict.clear()
        while self._lytAllSections.count() > 0:
            lytItem = self._lytAllSections.takeAt(0)
            lytItem.widget().deleteLater()

        if len(new_selection) == 0:
            return  # Early return if nothing to show

        for node in new_selection:
            for component in component_type_dict[node.type]:
                self._component_nodes_dict[component].append(node)

        for component_type, node_list in self._component_nodes_dict.items():
            root_node = TreeNode()
            has_data = False
            for node in node_list:
                child_nodes = build_scene_panel_tree(node, [component_type])
                if child_nodes:
                    zGeo_node = TreeNode(root_node, node)
                    zGeo_node.append_children(child_nodes)
                    has_data = True
            if has_data:
                self._component_tree_model_dict[component_type] = ComponentTreeModel(root_node)

        for component_type, tree_model in self._component_tree_model_dict.items():
            wgtSection = ComponentSectionWidget(component_type, tree_model)
            self._lytAllSections.addWidget(wgtSection)
