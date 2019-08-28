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
        self.weights = []
        self.attrs = {}

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
        # self.treeView.setHeaderHidden(True)
        header = self.treeView.header()
        header.setOffset(-20)
        header.setOffsetToSectionPosition(20)
        header.setFixedHeight(10)

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

        self.actionCopyWeight = QtWidgets.QAction(self)
        self.actionCopyWeight.setText('Copy')
        self.actionCopyWeight.setObjectName("actionCopyWeight")
        self.actionCopyWeight.triggered.connect(self.copy_weight)

        self.actionCopyAttrs = QtWidgets.QAction(self)
        self.actionCopyAttrs.setText('Copy')
        self.actionCopyAttrs.setObjectName("actionCopyAttrs")
        self.actionCopyAttrs.triggered.connect(self.copy_attrs)

        self.actionInvertWeight = QtWidgets.QAction(self)
        self.actionInvertWeight.setText('Invert')
        self.actionInvertWeight.setObjectName("actionInvertWeight")
        self.actionInvertWeight.triggered.connect(self.invert_weight)

        self.actionPasteWeight = QtWidgets.QAction(self)
        self.actionPasteWeight.setText('Paste')
        self.actionPasteWeight.setObjectName("actionPasteWeight")
        self.actionPasteWeight.triggered.connect(self.paste_weight)

        self.actionPasteAttrs = QtWidgets.QAction(self)
        self.actionPasteAttrs.setText('Paste')
        self.actionPasteAttrs.setObjectName("actionPasteAttrs")
        self.actionPasteAttrs.triggered.connect(self.paste_attrs)

        self.actionDuplicateObject = QtWidgets.QAction(self)
        self.actionDuplicateObject.setText("Duplicate")
        self.actionDuplicateObject.setObjectName("actionDuplicateObject")
        self.actionDuplicateObject.triggered.connect(self.duplicate_ziva_objects)

        self.actionToggleTetsVisibility = QtWidgets.QAction(self)
        self.actionToggleTetsVisibility.setText("Tets")
        self.actionToggleTetsVisibility.setObjectName("actionToggleTets")
        self.actionToggleTetsVisibility.setCheckable(True)

        self.actionToggleFibersVisibility = QtWidgets.QAction(self)
        self.actionToggleFibersVisibility.setText("Fibers")
        self.actionToggleFibersVisibility.setObjectName("actionToggleFibers")
        self.actionToggleFibersVisibility.setCheckable(True)

        self.actionToggleBonesVisibility = QtWidgets.QAction(self)
        self.actionToggleBonesVisibility.setText("Bones")
        self.actionToggleBonesVisibility.setObjectName("actionToggleBones")
        self.actionToggleBonesVisibility.setCheckable(True)

        self.actionToggleAxesVisibility = QtWidgets.QAction(self)
        self.actionToggleAxesVisibility.setText("Axes")
        self.actionToggleAxesVisibility.setObjectName("actionToggleAxes")
        self.actionToggleAxesVisibility.setCheckable(True)

    def duplicate_ziva_objects(self):
        indexes = self.treeView.selectedIndexes()
        # currently expanded items
        expanded = self._proxy_model.match(self._proxy_model.index(0, 0),
                                           model.SceneGraphModel.expandedRole, True, -1,
                                           QtCore.Qt.MatchExactly | QtCore.Qt.MatchRecursive)
        # remember names of items to expand
        names_to_expand = []
        for index in expanded:
            node = index.data(model.SceneGraphModel.nodeRole)
            names_to_expand.append(node.long_name)
        for index in indexes:
            self.treeView.selectionModel().select(index, QtCore.QItemSelectionModel.SelectCurrent)
            self.copy_attrs()
            self.copy_weight()
            node = index.data(model.SceneGraphModel.nodeRole)
            if node.type == 'zMaterial':
                mc.select(node.association[0])
                name = mc.ziva(m=True)[0]
                mc.select(name)
                self.builder.retrieve_connections()
                scene_items = self.builder.get_scene_items()
                self.unregister_callbacks(["AttributeChanged", "NameChanged"])
                self.callback_ids["AttributeChanged"] = []
                self.callback_ids["NameChanged"] = []
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
            indices = self._proxy_model.match(self._proxy_model.index(0, 0),
                                              model.SceneGraphModel.fullNameRole, name, -1,
                                              QtCore.Qt.MatchExactly | QtCore.Qt.MatchRecursive)
            for index in indices:
                self.treeView.expand(index)
        self.paste_attrs()
        self.paste_weight()

    def copy_attrs(self):
        indexes = self.treeView.selectedIndexes()
        node = indexes[-1].data(model.SceneGraphModel.nodeRole)
        self.attrs[node.type] = node.attrs.copy()
        print self.attrs

    def paste_attrs(self):
        indexes = self.treeView.selectedIndexes()
        objs = []
        for index in indexes:
            node = index.data(model.SceneGraphModel.nodeRole)
            for key in self.attrs:
                if node.type == key:
                    for attr in self.attrs[key]:
                        if mc.getAttr("%s.%s" % (node.name, attr), lock=True):
                            mc.setAttr("%s.%s" % (node.name, attr), lock=False)
                        mc.setAttr("%s.%s" % (node.name, attr), self.attrs[key][attr]['value'])
                        mc.setAttr("%s.%s" % (node.name, attr),
                                   lock=self.attrs[key][attr]['locked'])
                    objs.append(node.name)
        if objs:
            print 'Attributes pasted to:', ', '.join(objs)

    def set_node_attribute(self, attr, node, value=None):
        if not value:
            value = not mc.getAttr('%s.%s' % (node.name, attr))
        mc.setAttr('%s.%s' % (node.name, attr), value)

    def paint_by_prox_options(self):
        """Brings up UI for painting by proximity.
        """
        indexes = self.treeView.selectedIndexes()[0]
        node = indexes.data(model.SceneGraphModel.nodeRole)
        mc.select(node.name, r=True)
        mm.eval('ZivaPaintAttachmentsByProximityOptions;')

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
        node = indexes[0].data(model.SceneGraphModel.nodeRole)

        menu = model.CustomMenu(self)
        menu.installEventFilter(menu)
        menu.setWindowFlags(menu.windowFlags() | QtCore.Qt.FramelessWindowHint
                            | QtCore.Qt.NoDropShadowWindowHint)
        menu.setAttribute(QtCore.Qt.WA_TranslucentBackground)

        if node.type == 'zSolverTransform':
            node = node.child(0)

        if node.type == 'zSolver':
            menu.addLabel('Visibility')
            menu.setFixedWidth(135)

            tets_value = node.attrs['showTetMeshes']['value']
            fibers_value = node.attrs['showMuscleFibers']['value']
            bones_value = node.attrs['showBones']['value']
            axes_value = node.attrs['showAxes']['value']
            attachments_value = node.attrs['showAttachments']['value']
            collisions_value = node.attrs['showCollisions']['value']
            materials_value = node.attrs['showMaterials']['value']

            self.actionToggleTetsVisibility.setChecked(tets_value)
            self.actionToggleTetsVisibility.triggered.connect(
                partial(self.set_node_attribute, 'showTetMeshes', node))
            menu.addAction(self.actionToggleTetsVisibility)
            self.actionToggleFibersVisibility.setChecked(fibers_value)
            self.actionToggleFibersVisibility.triggered.connect(
                partial(self.set_node_attribute, 'showMuscleFibers', node))
            menu.addAction(self.actionToggleFibersVisibility)
            self.actionToggleBonesVisibility.setChecked(bones_value)
            self.actionToggleBonesVisibility.triggered.connect(
                partial(self.set_node_attribute, 'showBones', node))
            menu.addAction(self.actionToggleBonesVisibility)
            self.actionToggleAxesVisibility.setChecked(axes_value)
            self.actionToggleAxesVisibility.triggered.connect(
                partial(self.set_node_attribute, 'showAxes', node))
            menu.addAction(self.actionToggleAxesVisibility)

            attachments_menu = menu.addMenu("Attachments")
            radio_widget = model.RadioButtonsWidget(['None', 'Type', 'Stiffness', 'Strain'],
                                                    attachments_value)
            for i, button in enumerate(radio_widget.buttons):
                button.clicked.connect(partial(self.set_node_attribute, 'showAttachments', node, i))
            action_attachments = QtWidgets.QWidgetAction(attachments_menu)
            action_attachments.setDefaultWidget(radio_widget)
            attachments_menu.addAction(action_attachments)

            collisions_menu = menu.addMenu("Collisions")
            radio_widget = model.RadioButtonsWidget(['None', 'Type', 'Stiffness', 'Strain'],
                                                    collisions_value)
            for i, button in enumerate(radio_widget.buttons):
                button.clicked.connect(partial(self.set_node_attribute, 'showCollisions', node, i))
            action_collisions = QtWidgets.QWidgetAction(collisions_menu)
            action_collisions.setDefaultWidget(radio_widget)
            collisions_menu.addAction(action_collisions)

            materials_menu = menu.addMenu("Materials")
            radio_widget = model.RadioButtonsWidget(
                ['None', 'Type', 'Youngs Modulus', 'Strain', 'Volume Change'], materials_value)
            for i, button in enumerate(radio_widget.buttons):
                button.clicked.connect(partial(self.set_node_attribute, 'showMaterials', node, i))
            action_materials = QtWidgets.QWidgetAction(materials_menu)
            action_materials.setDefaultWidget(radio_widget)
            materials_menu.addAction(action_materials)

        if node.type == 'zTet':
            menu.setFixedWidth(125)

            attributes_menu = menu.addMenu('attributes')
            attributes_menu.addAction(self.actionCopyAttrs)
            attributes_menu.addAction(self.actionPasteAttrs)

            menu.addLabel('Maps')
            source_map_menu = menu.addMenu('weight')
            source_map_menu.addAction(self.actionPaintWeight)
            source_map_menu.addSection('')
            action_copy_weight = self.actionCopyWeight
            source_map_menu.addAction(action_copy_weight)
            source_map_menu.addAction(self.actionPasteWeight)
            source_map_menu.addAction(self.actionInvertWeight)

        if node.type == 'zTissue':
            menu.setFixedWidth(125)

            attributes_menu = menu.addMenu('attributes')
            attributes_menu.addAction(self.actionCopyAttrs)
            attributes_menu.addAction(self.actionPasteAttrs)

        if node.type == 'zFiber':
            menu.setFixedWidth(125)

            attributes_menu = menu.addMenu('attributes')
            attributes_menu.addAction(self.actionCopyAttrs)
            attributes_menu.addAction(self.actionPasteAttrs)

            menu.addLabel('Maps')
            source_map_menu = menu.addMenu('weight')
            source_map_menu.addAction(self.actionPaintWeight)
            source_map_menu.addSection('')
            action_copy_weight = QtWidgets.QAction(self)
            action_copy_weight.setText('Copy')
            action_copy_weight.setObjectName("actionCopyWeight")
            action_copy_weight.triggered.connect(self.copy_weight)
            source_map_menu.addAction(action_copy_weight)
            source_map_menu.addAction(self.actionPasteWeight)
            source_map_menu.addAction(self.actionInvertWeight)

            target_map_menu = menu.addMenu('endPoints')
            target_map_menu.addAction(self.actionPaintEndPoints)
            target_map_menu.addSection('')
            action_copy_weight = QtWidgets.QAction(self)
            action_copy_weight.setText('Copy')
            action_copy_weight.setObjectName("actionCopyWeight")
            action_copy_weight.triggered.connect(partial(self.copy_weight, 'endPoints'))
            target_map_menu.addAction(action_copy_weight)
            action_paste_weight = QtWidgets.QAction(self)
            action_paste_weight.setText('Paste')
            action_paste_weight.setObjectName("actionPasteWeight")
            action_paste_weight.triggered.connect(partial(self.paste_weight, 'endPoints'))
            target_map_menu.addAction(action_paste_weight)
            action_invert_weight = QtWidgets.QAction(self)
            action_invert_weight.setText('Invert')
            action_invert_weight.setObjectName("actionInvertWeight")
            action_invert_weight.triggered.connect(partial(self.invert_weight, 'endPoints'))
            target_map_menu.addAction(action_invert_weight)

        if node.type == 'zMaterial':
            menu.setFixedWidth(125)

            menu.addAction(self.actionDuplicateObject)
            attributes_menu = menu.addMenu('attributes')
            attributes_menu.addAction(self.actionCopyAttrs)
            attributes_menu.addAction(self.actionPasteAttrs)

            menu.addLabel('Maps')
            source_map_menu = menu.addMenu('weight')
            source_map_menu.addAction(self.actionPaintWeight)
            source_map_menu.addSection('')
            action_copy_weight = self.actionCopyWeight
            source_map_menu.addAction(action_copy_weight)
            source_map_menu.addAction(self.actionPasteWeight)
            source_map_menu.addAction(self.actionInvertWeight)

        if node.type == 'zEmbedder':
            menu.addAction(self.actionPaintWeight)
            menu.addSection('')

        if node.type == 'zAttachment':
            attributes_menu = menu.addMenu('attributes')
            attributes_menu.addAction(self.actionCopyAttrs)
            attributes_menu.addAction(self.actionPasteAttrs)

            menu.addAction(self.actionSelectST)

            menu.addLabel('Maps')
            source_map_menu = menu.addMenu('source')
            source_map_menu.addAction(self.actionPaintSource)
            source_map_menu.addSection('')
            action_copy_weight = QtWidgets.QAction(self)
            action_copy_weight.setText('Copy')
            action_copy_weight.setObjectName("actionCopyWeight")
            action_copy_weight.triggered.connect(self.copy_weight)
            source_map_menu.addAction(action_copy_weight)
            source_map_menu.addAction(self.actionPasteWeight)
            source_map_menu.addAction(self.actionInvertWeight)
            source_map_menu.addSection('')
            target_map_menu = menu.addMenu('target')
            target_map_menu.addAction(self.actionPaintTarget)
            target_map_menu.addSection('')
            action_copy_weight = QtWidgets.QAction(self)
            action_copy_weight.setText('Copy')
            action_copy_weight.setObjectName("actionCopyWeight")
            action_copy_weight.triggered.connect(partial(self.copy_weight, None, False))
            target_map_menu.addAction(action_copy_weight)
            action_paste_weight = QtWidgets.QAction(self)
            action_paste_weight.setText('Paste')
            action_paste_weight.setObjectName("actionPasteWeight")
            action_paste_weight.triggered.connect(partial(self.paste_weight, None, False))
            target_map_menu.addAction(action_paste_weight)
            action_invert_weight = QtWidgets.QAction(self)
            action_invert_weight.setText('Invert')
            action_invert_weight.setObjectName("actionInvertWeight")
            action_invert_weight.triggered.connect(partial(self.invert_weight, None, False))
            target_map_menu.addAction(action_invert_weight)
            menu.addSection('')
            proximity_menu = menu.addMenu('Paint By Proximity')
            proximity_menu.installEventFilter(menu)
            prox_widget = model.ProximityWidget()
            actionPaintByProx = QtWidgets.QWidgetAction(proximity_menu)
            actionPaintByProx.setDefaultWidget(prox_widget)
            proximity_menu.addAction(actionPaintByProx)
            proximity_menu.setDefaultAction(actionPaintByProx)

        menu.exec_(self.treeView.viewport().mapToGlobal(position))

    def tree_changed(self, *args):
        """When the tree selection changes this gets executed to select
        corrisponding item in Maya scene.
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
                  | om.MNodeMessage.kAttributeUnlocked):
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

    def copy_weight(self, map_name=None, source=True):
        indexes = self.treeView.selectedIndexes()
        tmp = []
        mesh = None
        for i in indexes:
            node = i.data(model.SceneGraphModel.nodeRole)
            if map_name:
                weights = mc.getAttr("{}.{}".format(node.name, map_name))
                mesh = node.association[0]
            else:
                if source:
                    index = 0
                else:
                    index = 1
                mesh = node.association[index]
                vert_count = mc.polyEvaluate(mesh, v=True)
                weights = mc.getAttr('{}.weightList[{}].weights[0:{}]'.format(
                    node.name, index, vert_count - 1))
            tmp.append(weights)

        self.weights = [sum(i) for i in zip(*tmp)]
        self.weights = [max(min(x, 1.0), 0) for x in self.weights]
        print mesh, self.weights

    def invert_weight(self, map_name=None, source=True):
        indexes = self.treeView.selectedIndexes()[0]
        node = indexes.data(model.SceneGraphModel.nodeRole)
        if map_name:
            weights = mc.getAttr("{}.{}".format(node.name, map_name))
            map_ = node.name + '.' + map_name
            weights = [1.0 - x for x in weights]
            mc.setAttr(map_, weights, type="doubleArray")
        else:
            if source:
                index = 0
            else:
                index = 1
            mesh = node.association[index]
            vert_count = mc.polyEvaluate(mesh, v=True)
            weights = mc.getAttr('{}.weightList[{}].weights[0:{}]'.format(
                node.name, index, vert_count - 1))
            map_ = node.name + '.weightList[%d].weights' % index

            weights = [1.0 - x for x in weights]

            tmp = []
            for w in weights:
                tmp.append(str(w))
            val = ' '.join(tmp)
            cmd = "setAttr " + '%s[0:%d] ' % (map_, len(weights) - 1) + val
            mm.eval(cmd)

    def paste_weight(self, map_name=None, source=True):
        indexes = self.treeView.selectedIndexes()[-1]
        node = indexes.data(model.SceneGraphModel.nodeRole)
        if not map_name:
            if source:
                index = 0
            else:
                index = 1
            map_ = node.name + '.weightList[%d].weights' % index
            tmp = []
            for w in self.weights:
                tmp.append(str(w))
            val = ' '.join(tmp)
            cmd = "setAttr " + '%s[0:%d] ' % (map_, len(self.weights) - 1) + val
            mm.eval(cmd)
        else:
            map_ = node.name + '.' + map_name
            mc.setAttr(map_, self.weights, type="doubleArray")
