import weakref
from functools import partial

import maya.cmds as mc
import maya.mel as mm
import maya.OpenMaya as om

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
import zBuilder.zMaya as mz
import zBuilder.parameters.maps as mp

dir_path = os.path.dirname(os.path.realpath(__file__)).replace("\\", "/")
os.chdir(dir_path)


def run():
    builder = zva.Ziva()
    builder.retrieve_connections()

    dock_window(MyDockingUI, builder=builder)


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
        self.ui.setStyleSheet(open(os.path.join(dir_path, "style.css"), "r").read())
        self.main_layout = parent.layout()
        self.main_layout.setContentsMargins(2, 2, 2, 2)
        self.builder = builder
        # clipboard for copied weightmaps
        self.weights_clipboard = []

        root_node = None

        if builder:
            root_node = builder.root_node

        self.treeView = view.SceneTreeView(self)
        self.treeView.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.treeView.customContextMenuRequested.connect(self.open_menu)
        self.treeView.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)

        self._proxy_model = model.SceneSortFilterProxyModel(self.treeView)
        self._model = model.SceneGraphModel(root_node, self._proxy_model)
        self._proxy_model.setSourceModel(self._model)
        self._proxy_model.setDynamicSortFilter(True)
        self._proxy_model.setFilterCaseSensitivity(QtCore.Qt.CaseInsensitive)

        self.treeView.setModel(self._proxy_model)
        self.delegate = model.TreeItemDelegate()
        self.treeView.setItemDelegate(self.delegate)
        self.treeView.setIndentation(15)

        # changing header size
        # this used to create some space between left/top side of the tree view and it items
        # "razzle dazzle" but the only way I could handle that
        # height - defines padding from top
        # offset - defines padding from left
        # opposite value of offset should be applied in view.py in drawBranches method
        height = 10
        offset = -20
        header = self.treeView.header()
        header.setOffset(offset)
        header.setFixedHeight(height)

        self.callback_ids = {}

        self.reset_tree(root_node=root_node)

        self.tool_bar = QtWidgets.QToolBar(self)
        self.tool_bar.setIconSize(QtCore.QSize(27, 27))
        self.tool_bar.setObjectName("toolBar")
        self.setFixedHeight(27)
        self.setFixedWidth(27)

        self.top_layout = QtWidgets.QHBoxLayout()
        self.top_layout.addWidget(self.tool_bar)
        self.top_layout.setContentsMargins(15, 0, 0, 0)
        self.main_layout.addLayout(self.top_layout)
        self.main_layout.addWidget(self.treeView)

        # The next two selection signals ( eventCallback and selectionModel ) will cause a loop if
        # you making selection by code, to prevent that make sure to break the loop by using variable
        # self.is_selection_callback_active = False
        event_id = om.MEventMessage.addEventCallback("SelectionChanged", self.selection_callback)
        self.callback_ids["SelectionCallback"] = [event_id]
        self.destroyed.connect(lambda: self.unregister_callbacks())
        self.is_selection_callback_active = True

        self.treeView.selectionModel().selectionChanged.connect(self.tree_changed)

        self._setup_actions()

        self.tool_bar.addAction(self.actionRefresh)

    def unregister_callbacks(self, callback_names=None):
        if callback_names:
            for callback in callback_names:
                if callback in self.callback_ids:
                    for id_ in self.callback_ids[callback]:
                        om.MMessage.removeCallback(id_)
        else:
            for ids in self.callback_ids.values():
                for id_ in ids:
                    om.MMessage.removeCallback(id_)

    def _setup_actions(self):
        refresh_path = icons.get_icon_path_from_name('refresh')
        refresh_icon = QtGui.QIcon()
        refresh_icon.addPixmap(QtGui.QPixmap(refresh_path), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.actionRefresh = QtWidgets.QAction(self)
        self.actionRefresh.setText('Refresh')
        self.actionRefresh.setIcon(refresh_icon)
        self.actionRefresh.setObjectName("actionUndo")
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

    def paint_by_prox(self, minimum, maximum):
        """Paints attachment map by proximity.
        
        Args:
            minimum ([float]): minimum
            maximum ([float]): maximum
        """
        indexes = self.treeView.selectedIndexes()[0]
        node = indexes.data(model.SceneGraphModel.nodeRole)
        mc.select(node.name, r=True)
        mm.eval('zPaintAttachmentsByProximity -min {} -max {}'.format(str(minimum), str(maximum)))

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

    def add_placeholder_action(self, menu):
        """Adds an empty action to the menu
        To be able to add separator at the very top of menu
        """
        empty_widget = QtWidgets.QWidget()
        empty_action = QtWidgets.QWidgetAction(menu)
        empty_action.setDefaultWidget(empty_widget)
        menu.addAction(empty_action)

    def open_menu(self, position):
        """Generates menu for tree items

        We are getting the zBuilder node in the tree item and checking type.
        With that we can build a custom menu per type.  If there are more then 
        one object selected in UI a menu does not appear as items in menu work
        on a single selection.
        """
        indexes = self.treeView.selectedIndexes()
        if not indexes:
            return

        node = indexes[0].data(model.SceneGraphModel.nodeRole)

        menu = QtWidgets.QMenu(self)

        source_mesh_name = node.association[0]
        if len(node.association) > 1:
            target_mesh_name = node.association[1]
        else:
            target_mesh_name = None
        menu_dict = {
            'zTet': [self.open_tet_menu, menu, source_mesh_name],
            'zFiber': [self.open_fiber_menu, menu, source_mesh_name],
            'zMaterial': [self.open_tet_menu, menu, source_mesh_name],
            'zAttachment': [self.open_attachment_menu, menu, source_mesh_name, target_mesh_name]
        }

        if node.type in menu_dict:
            method = menu_dict[node.type][0]
            args = []
            for arg in menu_dict[node.type]:
                if arg != method:
                    args.append(arg)
            method(*args)

        menu.exec_(self.treeView.viewport().mapToGlobal(position))

    def add_copy_paste_invert_to_menu(self, menu, map_name_format_string, mesh_name):
        menu.addSection('')
        action_copy_weight = QtWidgets.QAction(self)
        action_copy_weight.setText('Copy')
        action_copy_weight.setObjectName("actionCopyWeight")
        action_copy_weight.triggered.connect(
            partial(self.copy_weight, map_name_format_string, mesh_name))
        menu.addAction(action_copy_weight)
        action_paste_weight = QtWidgets.QAction(self)
        action_paste_weight.setText('Paste')
        action_paste_weight.setObjectName("actionPasteWeight")
        action_paste_weight.triggered.connect(partial(self.paste_weight, map_name_format_string))
        menu.addAction(action_paste_weight)
        action_invert_weight = QtWidgets.QAction(self)
        action_invert_weight.setText('Invert')
        action_invert_weight.setObjectName("actionInvertWeight")
        action_invert_weight.triggered.connect(
            partial(self.invert_weight, map_name_format_string, mesh_name))
        menu.addAction(action_invert_weight)

    def open_tet_menu(self, menu, mesh_name):
        self.add_placeholder_action(menu)
        menu.addSection('Maps')
        weight_map_menu = menu.addMenu('weight')
        weight_map_menu.addAction(self.actionPaintSource)
        self.add_copy_paste_invert_to_menu(weight_map_menu, '{}.weightList[0].weights[0:{}]',
                                           mesh_name)

    def open_fiber_menu(self, menu, mesh_name):
        self.add_placeholder_action(menu)
        menu.addSection('Maps')
        weight_map_menu = menu.addMenu('weight')
        weight_map_menu.addAction(self.actionPaintSource)
        self.add_copy_paste_invert_to_menu(weight_map_menu, '{}.weightList[0].weights[0:{}]',
                                           mesh_name)
        end_points_map_menu = menu.addMenu('endPoints')
        end_points_map_menu.addAction(self.actionPaintEndPoints)
        self.add_copy_paste_invert_to_menu(end_points_map_menu, '{}.endPoints', mesh_name)

    def open_material_menu(self, menu, mesh_name):
        self.add_placeholder_action(menu)
        menu.addSection('Maps')
        weight_map_menu = menu.addMenu('weight')
        weight_map_menu.addAction(self.actionPaintSource)
        self.add_copy_paste_invert_to_menu(weight_map_menu, '{}.weightList[0].weights[0:{}]',
                                           mesh_name)

    def open_attachment_menu(self, menu, source_mesh_name, target_mesh_name):
        menu.addAction(self.actionSelectST)
        menu.addSection('Maps')
        source_menu_text = (source_mesh_name[:12] +
                            '..') if len(source_mesh_name) > 14 else source_mesh_name
        source_menu_text = 'source (%s)' % source_menu_text
        source_map_menu = menu.addMenu(source_menu_text)
        source_map_menu.addAction(self.actionPaintSource)
        self.add_copy_paste_invert_to_menu(source_map_menu, '{}.weightList[0].weights[0:{}]',
                                           source_mesh_name)
        target_menu_text = (target_mesh_name[:12] +
                            '..') if len(target_mesh_name) > 14 else target_mesh_name
        target_menu_text = 'target (%s)' % target_menu_text
        target_map_menu = menu.addMenu(target_menu_text)
        target_map_menu.addAction(self.actionPaintTarget)
        self.add_copy_paste_invert_to_menu(target_map_menu, '{}.weightList[1].weights[0:{}]',
                                           target_mesh_name)
        menu.addSection('')
        proximity_menu = menu.addMenu('Paint By Proximity')
        prox_widget = view.ProximityWidget()
        action_paint_by_prox = QtWidgets.QWidgetAction(proximity_menu)
        action_paint_by_prox.setDefaultWidget(prox_widget)
        proximity_menu.addAction(action_paint_by_prox)

    def tree_changed(self, *args):
        """When the tree selection changes this gets executed to select
        corresponding item in Maya scene.
        """
        # To exclude cycle caused by selection we need to break the loop before manually making selection
        self.is_selection_callback_active = False
        indexes = self.treeView.selectedIndexes()
        mc.select(clear=True)
        if indexes:
            nodes = [x.data(model.SceneGraphModel.nodeRole).long_name for x in indexes]
            existing_nodes = mc.ls(nodes, long=True)
            if len(existing_nodes) == len(nodes):
                mc.select(nodes)
            else:
                missing_objs = list(set(nodes) - set(existing_nodes))
                mc.warning('These objects are not found in the scene: ' + ', '.join(missing_objs))
        self.is_selection_callback_active = True

    def redraw_tree_view(self):
        # This updates TreeView UI ones attribute changed
        # without that it will be updated only when focus is moved to this widget
        # not the best solution and has be to revisited if better one found
        # works faster then rebuilding TreeView
        self.treeView.hide()
        self.treeView.show()

    def attribute_changed(self, msg, plug, other_plug, *clientData):
        if msg & (om.MNodeMessage.kAttributeSet | om.MNodeMessage.kAttributeLocked
                  | om.MNodeMessage.kAttributeUnlocked | om.MNodeMessage.kConnectionMade
                  | om.MNodeMessage.kConnectionBroken):
            name = plug.name()
            attr_name = name.split(".")[-1]
            node_name = name.split(".")[0]
            z_node = self.builder.get_scene_items(name_filter=node_name)[-1]
            if attr_name in z_node.attrs:
                attr_dict = mz.build_attr_key_values(node_name, [attr_name])
                if attr_name in attr_dict:
                    z_node.attrs[attr_name] = attr_dict[attr_name]

        self.redraw_tree_view()

    def node_renamed(self, msg, prev_name, *clientData):
        '''
        This triggers when node renamed in maya
        Renames corresponding node in Scene Panel
        :param msg: MObject
        :param prev_name: previous name
        :param clientData: custom data
        :return: None
        '''
        if msg.hasFn(om.MFn.kDagNode):
            m_dag_path = om.MDagPath()
            om.MDagPath.getAPathTo(msg, m_dag_path)
            full_path_name = m_dag_path.fullPathName()
            current_full_name = full_path_name
        else:
            dep_node = om.MFnDependencyNode(msg)
            current_full_name = dep_node.name()

        scene_items = self.builder.get_scene_items()

        for item in scene_items:
            if msg == item.mobject:
                item.name = current_full_name
                break

        self.redraw_tree_view()

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
            self.builder = zva.Ziva()
            self.builder.retrieve_connections()
            root_node = self.builder.root_node

        scene_items = self.builder.get_scene_items()

        # currently expanded items
        expanded = self._proxy_model.match(self._proxy_model.index(0, 0),
                                           model.SceneGraphModel.expandedRole, True, -1,
                                           QtCore.Qt.MatchExactly | QtCore.Qt.MatchRecursive)

        # remember names of items to expand
        names_to_expand = []
        for index in expanded:
            node = index.data(model.SceneGraphModel.nodeRole)
            names_to_expand.append(node.long_name)

        self.unregister_callbacks(["AttributeChanged", "NameChanged"])
        self.callback_ids["AttributeChanged"] = []
        self.callback_ids["NameChanged"] = []

        # connect callbacks from Ziva objects
        for item in scene_items:
            obj = item.mobject
            id_ = om.MNodeMessage.addAttributeChangedCallback(obj, self.attribute_changed)
            self.callback_ids["AttributeChanged"].append(id_)
            id_ = om.MNodeMessage.addNameChangedCallback(obj, self.node_renamed)
            self.callback_ids["NameChanged"].append(id_)

        # connect callbacks for Maya meshes
        for item in self.builder.bodies.values():
            obj = item.mobject
            id_ = om.MNodeMessage.addNameChangedCallback(obj, self.node_renamed)
            self.callback_ids["NameChanged"].append(id_)

        self._model.beginResetModel()
        self._model.root_node = root_node
        self._model.endResetModel()

        sel = mc.ls(sl=True, long=True)
        # select item in treeview that is selected in maya to begin with and
        # expand item in view.
        if expanded:
            for name in names_to_expand:
                indices = self._proxy_model.match(self._proxy_model.index(0, 0),
                                                  model.SceneGraphModel.fullNameRole, name, -1,
                                                  QtCore.Qt.MatchExactly | QtCore.Qt.MatchRecursive)
                for index in indices:
                    self.treeView.expand(index)
        if sel:
            checked = self.find_and_select(sel)

            # this works for a zBuilder view.  This is expanding the item
            # selected and it's parent if any.  This makes it possible if you
            # have a material or attachment selected, it will become visible in
            # UI
            if checked:
                # keeps previous expansion if TreeView was updated
                self.treeView.expand(checked[0])
                parent = checked[0].parent()
                if parent.isValid():
                    self.treeView.expand(parent)

        # Expand all zSolverTransform tree items-------------------------------
        if not expanded:
            for row in range(self._proxy_model.rowCount()):
                index = self._proxy_model.index(row, 0)
                node = index.data(model.SceneGraphModel.nodeRole)
                if node.type == 'zSolverTransform':
                    self.treeView.expand(index)
                    break

    def find_and_select(self, sel=None):
        """
        find and select items in the Tree View based on maya selection
        :param sel: maya selection
        :return:
        checked - indices that match selection ( QModelIndex )
        """
        if not sel:
            sel = mc.ls(sl=True, long=True)
        if sel:
            checked = []
            for s in sel:
                checked += self._proxy_model.match(
                    self._proxy_model.index(0, 0), model.SceneGraphModel.fullNameRole, s, -1,
                    QtCore.Qt.MatchExactly | QtCore.Qt.MatchRecursive)

            for index in checked:
                self.treeView.selectionModel().select(index, QtCore.QItemSelectionModel.Select)
            return checked

    def selection_callback(self, *args):
        # To exclude cycle caused by selection we need to break the loop before manually making selection
        if self.is_selection_callback_active:
            self.treeView.selectionModel().selectionChanged.disconnect(self.tree_changed)
            self.treeView.selectionModel().clearSelection()
            self.find_and_select()
            self.treeView.selectionModel().selectionChanged.connect(self.tree_changed)

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

    def copy_weight(self, map_name_format_string, mesh_name):
        """
        :param map_name_format_string: A format string to produce the map name.
               Format argument will be (node_name)
        :param mesh_name: name of the mesh
        :return: None
        """
        indexes = self.treeView.selectedIndexes()
        tmp = []

        for index in indexes:
            node = index.data(model.SceneGraphModel.nodeRole)
            map_node = mp.Map()
            # remove vertex array if exists, requirement for populate method
            map_name_format_string = map_name_format_string.split('[0:')[0]
            map_node.populate(map_name_format_string.format(node.name), mesh_name)
            weights = map_node.values
            tmp.append(weights)

        self.weights_clipboard = [sum(i) for i in zip(*tmp)]
        self.weights_clipboard = [max(min(x, 1.0), 0) for x in self.weights_clipboard]

    def invert_weight(self, map_name_format_string, mesh_name):
        """
        :param map_name_format_string: A format string to produce the map name.
               Format arguments will be (node_name, number_of_vertices_in_mesh)
        :param mesh_name: name of the mesh
        :return: None
        """
        indexes = self.treeView.selectedIndexes()

        for index in indexes:
            node = index.data(model.SceneGraphModel.nodeRole)
            map_node = mp.Map()
            # remove vertex array if exists, requirement for populate method
            map_name_format_string_part = map_name_format_string.split('[0:')[0]
            map_node.populate(map_name_format_string_part.format(node.name), mesh_name)
            weights = map_node.values
            number_of_vertices_in_mesh = len(weights) - 1

            weights = [1.0 - x for x in weights]

            map_attribute = map_name_format_string.format(node.name, number_of_vertices_in_mesh)
            self.set_weights(map_attribute, weights)

    def paste_weight(self, map_name_format_string):
        """
        :param map_name_format_string: A format string to produce the map name.
               Format arguments will be (node_name, number_of_vertices_in_mesh)
        :return: None
        """
        indexes = self.treeView.selectedIndexes()
        number_of_vertices_in_mesh = len(self.weights_clipboard) - 1
        for index in indexes:
            node = index.data(model.SceneGraphModel.nodeRole)

            map_attribute = map_name_format_string.format(node.name, number_of_vertices_in_mesh)
            self.set_weights(map_attribute, self.weights_clipboard)

    def set_weights(self, map_attribute, weights):
        # Maya's weightList.weights is not doubleArray and should be set as mel command
        # Could not set doubleArray easily other then using maya.cmds ( Maya issue )
        if mc.getAttr(map_attribute, type=True) == 'doubleArray':
            mc.setAttr(map_attribute, weights, type='doubleArray')
        else:
            tmp = []
            for w in weights:
                tmp.append(str(w))
            val = ' '.join(tmp)
            cmd = "setAttr " + map_attribute + " " + val
            mm.eval(cmd)
