import zBuilder.builders.ziva as zva
import os
import weakref
import logging

from .model import SceneGraphModel, zGeoFilterProxyModel
from .zGeoView import zGeoTreeView
from .componentWidget import SelectedGeoListModel
from zBuilder.uiUtils import nodeRole, longNameRole, dock_window, get_icon_path_from_name
from maya import cmds
from PySide2 import QtGui, QtWidgets, QtCore
from functools import partial

logger = logging.getLogger(__name__)

DIR_PATH = os.path.dirname(os.path.realpath(__file__)).replace("\\", "/")


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

        self._sceneGraphModel = SceneGraphModel(self._builder, self)
        self._proxy_model = zGeoFilterProxyModel()
        self._proxy_model.setSourceModel(self._sceneGraphModel)
        self._proxy_model.setDynamicSortFilter(True)
        self._proxy_model.setFilterCaseSensitivity(QtCore.Qt.CaseInsensitive)
        self._tvGeo.setModel(self._proxy_model)

        self._selectedGeoModel = SelectedGeoListModel(self)
        self._lvComponent.setModel(self._selectedGeoModel)

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

        self._sceneGraphModel.beginResetModel()
        self._sceneGraphModel.builder = builder
        self._sceneGraphModel.endResetModel()

        # show expanded view of the tree
        self._tvGeo.expandAll()

        # select item in treeview that is selected in maya
        sel = cmds.ls(sl=True, long=True)
        if sel:
            checked = self._proxy_model.match(self._proxy_model.index(0, 0), longNameRole, sel[0],
                                              -1, QtCore.Qt.MatchExactly | QtCore.Qt.MatchRecursive)
            for index in checked:
                self._tvGeo.selectionModel().select(index, QtCore.QItemSelectionModel.Select)

    def _setup_ui(self, parent):
        self.toolbar = QtWidgets.QToolBar(self)
        self.toolbar.setIconSize(QtCore.QSize(27, 27))
        self.toolbar.setObjectName("toolBar")
        lytToolbar = QtWidgets.QHBoxLayout()
        lytToolbar.addWidget(self.toolbar)

        self._tvGeo = zGeoTreeView(self)
        self._tvGeo.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self._tvGeo.customContextMenuRequested.connect(self.open_menu)
        self._tvGeo.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        self._tvGeo.setAlternatingRowColors(True)
        self._tvGeo.setIndentation(15)
        # changing header size
        # this used to create some space between left/top side of the tree view and it items
        # "razzle dazzle" but the only way I could handle that
        # height - defines padding from top
        # offset - defines padding from left
        # opposite value of offset should be applied in view.py in drawBranches method
        header = self._tvGeo.header()
        header.setOffset(-zGeoTreeView.offset)
        header.setFixedHeight(10)

        lytGeo = QtWidgets.QVBoxLayout()
        lytGeo.addWidget(self._tvGeo)
        grpGeo = QtWidgets.QGroupBox("Scene Panel")
        grpGeo.setLayout(lytGeo)

        self._lvComponent = QtWidgets.QListView(self)
        self._lvComponent.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        lytComponent = QtWidgets.QVBoxLayout()
        lytComponent.addWidget(self._lvComponent)
        grpComponent = QtWidgets.QGroupBox("Component")
        grpComponent.setLayout(lytComponent)

        splTreeView = QtWidgets.QSplitter(self)
        splTreeView.addWidget(grpGeo)
        splTreeView.addWidget(grpComponent)

        lytTwoPanel = QtWidgets.QVBoxLayout()
        lytTwoPanel.addLayout(lytToolbar)
        lytTwoPanel.addWidget(splTreeView)

        with open(os.path.join(DIR_PATH, "style.css"), "r") as f:
            style_sheet = f.read()
            parent.setStyleSheet(style_sheet)

        lytMain = parent.layout()
        lytMain.addLayout(lytTwoPanel)

    def _setup_actions(self):
        refresh_path = get_icon_path_from_name('refresh')
        refresh_icon = QtGui.QIcon()
        refresh_icon.addPixmap(QtGui.QPixmap(refresh_path), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.actionRefresh = QtWidgets.QAction(self)
        self.actionRefresh.setText('Refresh')
        self.actionRefresh.setIcon(refresh_icon)
        self.actionRefresh.setObjectName("actionRefresh")
        self.actionRefresh.triggered.connect(self._set_builder)
        self.toolbar.addAction(self.actionRefresh)

        self._tvGeo.selectionModel().selectionChanged.connect(self.on_tvGeo_selectionChanged)

    def on_tvGeo_selectionChanged(self, selected, deselected):
        """
        When the tree selection changes this gets executed to select
        corresponding item in Maya scene.
        """
        selectedIndexList = self._tvGeo.selectedIndexes()
        if selectedIndexList:
            nodes = [x.data(nodeRole) for x in selectedIndexList]
            node_names = [x.long_name for x in nodes]
            # find nodes that exist in the scene
            scene_nodes = cmds.ls(node_names, l=True)
            if scene_nodes:
                cmds.select(scene_nodes)

            # filter non-exist nodes and solver nodes
            selected_nodes = list(
                filter(lambda n: (n.long_name in scene_nodes) and not n.type.startswith('zSolver'),
                       nodes))
            self._selectedGeoModel.setNewSelection(selected_nodes)

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
        for index in self._proxy_model.persistentIndexList():
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
            indexes = self._proxy_model.match(self._proxy_model.index(0, 0), longNameRole, name, -1,
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
        if node.type == 'zSolverTransform':
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
        cmdOut = cmds.ziva(sel[0], i=True) # only allow one
        print(cmdOut) #print result in maya

    def add_set_default_action(self, menu):
        action = QtWidgets.QAction(self)
        action.setText('Set Default')
        action.setToolTip('Set the default solver to the solver inferred from selection. The default solver is used in case of solver ambiguity when there are 2 or more solvers in the scene.')
        sel = cmds.ls(sl=True)
        defaultSolver = cmds.zQuery(defaultSolver=True)
        if defaultSolver and defaultSolver[0] == sel[0]:
            action.setEnabled(False)
        action.triggered.connect(lambda: self.run_set_default_command(sel[0]))
        menu.addAction(action)

    def run_set_default_command(self, sel):
        cmdOut = cmds.ziva(sel, defaultSolver=True) # only allow one
        print(cmdOut) #print result in maya

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

# Show window with docking ability
def run():
    return dock_window(ScenePanel2)
