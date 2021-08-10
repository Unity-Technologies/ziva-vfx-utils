import logging

from ..uiUtils import nodeRole, get_icon_path_from_name, get_icon_path_from_node, get_node_by_index
from .zTreeView import zTreeView
from .treeItem import TreeItem, build_scene_panel_tree
from PySide2 import QtCore, QtGui, QtWidgets
from maya import cmds
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
    def __init__(self, builder, root_node=None, parent=None):
        super(ComponentTreeModel, self).__init__(parent)
        self._builder = builder
        self._root_node = root_node if root_node else TreeItem()
        self._component_nodes_dict = defaultdict(list)

    # QtCore.QAbstractItemModel override functions
    def rowCount(self, parent):
        parent_node = get_node_by_index(parent, self._root_node)
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

    def setData(self, index, value, role=QtCore.Qt.EditRole):
        if role == QtCore.Qt.EditRole:
            node = get_node_by_index(index, None)
            if node:
                long_name = node.data.long_name
                short_name = node.data.name
                if value and value != short_name:
                    name = cmds.rename(long_name, value)
                    self._builder.string_replace("^{}$".format(short_name), name)
                    node.data.name = name
                return True
        return False

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
            if index.row() % 2 == 0:
                return QtGui.QColor(54, 54, 54)  # gray

    def parent(self, index):
        child_node = get_node_by_index(index, self._root_node)
        parent_node = child_node.parent
        if parent_node == self._root_node or parent_node is None:
            return QtCore.QModelIndex()
        return self.createIndex(parent_node.row(), 0, parent_node)

    def index(self, row, column, parent):
        if not self.hasIndex(row, column, parent):
            return QtCore.QModelIndex()

        parent_node = get_node_by_index(parent, self._root_node)
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

        self._tvComponent = zTreeView()
        self._tvComponent.setModel(tree_model)
        self._tvComponent.expandAll()
        self._tvComponent.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        lytSection = QtWidgets.QVBoxLayout()
        lytSection.addLayout(lytTitle)
        lytSection.addWidget(self._tvComponent)
        self.setLayout(lytSection)

        btnIcon.toggled.connect(self.on_btnIcon_toggled)
        self._tvComponent.selectionModel().selectionChanged.connect(
            self.on_tvComponent_selectionChanged)

    def on_btnIcon_toggled(self, checked):
        self._tvComponent.setVisible(checked)

    def on_tvComponent_selectionChanged(self, selected, deselected):
        """
        When the tree selection changes this gets executed to select
        corresponding item in Maya scene.
        """
        selection_list = self._tvComponent.selectedIndexes()
        if selection_list:
            nodes = [x.data(nodeRole).data for x in selection_list]
            node_names = [x.long_name for x in nodes]
            # find nodes that exist in the scene
            scene_nodes = cmds.ls(node_names, l=True)
            if scene_nodes:
                cmds.select(scene_nodes)

            not_found_nodes = [name for name in node_names if name not in scene_nodes]
            if not_found_nodes:
                cmds.warning(
                    "Nodes {} not found. Try to press refresh button.".format(not_found_nodes))


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

    def reset_model(self, builder, new_selection):
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
            root_node = TreeItem()
            has_data = False
            for node in node_list:
                child_nodes = build_scene_panel_tree(node, [component_type])
                if child_nodes:
                    zGeo_node = TreeItem(root_node, node)
                    zGeo_node.append_children(child_nodes)
                    has_data = True
            if has_data:
                self._component_tree_model_dict[component_type] = ComponentTreeModel(
                    builder, root_node)

        for component_type, tree_model in self._component_tree_model_dict.items():
            wgtSection = ComponentSectionWidget(component_type, tree_model)
            self._lytAllSections.addWidget(wgtSection)
