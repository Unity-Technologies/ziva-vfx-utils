import zBuilder.builders.ziva as zva
import os
import weakref
import logging

from .model import SceneGraphModel
from .zTreeView import zTreeView
from .componentWidget import ComponentWidget
from .groupNode import GroupNode
from .menuBar import ScenePanel2MenuBar
from ..uiUtils import *
from ..utils import *
from maya import cmds
from PySide2 import QtGui, QtWidgets, QtCore
from functools import partial

logger = logging.getLogger(__name__)

DIR_PATH = os.path.dirname(os.path.realpath(__file__)).replace("\\", "/")


def is_group_node(node):
    return node.type == "group"


class ScenePanel2(QtWidgets.QWidget):
    instances = list()
    CONTROL_NAME = 'zfxScenePanel2'
    DOCK_LABEL_NAME = 'Ziva VFX Scene Panel 2'

    @staticmethod
    def delete_instances():
        for ins in ScenePanel2.instances:
            try:
                ins.setParent(None)
                ins.deleteLater()
            except:
                # ignore the fact that the actual parent has already been
                # deleted by Maya...
                pass

            ScenePanel2.instances.remove(ins)
            del ins

    def __init__(self, parent=None, builder=None):
        super(ScenePanel2, self).__init__(parent)

        # let's keep track of our docks so we only have one at a time.
        ScenePanel2.delete_instances()
        ScenePanel2.instances.append(weakref.proxy(self))
        cmds.workspaceControlState(ScenePanel2.CONTROL_NAME, widthHeight=[500, 600])

        self._setup_ui(parent)
        self._setup_model(builder)
        # must be after _setup_model() because assigning model resets item expansion
        self._set_builder(self._builder)
        self._setup_actions()

    def _setup_model(self, builder):
        self._builder = builder or zva.Ziva()
        self._builder.retrieve_connections()

        self._group_count = 0
        self._zGeo_treemodel = SceneGraphModel(self._builder, self)
        self._tvGeo.setModel(self._zGeo_treemodel)

    def _set_builder(self, builder):
        """
        This builds and/or resets the tree given a builder.
        The builder is a zBuilder object that the tree is built from.
        If None is passed it uses the scene selection to build a new builder.
        This forces a complete redraw of the ui tree.

        Args:
            builder (:obj:`obj`): The zBuilder builder to build tree from.
        """

        if not builder:
            # reset builder
            self._builder = zva.Ziva()
            self._builder.retrieve_connections()
            builder = self._builder

        self._zGeo_treemodel.reset_model(builder)

        # show expanded view of the tree
        self._tvGeo.expandAll()

        # select item in TreeView that is selected in Maya
        sel = cmds.ls(sl=True, long=True)
        if sel:
            checked = self._zGeo_treemodel.match(self._zGeo_treemodel.index(0, 0), longNameRole,
                                                 sel[0], -1,
                                                 QtCore.Qt.MatchExactly | QtCore.Qt.MatchRecursive)
            for index in checked:
                self._tvGeo.selectionModel().select(index, QtCore.QItemSelectionModel.Select)

    def _setup_ui(self, parent):
        self.toolbarCreate = QtWidgets.QToolBar(self)
        self.toolbarCreate.setWindowTitle("Create")
        self.toolbarCreate.setIconSize(QtCore.QSize(27, 27))
        self.toolbarCreate.setObjectName("toolBarCreate")

        lytToolbarCreate = QtWidgets.QVBoxLayout()
        labelCreate = QtWidgets.QLabel("Create")
        labelCreate.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        lytToolbarCreate.addWidget(labelCreate)
        lytToolbarCreate.addWidget(self.toolbarCreate)

        self.toolbarAdd = QtWidgets.QToolBar(self)
        self.toolbarAdd.setIconSize(QtCore.QSize(27, 27))
        self.toolbarAdd.setObjectName("toolBarAdd")

        lytToolbarAdd = QtWidgets.QVBoxLayout()
        labelAdd = QtWidgets.QLabel("Add")
        labelAdd.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        lytToolbarAdd.addWidget(labelAdd)
        lytToolbarAdd.addWidget(self.toolbarAdd)

        self.toolbarEdit = QtWidgets.QToolBar(self)
        self.toolbarEdit.setIconSize(QtCore.QSize(27, 27))
        self.toolbarEdit.setObjectName("toolBarEdit")

        lytToolbarEdit = QtWidgets.QVBoxLayout()
        labelEdit = QtWidgets.QLabel("Edit")
        labelEdit.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        lytToolbarEdit.addWidget(labelEdit)
        lytToolbarEdit.addWidget(self.toolbarEdit)

        lytToolbar = QtWidgets.QHBoxLayout()
        lytToolbar.addLayout(lytToolbarCreate)
        lytToolbar.addLayout(lytToolbarAdd)
        lytToolbar.addLayout(lytToolbarEdit)

        self._tvGeo = zTreeView(self)
        self._tvGeo.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self._tvGeo.customContextMenuRequested.connect(self.open_menu)
        self._tvGeo.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)

        lytGeo = QtWidgets.QVBoxLayout()
        lytGeo.addWidget(self._tvGeo)
        grpGeo = QtWidgets.QGroupBox("Scene Panel")
        grpGeo.setLayout(lytGeo)

        self._wgtComponent = ComponentWidget(self)
        lytComponent = QtWidgets.QVBoxLayout()
        lytComponent.addWidget(self._wgtComponent)
        grpComponent = QtWidgets.QGroupBox("Component")
        grpComponent.setLayout(lytComponent)

        splTreeView = QtWidgets.QSplitter(self)
        splTreeView.addWidget(grpGeo)
        splTreeView.addWidget(grpComponent)

        lytMenuBar = ScenePanel2MenuBar(self)

        lytMenuBarContainer = QtWidgets.QHBoxLayout()
        lytMenuBarContainer.addWidget(lytMenuBar)
        lytMenuBarContainer.setAlignment(lytMenuBar, QtCore.Qt.AlignRight)

        lytTwoPanel = QtWidgets.QVBoxLayout()
        lytTwoPanel.addLayout(lytMenuBarContainer)
        lytTwoPanel.addLayout(lytToolbar)
        lytTwoPanel.addWidget(splTreeView)

        with open(os.path.join(DIR_PATH, "style.css"), "r") as f:
            style_sheet = f.read()
            parent.setStyleSheet(style_sheet)

        lytMain = parent.layout()
        lytMain.addLayout(lytTwoPanel)

    def _setup_actions(self):
        self._setup_toolbar_action('zSolver', 'Create zSolver', 'actionCreateSolver',
                                   self.toolbarCreate, create_zSolver)
        self._setup_toolbar_action('zTissue', 'Create zTissue', 'actionCreateTissue',
                                   self.toolbarCreate, create_zTissue)
        self._setup_toolbar_action('zBone', 'Create zBone', 'actionCreateBone', self.toolbarCreate,
                                   create_zBone)
        self._setup_toolbar_action('zCloth', 'Create zCloth', 'actionCreateCloth',
                                   self.toolbarCreate, create_zCloth)
        self._setup_toolbar_action('zAttachmentPlus',
                                   'Create zAttachment: select source vertices and target object',
                                   'actionCreateAttachment', self.toolbarCreate, create_zAttachment)
        self._setup_toolbar_action('create-group-plus', 'Create group', 'actionCreateGroup',
                                   self.toolbarCreate, self._create_group)
        self._setup_toolbar_action('zMaterial', 'Add zMaterial: select tissue geometry',
                                   'actionAddMaterial', self.toolbarAdd, add_zMaterial)
        self._setup_toolbar_action('zFiber', 'Add zFiber: select tissue geometry', 'actionAddFiber',
                                   self.toolbarAdd, add_zFiber)
        self._setup_toolbar_action('subtissue',
                                   'Add zSubtissue: select parent and then child tissue mesh',
                                   'actionAddSubtissue', self.toolbarAdd, add_zSubtissue)
        self._setup_toolbar_action('zRestShape',
                                   'Add zRestShape: select tissue mesh and then restShape mesh',
                                   'actionAddRestShape', self.toolbarAdd, add_zRestShape)
        self._setup_toolbar_action('zLineOfAction', 'Add zLineOfAction: select zFiber and curve',
                                   'actionAddLineOfAction', self.toolbarAdd, add_zLineOfAction)
        self._setup_toolbar_action('curve', 'Add Fiber Curve: select zFiber', 'actionAddFiberCurve',
                                   self.toolbarAdd, add_fiberCurve)
        self._setup_toolbar_action('zRivetToBone',
                                   'Add zRivetToBone: select target curve vertex and bone mesh',
                                   'actionAddRivetToBone', self.toolbarAdd, add_rivetToBone)
        self._setup_toolbar_action('zCache', 'Add zCache', 'actionAddCache', self.toolbarAdd,
                                   add_cache)
        self._setup_refresh_action()

        self._tvGeo.selectionModel().selectionChanged.connect(self.on_tvGeo_selectionChanged)
        self._tvGeo.installEventFilter(self)

    def _setup_toolbar_action(self, name, text, objectName, toolbar, slot):
        icon_path = get_icon_path_from_name(name)
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(icon_path))
        action = QtWidgets.QAction(self)
        action.setText(text)
        action.setIcon(icon)
        action.setObjectName(objectName)
        action.triggered.connect(slot)
        toolbar.addAction(action)

    def _create_group(self):
        treemodel_root = self._zGeo_treemodel.index(0, 0)

        # tree item selection
        selected_nodes = []
        selectedIndexList = self._tvGeo.selectedIndexes()
        if selectedIndexList:
            selected_nodes = [x.data(nodeRole) for x in selectedIndexList]

        # add group end of the top tree. TODO: This will change with nested group.
        self._group_count = self._group_count + 1 # TODO: temporary method for unique name. Update with proper check.
        group_name = "Group" + str(self._group_count)
        group_node = GroupNode(group_name)

        # add selected nodes as children of newly created group node and remove from top tree.
        row_count = self._zGeo_treemodel.rowCount(treemodel_root)
        if self._zGeo_treemodel.insertRow(row_count, treemodel_root):
            new_group_index = self._zGeo_treemodel.index(row_count, 0, treemodel_root)
            self._zGeo_treemodel.setData(new_group_index, group_node, nodeRole)

            for node in selected_nodes:
                new_row_count = self._zGeo_treemodel.rowCount(new_group_index)
                if self._zGeo_treemodel.insertRow(new_row_count, new_group_index):
                    new_node_index = self._zGeo_treemodel.index(new_row_count, 0, new_group_index)
                    self._zGeo_treemodel.setData(new_node_index, node, nodeRole)
                    match_index = self._zGeo_treemodel.match(self._zGeo_treemodel.index(0, 0), longNameRole,
                                                 node.long_name, 1,
                                                 QtCore.Qt.MatchExactly | QtCore.Qt.MatchRecursive)
                    # TODO: add long name for GroupNode
                    self._zGeo_treemodel.removeRow(match_index[0].row(), match_index[0].parent())
                else:
                    logger.warning("Failed to insert row to TreeView model for {}!", group_name)
        else:
            logger.warning("Failed to insert row to TreeView model!")

    def _setup_refresh_action(self):
        refresh_path = get_icon_path_from_name('refresh')
        refresh_icon = QtGui.QIcon()
        refresh_icon.addPixmap(QtGui.QPixmap(refresh_path))
        self.actionRefresh = QtWidgets.QAction(self)
        self.actionRefresh.setText('Refresh')
        self.actionRefresh.setIcon(refresh_icon)
        self.actionRefresh.setObjectName("actionRefresh")
        self.actionRefresh.triggered.connect(self._set_builder)
        self.toolbarEdit.addAction(self.actionRefresh)

    def on_tvGeo_selectionChanged(self, selected, deselected):
        """
        When the tree selection changes this gets executed to select
        corresponding item in Maya scene.
        """
        selection_list = self._tvGeo.selectedIndexes()
        if selection_list:
            nodes = [x.data(nodeRole) for x in selection_list]
            non_group_nodes = filter(lambda n: not is_group_node(n), nodes)
            node_names = [x.long_name for x in nodes]
            # find nodes that exist in the scene
            scene_nodes = cmds.ls(node_names, l=True)
            if scene_nodes:
                cmds.select(scene_nodes)

            # filter non-exist nodes and solver nodes
            selected_nodes = list(
                filter(lambda n: (n.long_name in scene_nodes) and not n.type.startswith("zSolver"),
                       non_group_nodes))

            self._wgtComponent.reset_model(self._builder, selected_nodes)

            not_found_nodes = [name for name in node_names if name not in scene_nodes]
            if not_found_nodes:
                cmds.warning(
                    "Nodes {} not found. Try to press refresh button.".format(not_found_nodes))

    def get_expanded(self):
        """
        Returns: array of item names that are currently expanded in zGeoTreeView
        """
        # store currently expanded items
        expanded = []
        for index in self._zGeo_treemodel.persistentIndexList():
            if self._tvGeo.isExpanded(index):
                expanded.append(index.data(longNameRole))

        return expanded

    def expand(self, names):
        """
        Args:
            names (list): names to expand in zGeoTreeView
        """
        # collapseAll added in case refreshing of zGeoTreeView needed
        # otherwise new items might not be displayed ( Qt bug )
        self._tvGeo.collapseAll()
        for name in names:
            indexes = self._zGeo_treemodel.match(self._zGeo_treemodel.index(0, 0), longNameRole,
                                                 name, -1,
                                                 QtCore.Qt.MatchExactly | QtCore.Qt.MatchRecursive)
            for index in indexes:
                self._tvGeo.expand(index)

    def open_menu(self, position):
        """
        Generates menu for 'zSolver' item.

        If there are more than one object selected in UI a menu does not appear.
        """
        indexes = self._tvGeo.selectedIndexes()
        if len(indexes) != 1:
            return

        node = indexes[0].data(nodeRole)
        if node.type == "zSolverTransform":
            menu = QtWidgets.QMenu(self)
            menu.setToolTipsVisible(True)
            method = self.open_solver_menu
            method(menu, node)
            menu.exec_(self._tvGeo.viewport().mapToGlobal(position))

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
        menu.addSeparator()
        self.add_info_action(menu)
        self.add_set_default_action(menu)

    def add_info_action(self, menu):
        action = QtWidgets.QAction(self)
        action.setText('Info')
        action.setToolTip('Outputs solver statistics.')
        action.triggered.connect(self.run_info_command)
        menu.addAction(action)

    def run_info_command(self):
        sel = cmds.ls(sl=True)
        cmdOut = cmds.ziva(sel[0], i=True)  # only allow one
        print(cmdOut)  #print result in Maya

    def add_set_default_action(self, menu):
        action = QtWidgets.QAction(self)
        action.setText('Set Default')
        action.setToolTip(
            'Set the default solver to the solver inferred from selection. The default solver is used in case of solver ambiguity when there are 2 or more solvers in the scene.'
        )
        sel = cmds.ls(sl=True)
        defaultSolver = cmds.zQuery(defaultSolver=True)
        if defaultSolver and defaultSolver[0] == sel[0]:
            action.setEnabled(False)
        action.triggered.connect(lambda: self.run_set_default_command(sel[0]))
        menu.addAction(action)

    def run_set_default_command(self, sel):
        cmdOut = cmds.ziva(sel, defaultSolver=True)  # only allow one
        print(cmdOut)  #print result in Maya

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

    def _delete_zGeo_treeview_nodes(self):
        """ Delete current selected nodes in zGeo treeview.
        Currently we only support delete one item each
        """
        selection_list = self._tvGeo.selectedIndexes()
        # TODO: Add support for multiple nodes deletion
        if len(selection_list) != 1:
            return

        cur_sel = selection_list[0]
        node = cur_sel.data(nodeRole)
        if is_group_node(node):
            self._zGeo_treemodel.removeRow(cur_sel.row(), cur_sel.parent())
        # TODO: Add support for zGeo node delete


    # Override
    def eventFilter(self, obj, event):
        """ Handle key press event for treeviews
        """
        if event.type() == QtCore.QEvent.KeyPress:
            # Delete operation on zGeo tree view
            if (obj is self._tvGeo) and (event.key() == QtCore.Qt.Key_Delete):
                self._delete_zGeo_treeview_nodes()
                return True

        # standard event processing
        return QtCore.QObject.eventFilter(self, obj, event)

# Show window with docking ability
def run():
    return dock_window(ScenePanel2)
