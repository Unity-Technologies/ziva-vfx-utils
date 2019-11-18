import weakref
from functools import partial
import copy

import maya.cmds as mc
import maya.mel as mm
try:
    from shiboken2 import wrapInstance
except ImportError:
    raise StandardError("Ziva Scene Panel supported on Maya 2017+")

from PySide2 import QtGui, QtWidgets, QtCore
from zBuilder.ui.utils import dock_window

import model
import view
import icons
import os
import zBuilder.builders.ziva as zva
import zBuilder.parameters.maps as mp

DIR_PATH = os.path.dirname(os.path.realpath(__file__)).replace("\\", "/")


# Show window with docking ability
def run():
    builder = zva.Ziva()
    builder.retrieve_connections()

    dock_window(MyDockingUI, builder=builder)


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
        mm.eval('zPaintAttachmentsByProximity -min {} -max {}'.format(self.from_edit.text(),
                                                                      self.to_edit.text()))


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

        # clipboard for copied attributes
        self.attrs_clipboard = {}
        # clipboard for the maps.  This is a dictionary whose key is is the node that the map
        # was copied from and the value is the zBuilder 'map' object to help facilitate
        # getting and setting of the map.  We need to keep track of the original node
        # because we need a way to consistently do a string replace.  What goes in the buffer
        # should not be altered as that will affect multple pastes.
        self.maps_clipboard = {}

        root_node = builder.root_node

        self._proxy_model = QtCore.QSortFilterProxyModel()
        self._model = model.SceneGraphModel(root_node, self._proxy_model)
        self._proxy_model.setSourceModel(self._model)
        self._proxy_model.setDynamicSortFilter(True)
        self._proxy_model.setFilterCaseSensitivity(QtCore.Qt.CaseInsensitive)

        self.treeView = view.SceneTreeView(self)
        self.treeView.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.treeView.customContextMenuRequested.connect(self.open_menu)
        self.treeView.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        self.treeView.setModel(self._proxy_model)
        self.treeView.setIndentation(15)

        # must be after .setModel because assigning model resets item expansion
        self.set_root_node(root_node=root_node)

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
        refresh_path = icons.get_icon_path_from_name('refresh')
        refresh_icon = QtGui.QIcon()
        refresh_icon.addPixmap(QtGui.QPixmap(refresh_path), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.actionRefresh = QtWidgets.QAction(self)
        self.actionRefresh.setText('Refresh')
        self.actionRefresh.setIcon(refresh_icon)
        self.actionRefresh.setObjectName("actionRefresh")
        self.actionRefresh.triggered.connect(self.set_root_node)

        self.actionSelectST = QtWidgets.QAction(self)
        self.actionSelectST.setText('Select Source and Target')
        self.actionSelectST.setObjectName("actionSelectST")
        self.actionSelectST.triggered.connect(self.select_source_and_target)

        self.actionPaintSource = QtWidgets.QAction(self)
        self.actionPaintSource.setText('Paint')
        self.actionPaintSource.setObjectName("paintSource")
        self.actionPaintSource.triggered.connect(partial(self.paint_weights, 0, 'weights'))

        self.actionPaintTarget = QtWidgets.QAction(self)
        self.actionPaintTarget.setText('Paint')
        self.actionPaintTarget.setObjectName("paintTarget")
        self.actionPaintTarget.triggered.connect(partial(self.paint_weights, 1, 'weights'))

        self.actionPaintEndPoints = QtWidgets.QAction(self)
        self.actionPaintEndPoints.setText('Paint')
        self.actionPaintEndPoints.setObjectName("paintEndPoints")
        self.actionPaintEndPoints.triggered.connect(partial(self.paint_weights, 0, 'endPoints'))

        self.actionCopyAttrs = QtWidgets.QAction(self)
        self.actionCopyAttrs.setText('Copy')
        self.actionCopyAttrs.setObjectName("actionCopyAttrs")
        self.actionCopyAttrs.triggered.connect(self.copy_attrs)

        self.actionPasteAttrs = QtWidgets.QAction(self)
        self.actionPasteAttrs.setText('Paste')
        self.actionPasteAttrs.setObjectName("actionPasteAttrs")
        self.actionPasteAttrs.triggered.connect(self.paste_attrs)
        self.actionPasteAttrs.setEnabled(False)

    def invert_weights(self, weight_map):

        weight_map.invert()
        weight_map.apply_weights()

    def copy_weights(self, weight_map):

        indexes = self.treeView.selectedIndexes()
        node = indexes[-1].data(model.SceneGraphModel.nodeRole)
        self.maps_clipboard = {}
        self.maps_clipboard[node.name] = weight_map

    def paste_weights(self, weight_map):
        if self.maps_clipboard:
            copied_weight_map = self.maps_clipboard.values()[0]
        else:
            return

        index = self.treeView.selectedIndexes()[0]
        node = index.data(model.SceneGraphModel.nodeRole)

        # It will be simple for a user to paste the wrong map in worng location
        # here we are comparing the length of the maps and if they are different we can bring up
        # a dialog to warn user unexpected results may happen,
        new_map_length = len(weight_map.values)
        original_map_length = len(copied_weight_map.values)

        dialog_return = None
        if new_map_length != original_map_length:
            msgBox = QtWidgets.QMessageBox()
            msgBox.setText(
                "The map you are copying from ({}) and pasting to ({}) have a different length.  Unexpected results may happen."
                .format(original_map_length, new_map_length))
            msgBox.setInformativeText("Are you sure you want to continue?")
            msgBox.setStandardButtons(QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
            msgBox.setDefaultButton(QtWidgets.QMessageBox.No)
            dialog_return = msgBox.exec_()

        if dialog_return == QtWidgets.QMessageBox.Yes or new_map_length == original_map_length:

            # check if node type of map is same as what we are tryiong to paste to
            if node.type == weight_map.map_type:
                source_node_name = self.maps_clipboard.keys()[0]
                target_node_name = node.name

                # Need to make a deep copy of the map.  This is so if it is pasted
                # on multiple items we need the string_replace to work on original name.  We do not
                # want anything to change data in buffer
                weight_map_copy = copy.deepcopy(weight_map)
                weight_map_copy.string_replace(source_node_name, target_node_name)
                weight_map_copy.apply_weights()

    def paste_attrs(self):
        indexes = self.treeView.selectedIndexes()
        for index in indexes:
            node = index.data(model.SceneGraphModel.nodeRole)
            for attr, entry in self.attrs_clipboard.get(node.type, {}).iteritems():
                mc.setAttr("{}.{}".format(node.name, attr), lock=False)
                mc.setAttr("{}.{}".format(node.name, attr), entry['value'], lock=entry['locked'])

    def copy_attrs(self):
        self.attrs_clipboard = {}
        indexes = self.treeView.selectedIndexes()
        node = indexes[-1].data(model.SceneGraphModel.nodeRole)
        self.attrs_clipboard[node.type] = node.attrs.copy()
        # enable paste button
        self.actionPasteAttrs.setEnabled(True)

    def paint_weights(self, association_idx, attribute):
        """Paint weights menu command.

        This is checking item selected in treeView to get zBuilder node.

        Args:
            association_idx (int): The index of mesh to use in node association
            attribute (string): The name of the attribute to paint.
        """
        # sourcing the mel command so we have access to it
        mm.eval('source "artAttrCreateMenuItems"')

        indexes = self.treeView.selectedIndexes()[0]
        node = indexes.data(model.SceneGraphModel.nodeRole)
        mesh = node.long_association[association_idx]
        mc.select(mesh, r=True)
        cmd = 'artSetToolAndSelectAttr( "artAttrCtx", "{}.{}.{}" );'.format(
            node.type, node.long_name, attribute)
        mm.eval(cmd)

    def select_source_and_target(self):
        """Selects the source and target mesh of an attachment. This is a menu 
        command.
        """

        indexes = self.treeView.selectedIndexes()[0]
        node = indexes.data(model.SceneGraphModel.nodeRole)
        mc.select(node.long_association)

    def open_menu(self, position):
        """Generates menu for tree items

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
            'zRestShape': self.open_rest_shape_menu
        }

        node = indexes[0].data(model.SceneGraphModel.nodeRole)
        if node.type in menu_dict:
            menu = QtWidgets.QMenu(self)
            method = menu_dict[node.type]
            method(menu, node)
            menu.exec_(self.treeView.viewport().mapToGlobal(position))

    # TODO: Implement this functionality in zBuilder core
    def get_maps_from_node(self, node):
        maps = []
        # get node parameters
        param_dict = node.spawn_parameters()
        param_dict.pop('mesh', None)
        for key, values in param_dict.iteritems():
            for value in values:
                obj = self.builder.parameter_factory(key, value)
                maps.append(obj)
        return maps

    def add_invert_action_to_menu(self, menu, weight_map):
        action_invert_weight_map = QtWidgets.QAction(self)
        action_invert_weight_map.setText('Invert')
        action_invert_weight_map.setObjectName("actionInvertWeights")
        action_invert_weight_map.triggered.connect(partial(self.invert_weights, weight_map))
        menu.addAction(action_invert_weight_map)

    def add_copy_action_to_menu(self, menu, weight_map):
        action = QtWidgets.QAction(self)
        action.setText('Copy')
        action.setObjectName("actionCopyWeights")
        action.triggered.connect(partial(self.copy_weights, weight_map))
        menu.addAction(action)

    def add_paste_action_to_menu(self, menu, weight_map):

        action = QtWidgets.QAction(self)
        action.setText('Paste')
        action.setObjectName("actionPasteWeights")
        action.triggered.connect(partial(self.paste_weights, weight_map))
        if not self.maps_clipboard:
            action.setEnabled(False)
        menu.addAction(action)

    def add_attributes_menu(self, menu):
        attrs_menu = menu.addMenu('Attributes')
        attrs_menu.addAction(self.actionCopyAttrs)

        attrs_menu.addAction(self.actionPasteAttrs)

    def open_tet_menu(self, menu, node):
        self.add_attributes_menu(menu)
        menu.addSection('Maps')
        weight_map_menu = menu.addMenu('Weight')
        weight_map_menu.addAction(self.actionPaintSource)
        weight_map = self.get_maps_from_node(node)[0]
        self.add_invert_action_to_menu(weight_map_menu, weight_map)

        weight_map_menu.addSeparator()
        self.add_copy_action_to_menu(weight_map_menu, weight_map)
        self.add_paste_action_to_menu(weight_map_menu, weight_map)

    def open_fiber_menu(self, menu, node):
        self.add_attributes_menu(menu)
        menu.addSection('Maps')
        weight_map_menu = menu.addMenu('Weight')
        weight_map_menu.addAction(self.actionPaintSource)

        maps = self.get_maps_from_node(node)
        weight_map = maps[0]
        end_points_map = maps[1]

        self.add_invert_action_to_menu(weight_map_menu, weight_map)
        weight_map_menu.addSeparator()
        self.add_copy_action_to_menu(weight_map_menu, weight_map)
        self.add_paste_action_to_menu(weight_map_menu, weight_map)

        end_points_map_menu = menu.addMenu('EndPoints')
        end_points_map_menu.addAction(self.actionPaintEndPoints)
        self.add_invert_action_to_menu(end_points_map_menu, end_points_map)
        end_points_map_menu.addSeparator()
        self.add_copy_action_to_menu(end_points_map_menu, end_points_map)
        self.add_paste_action_to_menu(end_points_map_menu, weight_map)

    def open_material_menu(self, menu, node):
        self.add_attributes_menu(menu)
        menu.addSection('Maps')
        weight_map_menu = menu.addMenu('Weight')
        weight_map_menu.addAction(self.actionPaintSource)
        weight_map = self.get_maps_from_node(node)[0]
        self.add_invert_action_to_menu(weight_map_menu, weight_map)
        weight_map_menu.addSeparator()
        self.add_copy_action_to_menu(weight_map_menu, weight_map)
        self.add_paste_action_to_menu(weight_map_menu, weight_map)

    def open_attachment_menu(self, menu, node):
        source_mesh_name = node.long_association[0]
        target_mesh_name = node.long_association[1]
        maps = self.get_maps_from_node(node)
        source_map = maps[0]
        target_map = maps[1]

        self.add_attributes_menu(menu)
        menu.addAction(self.actionSelectST)
        menu.addSection('Maps')
        truncate = lambda x: (x[:12] + '..') if len(x) > 14 else x
        display_name = lambda x: truncate(x.split('|')[-1])
        source_menu_text = 'Source ({})'.format(display_name(source_mesh_name))
        target_menu_text = 'Target ({})'.format(display_name(target_mesh_name))

        source_map_menu = menu.addMenu(source_menu_text)
        source_map_menu.addAction(self.actionPaintSource)
        self.add_invert_action_to_menu(source_map_menu, source_map)
        source_map_menu.addSeparator()
        self.add_copy_action_to_menu(source_map_menu, source_map)
        self.add_paste_action_to_menu(source_map_menu, source_map)

        target_map_menu = menu.addMenu(target_menu_text)
        target_map_menu.addAction(self.actionPaintTarget)
        self.add_invert_action_to_menu(target_map_menu, target_map)
        target_map_menu.addSeparator()
        self.add_copy_action_to_menu(target_map_menu, target_map)
        self.add_paste_action_to_menu(target_map_menu, target_map)

        menu.addSection('')
        proximity_menu = menu.addMenu('Paint By Proximity')
        prox_widget = ProximityWidget()
        action_paint_by_prox = QtWidgets.QWidgetAction(proximity_menu)
        action_paint_by_prox.setDefaultWidget(prox_widget)
        proximity_menu.addAction(action_paint_by_prox)

    def open_tissue_menu(self, menu, _):
        self.add_attributes_menu(menu)

    def open_bone_menu(self, menu, _):
        self.add_attributes_menu(menu)

    def open_line_of_action_menu(self, menu, _):
        self.add_attributes_menu(menu)

    def open_rest_shape_menu(self, menu, _):
        self.add_attributes_menu(menu)

    def tree_changed(self):
        """When the tree selection changes this gets executed to select
        corresponding item in Maya scene.
        """
        indexes = self.treeView.selectedIndexes()
        if indexes:
            nodes = [x.data(model.SceneGraphModel.nodeRole).long_name for x in indexes]
            mc.select(nodes)

    def set_root_node(self, root_node=None):
        """This builds and/or resets the tree given a root_node.  The root_node
        is a zBuilder object that the tree is built from.  If None is passed
        it uses the scene selection to build a new root_node.

        This forces a complete redraw of the ui tree.

        Args:
            root_node (:obj:`obj`, optional): The zBuilder root_node to build
                tree from.  Defaults to None.
        """

        if not root_node:
            # clean builder
            # TODO: this line should be changed after VFXACT-388 to make more efficient
            self.builder = zva.Ziva()
            self.builder.retrieve_connections()
            root_node = self.builder.root_node

        # remember names of items to expand
        names_to_expand = self.get_expanded()

        self._model.beginResetModel()
        self._model.root_node = root_node
        self._model.endResetModel()

        # restore previous expansion in treeView or expand all zSolverTransform items
        if names_to_expand:
            self.expand(names_to_expand)
        else:
            indexes = self._proxy_model.match(self._proxy_model.index(0, 0),
                                              model.SceneGraphModel.sortRole, "zSolverTransform",
                                              -1, QtCore.Qt.MatchExactly | QtCore.Qt.MatchRecursive)
            for index in indexes:
                self.treeView.expand(index)

        sel = mc.ls(sl=True, long=True)
        # select item in treeview that is selected in maya to begin with and
        # expand item in view.
        if sel:
            checked = self._proxy_model.match(self._proxy_model.index(0, 0),
                                              model.SceneGraphModel.longNameRole, sel[0], -1,
                                              QtCore.Qt.MatchExactly | QtCore.Qt.MatchRecursive)
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
                expanded.append(index.data(model.SceneGraphModel.longNameRole))

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
            indexes = self._proxy_model.match(self._proxy_model.index(0, 0),
                                              model.SceneGraphModel.longNameRole, name, -1,
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

    def run(self):
        return self
