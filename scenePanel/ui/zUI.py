import os
import weakref
import zBuilder.builders.ziva as zva

from functools import partial
from PySide2 import QtGui, QtWidgets, QtCore
from maya import cmds
from zBuilder.nodes.base import Base
from .model import SceneGraphModel, TreeItemDelegate
from .view import SceneTreeView
from ..uiUtils import (ProximityWidget, dock_window, get_icon_path_from_name, sortRole, nodeRole,
                       longNameRole)

DIR_PATH = os.path.dirname(os.path.realpath(__file__)).replace("\\", "/")


# Show window with docking ability
def run():
    builder = zva.Ziva()

    return dock_window(MyDockingUI, builder=builder)


class MyDockingUI(QtWidgets.QWidget):
    instances = list()
    CONTROL_NAME = 'zivaScenePanel'
    DOCK_LABEL_NAME = 'Ziva Scene Panel'

    def __init__(self, parent=None, builder=None):
        super(MyDockingUI, self).__init__(parent)

        self.__copy_buffer = None
        # let's keep track of our docks so we only have one at a time.
        MyDockingUI.delete_instances()
        self.__class__.instances.append(weakref.proxy(self))

        self.window_name = self.CONTROL_NAME
        self.ui = parent
        self.ui.setStyleSheet(open(os.path.join(DIR_PATH, "style.css"), "r").read())
        self.main_layout = parent.layout()
        self.main_layout.setContentsMargins(2, 2, 2, 2)
        self.builder = builder or zva.Ziva()
        self.builder.retrieve_connections()

        # clipboard for copied attributes
        self.attrs_clipboard = {}
        # clipboard for the maps.  This is either a zBuilder Map object or None.
        self.maps_clipboard = None

        self._proxy_model = QtCore.QSortFilterProxyModel()
        self._model = SceneGraphModel(self.builder, self._proxy_model)
        self._proxy_model.setSourceModel(self._model)
        self._proxy_model.setDynamicSortFilter(True)
        self._proxy_model.setFilterCaseSensitivity(QtCore.Qt.CaseInsensitive)

        self.treeView = SceneTreeView(self)
        self.treeView.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.treeView.customContextMenuRequested.connect(self.open_menu)
        self.treeView.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        self.treeView.setModel(self._proxy_model)
        self.treeView.setItemDelegate(TreeItemDelegate())
        self.treeView.setIndentation(15)

        # must be after .setModel because assigning model resets item expansion
        self.set_builder(self.builder)

        # changing header size
        # this used to create some space between left/top side of the tree view and it items
        # "razzle dazzle" but the only way I could handle that
        # height - defines padding from top
        # offset - defines padding from left
        # opposite value of offset should be applied in view.py in drawBranches method
        header = self.treeView.header()
        header.setOffset(-self.treeView.offset)
        header.setFixedHeight(10)

        self.tool_bar = QtWidgets.QToolBar(self)
        self.tool_bar.setIconSize(QtCore.QSize(27, 27))
        self.tool_bar.setObjectName("toolBar")

        self.top_layout = QtWidgets.QHBoxLayout()
        self.top_layout.addWidget(self.tool_bar)
        self.top_layout.setContentsMargins(15, 0, 0, 0)
        self.main_layout.addLayout(self.top_layout)
        self.main_layout.addWidget(self.treeView)

        self.treeView.selectionModel().selectionChanged.connect(self.tree_changed)

        self._setup_actions()

        self.tool_bar.addAction(self.actionRefresh)

    def _setup_actions(self):
        refresh_path = get_icon_path_from_name('refresh')
        refresh_icon = QtGui.QIcon()
        refresh_icon.addPixmap(QtGui.QPixmap(refresh_path), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.actionRefresh = QtWidgets.QAction(self)
        self.actionRefresh.setText('Refresh')
        self.actionRefresh.setIcon(refresh_icon)
        self.actionRefresh.setObjectName("actionRefresh")
        self.actionRefresh.triggered.connect(self.set_builder)

        self.actionSelectST = QtWidgets.QAction(self)
        self.actionSelectST.setText('Select Source and Target')
        self.actionSelectST.setObjectName("actionSelectST")
        self.actionSelectST.triggered.connect(self.select_source_and_target)

    def invert_weights(self, node, map_index):
        node.parameters['map'][map_index].retrieve_values()
        map_ = node.parameters['map'][map_index]
        map_.invert()
        map_.apply_weights()

    def copy_weights(self, node, map_index):
        node.parameters['map'][map_index].retrieve_values()
        self.maps_clipboard = node.parameters['map'][map_index]

    def paste_weights(self, node, new_map_index):
        node.parameters['map'][new_map_index].retrieve_values()
        new_map = node.parameters['map'][new_map_index]
        """
        Pasting the maps.  Terms used here
            orig/new.
            The map/node the items were copied from are prefixed with orig.
            The map/node the items are going to be pasted onto are prefixed with new

        """
        if self.maps_clipboard:
            orig_map = self.maps_clipboard
        else:
            return

        # It will be simple for a user to paste the wrong map in wrong location
        # here we are comparing the length of the maps and if they are different we can bring up
        # a dialog to warn user unexpected results may happen,
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

    def paste_attrs(self, node):
        # type: (zBuilder.whatever.Base) -> None
        """
        Paste the attributes from the clipboard onto given node.
        @pre The node's type has an entry in the clipboard.
        """
        assert isinstance(
            node, Base), "Precondition violated: argument needs to be a zBuilder node of some type"
        assert node.type in self.attrs_clipboard, "Precondition violated: node type is not in the clipboard"
        orig_node_attrs = self.attrs_clipboard[node.type]
        assert isinstance(orig_node_attrs,
                          dict), "Invariant violated: value in attrs clipboard must be a dict"

        # Here, we expect the keys to be the same on node.attrs and orig_node_attrs. We probably don't need to check, but we could:
        assert set(node.attrs) == set(
            orig_node_attrs
        ), "Invariant violated: copied attribute list do not match paste-target's attribute list"
        node.attrs = orig_node_attrs.copy(
        )  # Note: given the above invariant, this should be the same as node.attrs.update(orig_node_attrs)
        node.set_maya_attrs()

    def copy_attrs(self, node):
        # update the model in case maya updated
        node.get_maya_attrs()

        self.attrs_clipboard = {}
        self.attrs_clipboard[node.type] = node.attrs.copy()

    def select_source_and_target(self):
        """
        Selects the source and target mesh of an attachment. This is a menu command.
        """

        indexes = self.treeView.selectedIndexes()[0]
        node = indexes.data(nodeRole)
        cmds.select(node.nice_association)

    def open_menu(self, position):
        """
        Generates menu for tree items

        We are getting the zBuilder node in the tree item and checking type.
        With that we can build a custom menu per type.  If there are more then
        one object selected in UI a menu does not appear as items in menu work
        on a single selection.
        """
        indexes = self.treeView.selectedIndexes()

        if len(indexes) != 1:
            return

        menu_dict = {
            'zTet': self.open_tet_menu,
            'zFiber': self.open_fiber_menu,
            'zMaterial': self.open_material_menu,
            'zAttachment': self.open_attachment_menu,
            'zTissue': self.open_tissue_menu,
            'zBone': self.open_bone_menu,
            'zLineOfAction': self.open_line_of_action_menu,
            'zRestShape': self.open_rest_shape_menu,
            'zSolverTransform': self.open_solver_menu
        }

        node = indexes[0].data(nodeRole)
        if node.type in menu_dict:
            menu = QtWidgets.QMenu(self)
            method = menu_dict[node.type]
            method(menu, node)
            menu.exec_(self.treeView.viewport().mapToGlobal(position))

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
        invert_action.triggered.connect(partial(self.invert_weights, node, map_index))
        menu.addAction(invert_action)

        menu.addSeparator()

        copy_action = QtWidgets.QAction(self)
        copy_action.setText('Copy')
        copy_action.setObjectName('actionCopyWeights')
        copy_action.triggered.connect(partial(self.copy_weights, node, map_index))
        menu.addAction(copy_action)

        paste_action = QtWidgets.QAction(self)
        paste_action.setText('Paste')
        paste_action.setObjectName('actionPasteWeights')
        paste_action.triggered.connect(partial(self.paste_weights, node, map_index))
        paste_action.setEnabled(bool(self.maps_clipboard))
        menu.addAction(paste_action)

    def add_attribute_actions_to_menu(self, menu, node):
        attrs_menu = menu.addMenu('Attributes')

        copy_attrs_action = QtWidgets.QAction(self)
        copy_attrs_action.setText('Copy')
        copy_attrs_action.setObjectName("actionCopyAttrs")
        copy_attrs_action.triggered.connect(partial(self.copy_attrs, node))

        paste_attrs_action = QtWidgets.QAction(self)
        paste_attrs_action.setText('Paste')
        paste_attrs_action.setObjectName("actionPasteAttrs")
        paste_attrs_action.triggered.connect(partial(self.paste_attrs, node))

        # only enable 'paste' IF it is same type as what is in buffer
        paste_attrs_action.setEnabled(node.type in self.attrs_clipboard)

        attrs_menu.addAction(copy_attrs_action)
        attrs_menu.addAction(paste_attrs_action)

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

    def open_tissue_menu(self, menu, node):
        self.add_attribute_actions_to_menu(menu, node)

    def open_bone_menu(self, menu, node):
        self.add_attribute_actions_to_menu(menu, node)

    def open_line_of_action_menu(self, menu, node):
        self.add_attribute_actions_to_menu(menu, node)

    def open_rest_shape_menu(self, menu, node):
        self.add_attribute_actions_to_menu(menu, node)

    def open_solver_menu(self, menu, node):
        solver_transform = node
        solver = node.children[0]

        self.add_zsolver_menu_action(menu, solver_transform, 'Enable', 'enable')
        self.add_zsolver_menu_action(menu, solver, 'Collision Detection', 'collisionDetection')
        self.add_zsolver_menu_action(menu, solver, 'Show Bones', 'showBones')
        self.add_zsolver_menu_action(menu, solver, 'Show Tet Meshes', 'showTetMeshes')
        self.add_zsolver_menu_action(menu, solver, 'Show Muscle Fibers', 'showMuscleFibers')
        self.add_zsolver_menu_action(menu, solver, 'Show Attachments', 'showAttachments')
        self.add_zsolver_menu_action(menu, solver, 'Show Collisions', 'showCollisions')
        self.add_zsolver_menu_action(menu, solver, 'Show Materials', 'showMaterials')

    def add_zsolver_menu_action(self, menu, node, text, attr):
        action = QtWidgets.QAction(self)
        action.setText(text)
        action.setCheckable(True)
        action.setChecked(node.attrs[attr]['value'])
        action.changed.connect(partial(self.toggle_attribute, node, attr))
        menu.addAction(action)

    def toggle_attribute(self, node, attr):
        value = node.attrs[attr]['value']
        if isinstance(value, bool):
            value = not value
        elif isinstance(value, int):
            value = 1 - value
        else:
            cmds.error("Attribute is not bool/int: {}.{}".format(node.name, attr))
            return
        node.attrs[attr]['value'] = value
        cmds.setAttr('{}.{}'.format(node.long_name, attr), value)

    def tree_changed(self, selected, deselected):
        """
        When the tree selection changes this gets executed to select
        corresponding item in Maya scene.
        """
        selectedIndexList = selected.indexes()
        if selectedIndexList:
            nodes = [x.data(nodeRole).long_name for x in selectedIndexList]
            # find nodes that exist in the scene
            scene_nodes = cmds.ls(nodes, l=True)
            if scene_nodes:
                cmds.select(scene_nodes)
            not_found_nodes = [node for node in nodes if node not in scene_nodes]
            if not_found_nodes:
                cmds.warning(
                    "Nodes {} not found. Try to press refresh button.".format(not_found_nodes))

    def set_builder(self, builder=None):
        """
        This builds and/or resets the tree given a builder.  The builder
        is a zBuilder object that the tree is built from.  If None is passed
        it uses the scene selection to build a new builder.

        This forces a complete redraw of the ui tree.

        Args:
            builder (:obj:`obj`, optional): The zBuilder builder to build
                tree from.  Defaults to None.
        """

        if not builder:
            # reset builder
            self.builder = zva.Ziva()
            self.builder.retrieve_connections()
            builder = self.builder

        # remember names of items to expand
        names_to_expand = self.get_expanded()

        self._model.beginResetModel()
        self._model.builder = builder
        self._model.endResetModel()

        # restore previous expansion in treeView or expand all zSolverTransform items
        if names_to_expand:
            self.expand(names_to_expand)
        else:
            indexes = self._proxy_model.match(self._proxy_model.index(0, 0), sortRole,
                                              "zSolverTransform", -1,
                                              QtCore.Qt.MatchExactly | QtCore.Qt.MatchRecursive)
            for index in indexes:
                self.treeView.expand(index)

        sel = cmds.ls(sl=True, long=True)
        # select item in treeview that is selected in maya to begin with and
        # expand item in view.
        if sel:
            checked = self._proxy_model.match(self._proxy_model.index(0, 0), longNameRole, sel[0],
                                              -1, QtCore.Qt.MatchExactly | QtCore.Qt.MatchRecursive)
            for index in checked:
                self.treeView.selectionModel().select(index, QtCore.QItemSelectionModel.Select)

            # this works for a zBuilder view.  This is expanding the item
            # selected and it's parent if any.  This makes it possible if you
            # have a material or attachment selected, it will become visible in
            # UI
            if checked:
                self.treeView.expand(checked[-1])
                self.treeView.expand(checked[-1].parent())

    def get_expanded(self):
        """
        Returns: array of item names that are currently expanded in treeView
        """
        # store currently expanded items
        expanded = []
        for index in self._proxy_model.persistentIndexList():
            if self.treeView.isExpanded(index):
                expanded.append(index.data(longNameRole))

        return expanded

    def expand(self, names):
        """
        Args:
            names (list): names to expand in treeView
        """
        # collapseAll added in case refreshing of treeView needed
        # otherwise new items might not be displayed ( Qt bug )
        self.treeView.collapseAll()
        for name in names:
            indexes = self._proxy_model.match(self._proxy_model.index(0, 0), longNameRole, name, -1,
                                              QtCore.Qt.MatchExactly | QtCore.Qt.MatchRecursive)
            for index in indexes:
                self.treeView.expand(index)

    @staticmethod
    def delete_instances():
        for ins in MyDockingUI.instances:
            try:
                ins.setParent(None)
                ins.deleteLater()
            except:
                # ignore the fact that the actual parent has already been
                # deleted by Maya...
                pass

            MyDockingUI.instances.remove(ins)
            del ins
