import weakref
from functools import partial
from collections import defaultdict

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
import maya.utils as mutils
import re

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
        # list of object names that removed in Maya to delete them on idle state from Scene Panel
        self.nodes_to_remove = []
        # clipboard for copied attributes
        self.attrs_clipboard = {}
        # clipboard for copied weightmaps
        self.weights_clipboard = []
        # list of nodes that are waiting for Maya's idle state to be added to Scene Panel
        self.waiting_nodes = []

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

        self.tool_bar = QtWidgets.QToolBar(self)
        self.tool_bar.setIconSize(QtCore.QSize(27, 27))
        self.tool_bar.setObjectName("toolBar")

        self.top_layout = QtWidgets.QHBoxLayout()
        self.top_layout.addWidget(self.tool_bar)
        self.top_layout.setContentsMargins(15, 0, 0, 0)
        self.main_layout.addLayout(self.top_layout)
        self.main_layout.addWidget(self.treeView)

        self.callback_ids = defaultdict(list)

        self.set_root_node(root_node=root_node)

        self.destroyed.connect(lambda: self.unregister_callbacks())

        self.is_selection_callback_active = False
        self._setup_node_callbacks()
        self._setup_scene_callbacks()
        self.treeView.selectionModel().selectionChanged.connect(self.tree_changed)

        self._setup_actions()

        self.tool_bar.addAction(self.actionRefresh)

    def _setup_node_callbacks(self):
        node_callbacks = ["NodeAdded", "NodeRemoved", "SelectionCallback"]
        self.unregister_callbacks(node_callbacks)
        id_ = om.MDGMessage.addNodeAddedCallback(self.node_added)
        self.callback_ids["NodeAdded"] = [id_]

        id_ = om.MDGMessage.addNodeRemovedCallback(self.add_nodes_to_remove)
        self.callback_ids["NodeRemoved"] = [id_]

        # eventCallback SelectionChanged and selectionModel.selectionChanged will cause a loop if
        # you making selection by code, to prevent that make sure to break the loop by using variable
        # self.is_selection_callback_active = False
        id_ = om.MEventMessage.addEventCallback("SelectionChanged", self.selection_callback)
        self.callback_ids["SelectionCallback"] = [id_]

        self.is_selection_callback_active = True

    def _setup_scene_callbacks(self):
        scene_callbacks = ["BeforeOpen", "BeforeNew", "AfterOpen", "AfterNew"]
        non_scene_callbacks = list(set(self.callback_ids) - set(scene_callbacks))
        self.unregister_callbacks(scene_callbacks)

        id_ = om.MSceneMessage.addCallback(om.MSceneMessage.kBeforeOpen,
                                           partial(self.unregister_callbacks, non_scene_callbacks))
        self.callback_ids["BeforeOpen"] = [id_]
        id_ = om.MSceneMessage.addCallback(om.MSceneMessage.kBeforeNew,
                                           partial(self.unregister_callbacks, non_scene_callbacks))
        self.callback_ids["BeforeNew"] = [id_]

        id_ = om.MSceneMessage.addCallback(om.MSceneMessage.kAfterOpen, self.update_new_scene)
        self.callback_ids["AfterOpen"] = [id_]
        id_ = om.MSceneMessage.addCallback(om.MSceneMessage.kAfterNew, self.update_new_scene)
        self.callback_ids["AfterNew"] = [id_]

    def update_new_scene(self, *ignore):
        mc.select(cl=True)
        self.set_root_node()
        self._setup_node_callbacks()

    def unregister_callbacks(self, callback_names=None, *ignore):
        callback_names = callback_names or self.callback_ids.keys()

        for callback in callback_names:
            if callback in self.callback_ids:
                for id_ in self.callback_ids[callback]:
                    om.MMessage.removeCallback(id_)
                self.callback_ids[callback] = []
                if callback == "SelectionCallback":
                    self.is_selection_callback_active = False

    def _setup_actions(self):
        refresh_path = icons.get_icon_path_from_name('refresh')
        refresh_icon = QtGui.QIcon()
        refresh_icon.addPixmap(QtGui.QPixmap(refresh_path), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.actionRefresh = QtWidgets.QAction(self)
        self.actionRefresh.setText('Refresh')
        self.actionRefresh.setIcon(refresh_icon)
        self.actionRefresh.setObjectName("actionUndo")
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

    def copy_attrs(self):
        self.attrs_clipboard = {}
        indexes = self.treeView.selectedIndexes()
        node = indexes[-1].data(model.SceneGraphModel.nodeRole)
        self.attrs_clipboard[node.type] = node.attrs.copy()

    def paste_attrs(self):
        indexes = self.treeView.selectedIndexes()
        for index in indexes:
            node = index.data(model.SceneGraphModel.nodeRole)
            for attr, entry in self.attrs_clipboard.get(node.type, {}).iteritems():
                mc.setAttr("{}.{}".format(node.name, attr), lock=False)
                mc.setAttr("{}.{}".format(node.name, attr), entry['value'], lock=entry['locked'])

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

        if not node.long_association:
            return

        menu = QtWidgets.QMenu(self)

        source_mesh_name = node.long_association[0]
        if len(node.long_association) > 1:
            target_mesh_name = node.long_association[1]
        else:
            target_mesh_name = None
        menu_dict = {
            'zTet': [self.open_tet_menu, menu, source_mesh_name],
            'zFiber': [self.open_fiber_menu, menu, source_mesh_name],
            'zMaterial': [self.open_tet_menu, menu, source_mesh_name],
            'zAttachment': [self.open_attachment_menu, menu, source_mesh_name, target_mesh_name],
            'zTissue': [self.open_tissue_menu, menu],
            'zBone': [self.open_bone_menu, menu],
            'zLineOfAction': [self.open_line_of_action_menu, menu],
            'zRestShapeNode': [self.open_rest_shape_menu, menu]
        }

        if node.type in menu_dict:
            method = menu_dict[node.type][0]
            args = menu_dict[node.type][1:]
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

    def add_attributes_menu(self, menu):
        attrs_menu = menu.addMenu('attributes')
        attrs_menu.addAction(self.actionCopyAttrs)
        attrs_menu.addAction(self.actionPasteAttrs)

    def open_tet_menu(self, menu, mesh_name):
        self.add_attributes_menu(menu)
        menu.addSection('Maps')
        weight_map_menu = menu.addMenu('weight')
        weight_map_menu.addAction(self.actionPaintSource)
        self.add_copy_paste_invert_to_menu(weight_map_menu, '{}.weightList[0].weights[0:{}]',
                                           mesh_name)

    def open_fiber_menu(self, menu, mesh_name):
        self.add_attributes_menu(menu)
        menu.addSection('Maps')
        weight_map_menu = menu.addMenu('weight')
        weight_map_menu.addAction(self.actionPaintSource)
        self.add_copy_paste_invert_to_menu(weight_map_menu, '{}.weightList[0].weights[0:{}]',
                                           mesh_name)
        end_points_map_menu = menu.addMenu('endPoints')
        end_points_map_menu.addAction(self.actionPaintEndPoints)
        self.add_copy_paste_invert_to_menu(end_points_map_menu, '{}.endPoints', mesh_name)

    def open_material_menu(self, menu, mesh_name):
        self.add_attributes_menu(menu)
        menu.addSection('Maps')
        weight_map_menu = menu.addMenu('weight')
        weight_map_menu.addAction(self.actionPaintSource)
        self.add_copy_paste_invert_to_menu(weight_map_menu, '{}.weightList[0].weights[0:{}]',
                                           mesh_name)

    def open_attachment_menu(self, menu, source_mesh_name, target_mesh_name):
        self.add_attributes_menu(menu)
        menu.addSection('')
        menu.addAction(self.actionSelectST)
        menu.addSection('Maps')
        # create short name for labels
        source_mesh_name_short = source_mesh_name.split('|')[-1]
        target_mesh_name_short = target_mesh_name.split('|')[-1]
        source_menu_text = (source_mesh_name_short[:12] +
                            '..') if len(source_mesh_name_short) > 14 else source_mesh_name_short
        source_menu_text = 'source (%s)' % source_menu_text
        source_map_menu = menu.addMenu(source_menu_text)
        source_map_menu.addAction(self.actionPaintSource)
        self.add_copy_paste_invert_to_menu(source_map_menu, '{}.weightList[0].weights[0:{}]',
                                           source_mesh_name)
        target_menu_text = (target_mesh_name_short[:12] +
                            '..') if len(target_mesh_name_short) > 14 else target_mesh_name_short
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

    def open_tissue_menu(self, menu):
        self.add_attributes_menu(menu)

    def open_bone_menu(self, menu):
        self.add_attributes_menu(menu)

    def open_line_of_action_menu(self, menu):
        self.add_attributes_menu(menu)

    def open_rest_shape_menu(self, menu):
        self.add_attributes_menu(menu)

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
            scene_items = self.builder.get_scene_items(name_filter=node_name)
            if scene_items:
                z_node = scene_items[-1]
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

    def add_nodes_to_remove(self, node, *clientData):
        # filter some node types kDagNode used for meshes, transforms and curves
        if node.hasFn(om.MFn.kDagNode) or node.apiTypeStr() in ('kPluginDependNode',
                                                                'kPluginDeformerNode'):
            dep_node = om.MFnDependencyNode(node)
            node_name = dep_node.name()
            self.nodes_to_remove.append(node_name)
            # to call scriptJob once per cycle
            if len(self.nodes_to_remove) == 1:
                # maya.utils.executeDeferred causing Maya to crash after closing Scene Panel window
                # Maya 2018 bug, works fine in Maya 2019
                # ie - idleEvent, ro - runOnce
                mc.scriptJob(ie=self.clean_removed_nodes, ro=True)

    def wrap_model_indexes_to_persistent(self, indexes):
        # need to store parent since if you get parent from model_index it returns bad
        # QModelIndex which refers to the wrong internal pointer
        persistent_indexes = []
        persistent_indexes_parent = []
        for index in indexes:
            model_index = self._proxy_model.mapToSource(index)
            parent_index = self._proxy_model.mapToSource(index.parent())
            persistent_indexes.append(QtCore.QPersistentModelIndex(model_index))
            persistent_indexes_parent.append(QtCore.QPersistentModelIndex(parent_index))

        return persistent_indexes, persistent_indexes_parent

    def clean_removed_nodes(self):
        if not self.nodes_to_remove:
            return

        for node_name in self.nodes_to_remove:
            nodes = self.builder.get_scene_items(name_filter=[node_name])
            if nodes:
                node = nodes[0]
                name = node.long_name
                if not mc.objExists(name):
                    indexes = self._proxy_model.match(
                        self._proxy_model.index(0, 0), model.SceneGraphModel.fullNameRole, name, -1,
                        QtCore.Qt.MatchExactly | QtCore.Qt.MatchRecursive)

                    p_indexes, p_indexes_parent = self.wrap_model_indexes_to_persistent(indexes)

                    for i, index in enumerate(p_indexes):
                        self._model.removeRow(index.row(), p_indexes_parent[i])
                    scene_items = self.builder.get_scene_items()
                    scene_items.remove(node)

        self.build_scene_items_callbacks()

        self.nodes_to_remove = []
        self.clean_empty_nodes()

    # removes geometry nodes from Scene Panel that don't have children
    def clean_empty_nodes(self):
        bodies = self.builder.bodies
        to_remove = []
        for name in bodies:
            node = bodies[name]
            if not node.children:
                indexes = self._proxy_model.match(self._proxy_model.index(0, 0),
                                                  model.SceneGraphModel.fullNameRole, name, -1,
                                                  QtCore.Qt.MatchExactly | QtCore.Qt.MatchRecursive)

                p_indexes, p_indexes_parent = self.wrap_model_indexes_to_persistent(indexes)
                for i, index in enumerate(p_indexes):
                    self._model.removeRow(index.row(), p_indexes_parent[i])
                    to_remove.append(name)

        for name in to_remove:
            bodies.pop(name)

    def build_scene_items_callbacks(self):
        self.unregister_callbacks(["AttributeChanged", "NameChanged"])

        scene_items = self.builder.get_scene_items()
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

    def add_waiting_nodes(self):
        # This statement is useful if multiple nodes were added at the same time
        # node_added will ask this method to be called as many times as amount of nodes created
        # but waiting_nodes list contains all of them so it can be executed one time
        if self.waiting_nodes:
            # store currently expanded items
            names_to_expand = self.get_expanded()

            mc.select(self.waiting_nodes)
            self.builder.retrieve_connections()

            self.build_scene_items_callbacks()

            # restore previous expansion in treeView
            if names_to_expand:
                self.expand(names_to_expand)

            self.waiting_nodes = []

    def node_added(self, node, *clientData):
        if node.apiTypeStr() in ('kPluginDependNode', 'kPluginDeformerNode'):
            dep_node = om.MFnDependencyNode(node)
            node_type = dep_node.typeName()
            # regex to filter Ziva nodes: starts with z and capital letter
            ziva_nodes_pattern = re.compile('z[A-Z]')
            if ziva_nodes_pattern.match(node_type):
                self.waiting_nodes.append(dep_node.name())
                # to call executeDeferred once per cycle
                if len(self.waiting_nodes) == 1:
                    mutils.executeDeferred(self.add_waiting_nodes)

    def get_expanded(self):
        """
        :return: array of item names that are currently expanded in treeView
        """
        # store currently expanded items
        expanded = self._proxy_model.match(self._proxy_model.index(0, 0),
                                           model.SceneGraphModel.expandedRole, True, -1,
                                           QtCore.Qt.MatchExactly | QtCore.Qt.MatchRecursive)
        names_to_expand = []
        for index in expanded:
            node = index.data(model.SceneGraphModel.nodeRole)
            names_to_expand.append(node.long_name)

        return names_to_expand

    def expand(self, names):
        """
        :param names: list of names to expand in treeView
        :return: None
        """
        # collapseAll added in case refreshing of treeView needed
        # otherwise new items might not be displayed ( Qt bug )
        self.treeView.collapseAll()
        for name in names:
            indexes = self._proxy_model.match(self._proxy_model.index(0, 0),
                                              model.SceneGraphModel.fullNameRole, name, -1,
                                              QtCore.Qt.MatchExactly | QtCore.Qt.MatchRecursive)
            for index in indexes:
                self.treeView.expand(index)

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
            self.builder = zva.Ziva()
            self.builder.retrieve_connections()
            root_node = self.builder.root_node

        # remember names of items to expand
        names_to_expand = self.get_expanded()

        self.build_scene_items_callbacks()

        self._model.beginResetModel()
        self._model.root_node = root_node
        self._model.endResetModel()

        # restore previous expansion in treeView
        if names_to_expand:
            self.expand(names_to_expand)

        # select item in treeview that is selected in maya to begin with and
        # expand item in view.
        sel = mc.ls(sl=True, long=True)

        if sel:
            checked = self.find_and_select(sel)

            # this works for a zBuilder view.  This is expanding the item
            # selected and it's parent if any.
            if checked:
                self.treeView.expand(checked[0])
                parent = checked[0].parent()
                if parent.isValid():
                    self.treeView.expand(parent)

        # expand all zSolverTransform tree items
        if not names_to_expand:
            for row in range(self._proxy_model.rowCount()):
                index = self._proxy_model.index(row, 0)
                node = index.data(model.SceneGraphModel.nodeRole)
                if node.type == 'zSolverTransform':
                    self.treeView.expand(index)

    def find_and_select(self, sel=None):
        """
        find and select items in the Tree View based on maya selection
        :param sel: maya selection
        :return:
        checked - indexes that match selection ( QModelIndex )
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

    def get_weights(self, map_name, mesh_name):
        """
        :param map_name: name of the map
        :param mesh_name: name of the mesh
        :return: array of weight values
        """
        map_node = mp.Map()
        map_node.populate(map_name, mesh_name)
        return map_node.values

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
            # remove vertex array if exists
            map_name_format_string = map_name_format_string.split('[0:')[0]
            map_name = map_name_format_string.format(node.name)
            weights = self.get_weights(map_name, mesh_name)
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
            # remove vertex array if exists
            map_name_format_string_part = map_name_format_string.split('[0:')[0]
            map_name = map_name_format_string_part.format(node.name)
            weights = self.get_weights(map_name, mesh_name)
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
            tmp = [str(w) for w in weights]
            val = ' '.join(tmp)
            cmd = "setAttr " + map_attribute + " " + val
            mm.eval(cmd)
