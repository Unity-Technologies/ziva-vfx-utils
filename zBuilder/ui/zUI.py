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
import maya.utils as mutils

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

        self.callback_ids = {}

        self.reset_tree(root_node=root_node)

        id_ = om.MDGMessage.addNodeAddedCallback(self.node_added)
        self.callback_ids["NodeAdded"] = [id_]

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

        self.actionCopy = QtWidgets.QAction(self)
        self.actionCopy.setText('Copy')
        self.actionCopy.setObjectName("actionCopy")

        self.actionPaste = QtWidgets.QAction(self)
        self.actionPaste.setText('Paste')
        self.actionPaste.setObjectName("actionPaste")

        self.actionPasteSansMaps = QtWidgets.QAction(self)
        self.actionPasteSansMaps.setText('Paste without maps')
        self.actionPasteSansMaps.setObjectName("actionPasteSansMaps")

        self.actionRemoveSolver = QtWidgets.QAction(self)
        self.actionRemoveSolver.setText('Remove Solver')
        self.actionRemoveSolver.setObjectName("actionRemove")
        self.actionRemoveSolver.triggered.connect(self.reset_tree)

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

        self.actionPaintWeight = QtWidgets.QAction(self)
        self.actionPaintWeight.setText('Paint')
        self.actionPaintWeight.setObjectName("paintWeight")
        self.actionPaintWeight.triggered.connect(partial(self.paint_weights, 0, 'weights'))

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
<<<<<<< HEAD
        node = indexes[0].data(model.SceneGraphModel.nodeRole)

        menu = model.CustomMenu(self)
        menu.setWindowFlags(menu.windowFlags() | QtCore.Qt.FramelessWindowHint | QtCore.Qt.NoDropShadowWindowHint)
        menu.setAttribute(QtCore.Qt.WA_TranslucentBackground)

        if node.type == 'zTet':
            menu.addLabel('Maps')
            menu.setFixedWidth(100)
            source_map_menu = menu.addMenu('weight')
            source_map_menu.addAction(self.actionPaintWeight)
            source_map_menu.addSection('')
            source_map_menu.addAction(self.actionCopyWeight)
            source_map_menu.addAction(self.actionPasteWeight)
            source_map_menu.addAction(self.actionInvertWeight)

        if node.type == 'zFiber':
            menu.addLabel('Maps')
            menu.setFixedWidth(120)
            source_map_menu = menu.addMenu('weight')
            source_map_menu.addAction(self.actionPaintWeight)
            source_map_menu.addSection('')
            source_map_menu.addAction(self.actionCopyWeight)
            source_map_menu.addAction(self.actionPasteWeight)
            source_map_menu.addAction(self.actionInvertWeight)

            target_map_menu = menu.addMenu('endPoints')
            target_map_menu.addAction(self.actionPaintEndPoints)
            target_map_menu.addSection('')
            target_map_menu.addAction(self.actionCopyWeight)
            target_map_menu.addAction(self.actionPasteWeight)
            target_map_menu.addAction(self.actionInvertWeight)

        if node.type == 'zMaterial':
            menu.addLabel('Maps')
            menu.setFixedWidth(100)
            source_map_menu = menu.addMenu('weight')
            source_map_menu.addAction(self.actionPaintWeight)
            source_map_menu.addSection('')
            source_map_menu.addAction(self.actionCopyWeight)
            source_map_menu.addAction(self.actionPasteWeight)
            source_map_menu.addAction(self.actionInvertWeight)

        if node.type == 'zEmbedder':
            menu.addAction(self.actionPaintWeight)
            menu.addSection('')

        if node.type == 'zAttachment':
            menu.addAction(self.actionSelectST)
            menu.addLabel('Maps')
            source_map_menu = menu.addMenu('source')
            source_map_menu.addAction(self.actionPaintSource)
            source_map_menu.addSection('')
            source_map_menu.addAction(self.actionCopyWeight)
            source_map_menu.addAction(self.actionPasteWeight)
            source_map_menu.addAction(self.actionInvertWeight)
            source_map_menu.addSection('')
            target_map_menu = menu.addMenu('target')
            target_map_menu.addAction(self.actionPaintTarget)
            target_map_menu.addSection('')
            target_map_menu.addAction(self.actionCopyWeight)
            target_map_menu.addAction(self.actionPasteWeight)
            target_map_menu.addAction(self.actionInvertWeight)
            menu.addSection('')
            sub = menu.addMenu('Paint By Proximity')
            sub.setTitle('Paint By Proximity')
            prox_widget = model.ProximityWidget()
            actionPaintByProx = QtWidgets.QWidgetAction(sub)
            actionPaintByProx.setDefaultWidget(prox_widget)
            sub.addAction(actionPaintByProx)

        menu.exec_(self.treeView.viewport().mapToGlobal(position))
=======
        if len(indexes) == 1:
            node = indexes[0].data(model.SceneGraphModel.nodeRole)

            menu = QtWidgets.QMenu(self)

            if node.type == 'zTet':
                # QMenu.addSection only works after action, creates an empty action before
                self.add_placeholder_action(menu)
                menu.addSection('Maps')
                source_map_menu = menu.addMenu('weight')
                source_map_menu.addAction(self.actionPaintWeight)

            if node.type == 'zFiber':
                self.add_placeholder_action(menu)
                menu.addSection('Maps')
                source_map_menu = menu.addMenu('weight')
                source_map_menu.addAction(self.actionPaintWeight)

                target_map_menu = menu.addMenu('endPoints')
                target_map_menu.addAction(self.actionPaintEndPoints)

            if node.type == 'zMaterial':
                self.add_placeholder_action(menu)
                menu.addSection('Maps')
                source_map_menu = menu.addMenu('weight')
                source_map_menu.addAction(self.actionPaintWeight)

            if node.type == 'zAttachment':
                menu.addAction(self.actionSelectST)

                menu.addSection('Maps')
                source_map_menu = menu.addMenu('source')
                source_map_menu.addAction(self.actionPaintSource)
                target_map_menu = menu.addMenu('target')
                target_map_menu.addAction(self.actionPaintTarget)
                menu.addSection('')
                proximity_menu = menu.addMenu('Paint By Proximity')
                prox_widget = view.ProximityWidget()
                action_paint_by_prox = QtWidgets.QWidgetAction(proximity_menu)
                action_paint_by_prox.setDefaultWidget(prox_widget)
                proximity_menu.addAction(action_paint_by_prox)

            menu.exec_(self.treeView.viewport().mapToGlobal(position))
>>>>>>> release/version1.7

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
        # elif msg & om.MNodeMessage.kConnectionMade:
        #     name = other_plug.name()
        #     node_name = name.split(".")[0]
        #     if name.split(".")[-1] in ['oMuscle', 'oGeo', 'oAttachment', 'oLineOfActionData']:
        #         # currently expanded items
        #         if not self.builder.get_scene_items(name_filter=node_name):
        #             expanded = self._proxy_model.match(self._proxy_model.index(0, 0),
        #                                                model.SceneGraphModel.expandedRole, True, -1,
        #                                                QtCore.Qt.MatchExactly | QtCore.Qt.MatchRecursive)
        #             names_to_expand = []
        #             for index in expanded:
        #                 node = index.data(model.SceneGraphModel.nodeRole)
        #                 names_to_expand.append(node.long_name)
        #             mc.select(node_name)
        #             self.unregister_callbacks(["AttributeChanged", "NameChanged"])
        #             self.callback_ids["AttributeChanged"] = []
        #             self.callback_ids["NameChanged"] = []
        #             self.builder.retrieve_connections()
        #             scene_items = self.builder.get_scene_items()
        #             for item in scene_items:
        #                 obj = item.mobject
        #                 id_ = om.MNodeMessage.addAttributeChangedCallback(obj, self.attribute_changed)
        #                 self.callback_ids["AttributeChanged"].append(id_)
        #                 id_ = om.MNodeMessage.addNameChangedCallback(obj, self.node_renamed)
        #                 self.callback_ids["NameChanged"].append(id_)
        #             for item in self.builder.bodies.values():
        #                 obj = item.mobject
        #                 id_ = om.MNodeMessage.addAttributeChangedCallback(obj, self.attribute_changed)
        #                 self.callback_ids["AttributeChanged"].append(id_)
        #                 id_ = om.MNodeMessage.addNameChangedCallback(obj, self.node_renamed)
        #                 self.callback_ids["NameChanged"].append(id_)
        #             self.treeView.collapseAll()
        #             for name in names_to_expand:
        #                 indices = self._proxy_model.match(
        #                     self._proxy_model.index(0, 0), model.SceneGraphModel.fullNameRole, name,
        #                     -1, QtCore.Qt.MatchExactly | QtCore.Qt.MatchRecursive)
        #                 for index in indices:
        #                     self.treeView.expand(index)

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

    def add_waiting_nodes(self):
        for node_name in self.waiting_nodes:
            print node_name
            if not self.builder.get_scene_items(name_filter=node_name):
                expanded = self._proxy_model.match(self._proxy_model.index(0, 0),
                                                   model.SceneGraphModel.expandedRole, True, -1,
                                                   QtCore.Qt.MatchExactly | QtCore.Qt.MatchRecursive)
                names_to_expand = []
                for index in expanded:
                    node = index.data(model.SceneGraphModel.nodeRole)
                    names_to_expand.append(node.long_name)

                self.unregister_callbacks(["AttributeChanged", "NameChanged"])
                self.callback_ids["AttributeChanged"] = []
                self.callback_ids["NameChanged"] = []

                mc.select(node_name)
                self.builder.retrieve_connections()
                scene_items = self.builder.get_scene_items()
                for item in scene_items:
                    obj = item.mobject
                    id_ = om.MNodeMessage.addAttributeChangedCallback(obj, self.attribute_changed)
                    self.callback_ids["AttributeChanged"].append(id_)
                    id_ = om.MNodeMessage.addNameChangedCallback(obj, self.node_renamed)
                    self.callback_ids["NameChanged"].append(id_)
                for item in self.builder.bodies.values():
                    obj = item.mobject
                    id_ = om.MNodeMessage.addAttributeChangedCallback(obj, self.attribute_changed)
                    self.callback_ids["AttributeChanged"].append(id_)
                    id_ = om.MNodeMessage.addNameChangedCallback(obj, self.node_renamed)
                    self.callback_ids["NameChanged"].append(id_)

                self.treeView.collapseAll()
                for name in names_to_expand:
                    indices = self._proxy_model.match(
                        self._proxy_model.index(0, 0), model.SceneGraphModel.fullNameRole, name,
                        -1, QtCore.Qt.MatchExactly | QtCore.Qt.MatchRecursive)
                    for index in indices:
                        self.treeView.expand(index)

        self.waiting_nodes = []

    def node_added(self, node, *clientData):
        if node.apiTypeStr() in ('kPluginDependNode', 'kPluginDeformerNode'):
            dep_node = om.MFnDependencyNode(node)
            node_type = dep_node.typeName()
            ziva_nodes = ['zAttachment', 'zBone', 'zMaterial', 'zTissue', 'zRivetToBone', 'zLineOfAction', 'zFiber']
            if node_type in ziva_nodes:
                self.waiting_nodes.append(dep_node.name())
                mutils.executeDeferred(self.add_waiting_nodes)

        # kPluginDeformerNode
        #print node.apiType()

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
            id_ = om.MNodeMessage.addAttributeChangedCallback(obj, self.attribute_changed)
            self.callback_ids["AttributeChanged"].append(id_)
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
