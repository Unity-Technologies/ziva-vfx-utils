import weakref
from functools import partial

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

DIR_PATH = os.path.dirname(os.path.realpath(__file__)).replace("\\", "/")

# Show window with docking ability
def run():
    z = zva.Ziva()
    z.retrieve_connections()

    dock_window(MyDockingUI, root_node=z.root_node)


class MenuLineEdit(QtWidgets.QLineEdit):
    """
    Groups LineEdits together so after you press Tab it switch focus to sibling_right
    If Shift+Tab pressed it uses sibling_left
    Sends acceptSignal when Enter or Return button is pressed
    """
    acceptSignal = QtCore.Signal()

    def __init__(self, parent=None):
        super(MenuLineEdit, self).__init__(parent)
        self.sibling_right = None
        self.sibling_left = None

    def event(self, event):
        if event.type() == QtCore.QEvent.KeyPress and event.key() == QtCore.Qt.Key_Tab:
            if self.sibling_right:
                self.sibling_right.setFocus()
                return True
        if event.type() == QtCore.QEvent.KeyPress and event.modifiers() == QtCore.Qt.ShiftModifier:
            # PySide bug, have to use this number instead of Ket_Tab with modifiers
            if event.key() == 16777218:
                if self.sibling_left:
                    self.sibling_left.setFocus()
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
        self.from_edit.sibling_right = self.to_edit
        self.to_edit.sibling_right = self.from_edit
        self.from_edit.sibling_left = self.to_edit
        self.to_edit.sibling_left = self.from_edit
        ok_button = QtWidgets.QPushButton()
        ok_button.setText("Ok")
        h_layout.addWidget(self.from_edit)
        h_layout.addWidget(self.to_edit)
        h_layout.addWidget(ok_button)
        ok_button.clicked.connect(self.paint_by_prox)
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

    def __init__(self, parent=None, root_node=None):
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

        self._proxy_model = QtCore.QSortFilterProxyModel()
        self.root_node = root_node
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
        self.reset_tree(root_node=self.root_node)

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
        refresh_icon.addPixmap(QtGui.QPixmap(refresh_path),
                               QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.actionRefresh = QtWidgets.QAction(self)
        self.actionRefresh.setText('Refresh')
        self.actionRefresh.setIcon(refresh_icon)
        self.actionRefresh.setObjectName("actionRefresh")
        self.actionRefresh.triggered.connect(self.reset_tree)

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
        cmd = 'artSetToolAndSelectAttr( "artAttrCtx", "{}.{}.{}" );'.format(node.type,
                                                                            node.long_name,
                                                                            attribute)
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
        if len(indexes) == 1:
            node = indexes[0].data(model.SceneGraphModel.nodeRole)

            menu = QtWidgets.QMenu(self)

            source_mesh_name = node.long_association[0]
            if len(node.long_association) > 1:
                target_mesh_name = node.long_association[1]
            else:
                target_mesh_name = None
            menu_dict = {
                'zTet': [self.open_tet_menu, menu],
                'zFiber': [self.open_fiber_menu, menu],
                'zMaterial': [self.open_material_menu, menu],
                'zAttachment': [self.open_attachment_menu, menu, source_mesh_name,
                                target_mesh_name]
            }

            if node.type in menu_dict:
                method = menu_dict[node.type][0]
                args = menu_dict[node.type][1:]
                method(*args)

            menu.exec_(self.treeView.viewport().mapToGlobal(position))

    def add_placeholder_menu_item(self, menu):
        placeholder_widget = QtWidgets.QWidget()
        placeholder_action = QtWidgets.QWidgetAction(menu)
        placeholder_action.setDefaultWidget(placeholder_widget)
        menu.addAction(placeholder_action)

    def open_tet_menu(self, menu):
        self.add_placeholder_menu_item(menu)
        menu.addSection('Maps')
        weight_map_menu = menu.addMenu('Weight')
        weight_map_menu.addAction(self.actionPaintSource)

    def open_fiber_menu(self, menu):
        self.add_placeholder_menu_item(menu)
        menu.addSection('Maps')
        weight_map_menu = menu.addMenu('Weight')
        weight_map_menu.addAction(self.actionPaintSource)
        end_points_map_menu = menu.addMenu('EndPoints')
        end_points_map_menu.addAction(self.actionPaintEndPoints)

    def open_material_menu(self, menu):
        self.add_placeholder_menu_item(menu)
        menu.addSection('Maps')
        weight_map_menu = menu.addMenu('Weight')
        weight_map_menu.addAction(self.actionPaintSource)

    def open_attachment_menu(self, menu, source_mesh_name, target_mesh_name):
        menu.addAction(self.actionSelectST)
        menu.addSection('Maps')
        truncate = lambda x: (x[:12] + '..') if len(x) > 14 else x
        display_name = lambda x: truncate(x.split('|')[-1])
        source_menu_text = 'Source ({})'.format(display_name(source_mesh_name))
        target_menu_text = 'Target ({})'.format(display_name(target_mesh_name))
        source_map_menu = menu.addMenu(source_menu_text)
        source_map_menu.addAction(self.actionPaintSource)
        target_map_menu = menu.addMenu(target_menu_text)
        target_map_menu.addAction(self.actionPaintTarget)
        menu.addSection('')
        proximity_menu = menu.addMenu('Paint By Proximity')
        prox_widget = ProximityWidget()
        action_paint_by_prox = QtWidgets.QWidgetAction(proximity_menu)
        action_paint_by_prox.setDefaultWidget(prox_widget)
        proximity_menu.addAction(action_paint_by_prox)

    def tree_changed(self):
        """When the tree selection changes this gets executed to select
        corresponding item in Maya scene.
        """
        indexes = self.treeView.selectedIndexes()
        if indexes:
            nodes = [x.data(model.SceneGraphModel.nodeRole).long_name for x in indexes]
            mc.select(nodes)

    def reset_tree(self, root_node=None):
        """This builds and/or resets the tree given a root_node.  The root_node
        is a zBuilder object that the tree is built from.  If None is passed
        it uses the scene selection to build a new root_node.

        This forces a complete redraw of the ui tree.

        Args:
            root_node (:obj:`obj`, optional): The zBuilder root_node to build
                tree from.  Defaults to None.
        """

        if not root_node:
            z = zva.Ziva()
            z.retrieve_connections()
            root_node = z.root_node

        self._model.beginResetModel()
        self._model.root_node = root_node
        self._model.endResetModel()

        for row in range(self._proxy_model.rowCount()):
            index = self._proxy_model.index(row, 0)
            node = index.data(model.SceneGraphModel.nodeRole)
            if node.type == 'zSolverTransform':
                self.treeView.expand(index)

        sel = mc.ls(sl=True)
        # select item in treeview that is selected in maya to begin with and 
        # expand item in view.
        if sel:
            checked = self._proxy_model.match(self._proxy_model.index(0, 0),
                                              QtCore.Qt.DisplayRole,
                                              sel[0].split('|')[-1],
                                              -1,
                                              QtCore.Qt.MatchExactly | QtCore.Qt.MatchRecursive)
            for index in checked:
                self.treeView.selectionModel().select(index, QtCore.QItemSelectionModel.SelectCurrent)

            # this works for a zBuilder view.  This is expanding the item 
            # selected and it's parent if any.  This makes it possible if you 
            # have a material or attachment selected, it will become visible in
            # UI
            if checked:
                self.treeView.expand(checked[-1])
                self.treeView.expand(checked[-1].parent())

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
