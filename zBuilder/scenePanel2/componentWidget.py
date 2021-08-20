import logging

from ..uiUtils import nodeRole, get_icon_path_from_name, get_icon_path_from_node, get_node_by_index
from .zTreeView import zTreeView
from .treeItem import TreeItem, build_scene_panel_tree
from PySide2 import QtCore, QtGui, QtWidgets
from maya import cmds, mel
from collections import defaultdict
from functools import partial
from zBuilder.nodes.base import Base

logger = logging.getLogger(__name__)

# Component for each zGeo node
component_type_dict = {
    "ui_zBone_body": ["zAttachment", "zBone", "zRivetToBone"],
    "ui_zTissue_body":
    ["zAttachment", "zTissue", "zTet", "zMaterial", "zFiber", "zLineOfAction", "zRestShape"],
    "ui_zCloth_body": ["zAttachment", "zCloth", "zMaterial"]
}

# clipboard for copied attributes
attrs_clipboard = {}
# clipboard for the maps.  This is either a zBuilder Map object or None.
maps_clipboard = None


def copy_attrs(node):
    # update the model in case maya updated
    node.get_maya_attrs()

    global attrs_clipboard
    attrs_clipboard = {}
    attrs_clipboard[node.type] = node.attrs.copy()


def paste_attrs(node):
    # type: (zBuilder.whatever.Base) -> None
    """
    Paste the attributes from the clipboard onto given node.
    @pre The node's type has an entry in the clipboard.
    """
    assert isinstance(node, Base), "Precondition violated: argument needs to be a zBuilder node of some type"
    assert node.type in attrs_clipboard, "Precondition violated: node type is not in the clipboard"
    orig_node_attrs = attrs_clipboard[node.type]
    assert isinstance(orig_node_attrs, dict), "Invariant violated: value in attrs clipboard must be a dict"

    # Here, we expect the keys to be the same on node.attrs and orig_node_attrs. We probably don't need to check, but we could:
    assert set(node.attrs) == set(orig_node_attrs), "Invariant violated: copied attribute list do not match paste-target's attribute list"
    node.attrs = orig_node_attrs.copy()  # Note: given the above invariant, this should be the same as node.attrs.update(orig_node_attrs)
    node.set_maya_attrs()


def invert_weights(node, map_index):
    map_ = node.parameters['map'][map_index]
    map_.invert()
    map_.apply_weights()


def copy_weights(node, map_index):
    global maps_clipboard
    maps_clipboard = node.parameters['map'][map_index]

def paste_weights(node, new_map_index):
    """
    Pasting the maps.  Terms used here
        orig/new.
        The map/node the items were copied from are prefixed with orig.
        The map/node the items are going to be pasted onto are prefixed with new

    """
    if maps_clipboard:
        orig_map = maps_clipboard
    else:
        return

    # It will be simple for a user to paste the wrong map in wrong location
    # here we are comparing the length of the maps and if they are different we can bring up
    # a dialog to warn user unexpected results may happen,
    new_map = node.parameters['map'][new_map_index]
    orig_map_length = len(orig_map.values)
    new_map_length = len(new_map.values)

    dialog_return = None
    if orig_map_length != new_map_length:
        msg_box = QtWidgets.QMessageBox()
        msg_box.setText(
            "The map you are copying from ({}) and pasting to ({}) have a different length.  Unexpected results may happen."
            .format(orig_map_length, new_map_length))
        msg_box.setInformativeText("Are you sure you want to continue?")
        msg_box.setStandardButtons(QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
        msg_box.setDefaultButton(QtWidgets.QMessageBox.No)
        dialog_return = msg_box.exec_()

    if dialog_return == QtWidgets.QMessageBox.Yes or orig_map_length == new_map_length:
        new_map.copy_values_from(orig_map)
        new_map.apply_weights()

class ProximityWidget(QtWidgets.QWidget):
    """
    Widget in right-click menu to change map weights for attachments
    """
    def __init__(self, parent=None):
        super(ProximityWidget, self).__init__(parent)
        h_layout = QtWidgets.QHBoxLayout(self)
        h_layout.setContentsMargins(15, 15, 15, 15)
        self.from_edit = MenuLineEdit()
        self.from_edit.setFixedHeight(24)
        self.from_edit.setPlaceholderText("From")
        self.from_edit.setText("0.1")
        self.from_edit.setFixedWidth(40)
        self.to_edit = MenuLineEdit()
        self.to_edit.setFixedHeight(24)
        self.to_edit.setPlaceholderText("To")
        self.to_edit.setText("0.2")
        self.to_edit.setFixedWidth(40)
        ok_button = QtWidgets.QPushButton()
        ok_button.setText("Ok")
        h_layout.addWidget(self.from_edit)
        h_layout.addWidget(self.to_edit)
        h_layout.addWidget(ok_button)
        ok_button.clicked.connect(self.paint_by_prox)
        # setTabOrder doesn't work when used for menu
        # need to use next 2 lines as a workaround
        self.setFocusProxy(self.to_edit)
        ok_button.setFocusProxy(self.from_edit)
        self.from_edit.acceptSignal.connect(self.paint_by_prox)
        self.to_edit.acceptSignal.connect(self.paint_by_prox)

    def paint_by_prox(self):
        """Paints attachment map by proximity.
        """
        # to_edit can't have smaller value then from_edit
        from_value = float(self.from_edit.text())
        to_value = float(self.to_edit.text())
        if to_value < from_value:
            self.to_edit.setText(str(from_value))
        mel.eval('zPaintAttachmentsByProximity -min {} -max {}'.format(
            self.from_edit.text(), self.to_edit.text()))

class MenuLineEdit(QtWidgets.QLineEdit):
    """
    Groups LineEdits together so after you press Tab it switch focus to sibling_right.
    If Shift+Tab pressed it uses sibling_left.
    Sends acceptSignal when Enter or Return button is pressed.
    This is for use in Menus, where tab navigation is broken out of the box,
    and the 'entered pressed' action undesirably causes the menu to close sometimes.
    """
    acceptSignal = QtCore.Signal()

    def __init__(self, parent=None):
        super(MenuLineEdit, self).__init__(parent)

    def event(self, event):
        if event.type() == QtCore.QEvent.KeyPress and event.key() == QtCore.Qt.Key_Tab:
            self.nextInFocusChain().setFocus()
            return True
        if event.type() == QtCore.QEvent.KeyPress and event.modifiers() == QtCore.Qt.ShiftModifier:
            # PySide bug, have to use this number instead of Key_Tab with modifiers
            if event.key() == 16777218:
                self.previousInFocusChain().setFocus()
                return True

        if event.type() == QtCore.QEvent.KeyPress and event.key() in [
                QtCore.Qt.Key_Enter, QtCore.Qt.Key_Return
        ]:
            self.acceptSignal.emit()
            # This will prevent menu to close after Enter/Return is pressed
            return True

        return super(MenuLineEdit, self).event(event)


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
        node = get_node_by_index(index, None)
        assert node, "Can't get node through QModelIndex."

        is_data_set = False
        if role == QtCore.Qt.EditRole:
            long_name = node.data.long_name
            short_name = node.data.name
            if value and value != short_name:
                name = cmds.rename(long_name, value)
                self._builder.string_replace("^{}$".format(short_name), name)
                node.data.name = name
                is_data_set = True

        if is_data_set:
            self.dataChanged.emit(index, index, role)
        return is_data_set

    def data(self, index, role):
        if not index.isValid():
            return None

        node = index.internalPointer()
        if role == QtCore.Qt.DisplayRole or role == QtCore.Qt.EditRole:
            # text
            return node.data.name
        if role == QtCore.Qt.DecorationRole:
            # icon
            if hasattr(node.data, "type"):
                parent_name = node.parent.data.name if node.parent.data else None
                return QtGui.QIcon(QtGui.QPixmap(get_icon_path_from_node(node.data, parent_name)))
        if role == nodeRole and hasattr(node.data, "type"):
            # attached node, such as zBuilder node
            return node.data
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
        self._tvComponent.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self._tvComponent.customContextMenuRequested.connect(self.open_menu)
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

        self._setup_actions()

    def open_menu(self, position):
        indexes = self._tvComponent.selectedIndexes()

        if len(indexes) != 1:
            return

        menu_dict = {
            'zTissue': self.open_tissue_menu, 
            'zBone': self.open_bone_menu,
            'zLineOfAction': self.open_line_of_action_menu,
            'zRestShape': self.open_rest_shape_menu,
            'zTet': self.open_tet_menu,
            'zFiber': self.open_fiber_menu,
            'zMaterial': self.open_material_menu,
            'zAttachment': self.open_attachment_menu,
            }

        node = indexes[0].data(nodeRole)
        if node.type in menu_dict:
            menu = QtWidgets.QMenu(self)
            method = menu_dict[node.type]
            method(menu, node)
            menu.exec_(self._tvComponent.viewport().mapToGlobal(position))

    def on_btnIcon_toggled(self, checked):
        self._tvComponent.setVisible(checked)

    def on_tvComponent_selectionChanged(self, selected, deselected):
        """
        When the tree selection changes this gets executed to select
        corresponding item in Maya scene.
        """
        selection_list = self._tvComponent.selectedIndexes()
        if selection_list:
            nodes = [x.data(nodeRole) for x in selection_list]
            node_names = [x.long_name for x in nodes]
            # find nodes that exist in the scene
            scene_nodes = cmds.ls(node_names, l=True)
            if scene_nodes:
                cmds.select(scene_nodes)

            not_found_nodes = [name for name in node_names if name not in scene_nodes]
            if not_found_nodes:
                cmds.warning(
                    "Nodes {} not found. Try to press refresh button.".format(not_found_nodes))

    def add_attribute_actions_to_menu(self, menu, node):
        attrs_menu = menu.addMenu('Attributes')

        copy_attrs_action = QtWidgets.QAction(self)
        copy_attrs_action.setText('Copy')
        copy_attrs_action.setObjectName("actionCopyAttrs")
        copy_attrs_action.triggered.connect(partial(copy_attrs, node))

        paste_attrs_action = QtWidgets.QAction(self)
        paste_attrs_action.setText('Paste')
        paste_attrs_action.setObjectName("actionPasteAttrs")
        paste_attrs_action.triggered.connect(partial(paste_attrs, node))

        # only enable 'paste' IF it is same type as what is in buffer
        paste_attrs_action.setEnabled(node.type in attrs_clipboard)

        attrs_menu.addAction(copy_attrs_action)
        attrs_menu.addAction(paste_attrs_action)

    def open_tissue_menu(self, menu, node):
        self.add_attribute_actions_to_menu(menu, node)

    def open_bone_menu(self, menu, node):
        self.add_attribute_actions_to_menu(menu, node)

    def open_line_of_action_menu(self, menu, node):
        self.add_attribute_actions_to_menu(menu, node)

    def open_rest_shape_menu(self, menu, node):
        self.add_attribute_actions_to_menu(menu, node)

    def add_map_actions_to_menu(self, menu, node, map_index):
        """
        Add map actions to the menu
        Args:
            menu (QMenu): menu to add option to
            node (zBuilder object): zBuilder.nodes object
            map_index (int): map index. 0 for source map 1 for target/endPoints map
        """
        paint_action = QtWidgets.QAction(self)
        paint_action.setText('Paint')
        paint_action.setObjectName("actionPaint")
        paint_action.triggered.connect(partial(node.parameters['map'][map_index].open_paint_tool))
        menu.addAction(paint_action)

        invert_action = QtWidgets.QAction(self)
        invert_action.setText('Invert')
        invert_action.setObjectName('actionInvertWeights')
        invert_action.triggered.connect(partial(invert_weights, node, map_index))
        menu.addAction(invert_action)

        menu.addSeparator()

        copy_action = QtWidgets.QAction(self)
        copy_action.setText('Copy')
        copy_action.setObjectName('actionCopyWeights')
        copy_action.triggered.connect(partial(copy_weights, node, map_index))
        menu.addAction(copy_action)

        paste_action = QtWidgets.QAction(self)
        paste_action.setText('Paste')
        paste_action.setObjectName('actionPasteWeights')
        paste_action.triggered.connect(partial(paste_weights, node, map_index))
        paste_action.setEnabled(bool(maps_clipboard))
        menu.addAction(paste_action)

    def open_tet_menu(self, menu, node):
        self.add_attribute_actions_to_menu(menu, node)
        menu.addSection('Maps')

        weight_map_menu = menu.addMenu('Weight')
        self.add_map_actions_to_menu(weight_map_menu, node, 0)

    def open_fiber_menu(self, menu, node):
        self.add_attribute_actions_to_menu(menu, node)
        menu.addSection('Maps')

        weight_map_menu = menu.addMenu('Weight')

        self.add_map_actions_to_menu(weight_map_menu, node, 0)

        end_points_map_menu = menu.addMenu('EndPoints')
        self.add_map_actions_to_menu(end_points_map_menu, node, 1)

    def open_material_menu(self, menu, node):
        self.add_attribute_actions_to_menu(menu, node)
        menu.addSection('Maps')
        weight_map_menu = menu.addMenu('Weight')

        self.add_map_actions_to_menu(weight_map_menu, node, 0)

    def select_source_and_target(self):
        """
        Selects the source and target mesh of an attachment. This is a menu command.
        """
        indexes = self._tvComponent.selectedIndexes()[0]
        node = indexes.data(nodeRole)
        cmds.select(node.nice_association)

    def _setup_actions(self):
        self.actionSelectST = QtWidgets.QAction(self)
        self.actionSelectST.setText('Select Source and Target')
        self.actionSelectST.setObjectName("actionSelectST")
        self.actionSelectST.triggered.connect(self.select_source_and_target)

    def open_attachment_menu(self, menu, node):
        source_mesh_name = node.association[0]
        target_mesh_name = node.association[1]

        self.add_attribute_actions_to_menu(menu, node)
        menu.addAction(self.actionSelectST)
        menu.addSection('Maps')
        truncate = lambda x: (x[:12] + '..') if len(x) > 14 else x
        source_menu_text = 'Source ({})'.format(truncate(source_mesh_name))
        target_menu_text = 'Target ({})'.format(truncate(target_mesh_name))

        source_map_menu = menu.addMenu(source_menu_text)
        self.add_map_actions_to_menu(source_map_menu, node, 0)

        target_map_menu = menu.addMenu(target_menu_text)
        self.add_map_actions_to_menu(target_map_menu, node, 1)

        menu.addSection('')
        proximity_menu = menu.addMenu('Paint By Proximity')
        prox_widget = ProximityWidget()
        action_paint_by_prox = QtWidgets.QWidgetAction(proximity_menu)
        action_paint_by_prox.setDefaultWidget(prox_widget)
        proximity_menu.addAction(action_paint_by_prox)


class ComponentWidget(QtWidgets.QWidget):
    """ The Component tree view widget.
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