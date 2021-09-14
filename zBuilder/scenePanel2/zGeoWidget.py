import zBuilder.builders.ziva as zva
import logging
import weakref

from .zGeoTreeModel import zGeoTreeModel
from .zTreeView import zTreeView
from .groupNode import GroupNode
from .serialize import is_serialize_data_to_zsolver_node, json_to_string, serialize_tree_model
from ..uiUtils import nodeRole, longNameRole
from ..uiUtils import get_unique_name, get_zSolverTransform_treeitem, is_zsolver_node, get_node_by_index
from ..commonUtils import is_sequence
from PySide2 import QtCore, QtWidgets
from maya import cmds
from functools import partial
""" This is the widget contains tree model and view for the zGeo view.
"""

logger = logging.getLogger(__name__)


def is_group_node(node):
    return node.type == "group"


class zGeoWidget(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super(zGeoWidget, self).__init__(parent)
        # member variable declaration and initialization
        self._tmGeo = None
        self._tvGeo = None
        self._wgtComponentRef = None
        self._builder = None
        self._selected_nodes = list()
        self._pinned_nodes = list()

        self._setup_ui()
        self._setup_actions()

    def _setup_ui(self):
        self._tmGeo = zGeoTreeModel(self)

        self._tvGeo = zTreeView(self)
        self._tvGeo.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self._tvGeo.customContextMenuRequested.connect(self.open_menu)
        # selection and move setup
        self._tvGeo.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        self._tvGeo.setDragEnabled(True)
        self._tvGeo.setDragDropMode(QtWidgets.QAbstractItemView.InternalMove)
        self._tvGeo.setAcceptDrops(True)
        self._tvGeo.setDropIndicatorShown(True)
        self._tvGeo.setModel(self._tmGeo)

        self._lytGeo = QtWidgets.QVBoxLayout(self)
        self._lytGeo.addWidget(self._tvGeo)
        self.setLayout(self._lytGeo)

    def _setup_actions(self):
        self._tvGeo.selectionModel().selectionChanged.connect(self._on_tvGeo_selectionChanged)
        self._tvGeo.installEventFilter(self)

    def _on_tvGeo_selectionChanged(self, selected, deselected):
        """
        When the tree selection changes this gets executed to select
        corresponding item in Maya scene.
        """
        selection_list = self._tvGeo.selectedIndexes()
        if selection_list:
            nodes = [x.data(nodeRole) for x in selection_list]
            non_group_nodes = list(filter(lambda n: not is_group_node(n), nodes))
            node_names = [x.long_name for x in non_group_nodes]
            # find nodes that exist in the scene
            scene_nodes = cmds.ls(node_names, l=True)
            if scene_nodes:
                cmds.select(scene_nodes)

            # filter non-exist nodes and solver nodes
            self._selected_nodes = list(
                filter(lambda n: (n.long_name in scene_nodes) and not is_zsolver_node(n),
                       non_group_nodes))

            not_found_nodes = [name for name in node_names if name not in scene_nodes]
            if not_found_nodes:
                cmds.warning(
                    "Nodes {} not found. Try to press refresh button.".format(not_found_nodes))
        else:
            self._selected_nodes = []

        self._wgtComponentRef.reset_model(self._builder,
                                          list(set(self._selected_nodes) | set(self._pinned_nodes)))

    def _on_tvGeo_pinStateChanged(self, item_list):
        """ Update component TreeView when zGeo TreeView item's pin state changed.
        """
        def get_all_zGeo_items(item_list):
            """ Given TreeItem(s), return all TreeItem that is zGeo node type
            """
            if not is_sequence(item_list):
                item_list = [item_list]

            zGeo_items = []
            for item in item_list:
                if is_group_node(item.data):
                    zGeo_items.extend(get_all_zGeo_items(item.children))
                else:
                    assert len(item.children
                               ) == 0, "Non group node has child node. Need revamp code logic."
                    zGeo_items.append(item)

            return zGeo_items

        zGeo_treeItems = get_all_zGeo_items(item_list)
        node_names = [item.data.long_name for item in zGeo_treeItems]
        # find nodes that exist in the scene, filter non-exist nodes
        scene_nodes = cmds.ls(node_names, l=True)
        valid_zGeo_treeItems = list(
            filter(lambda n: (n.data.long_name in scene_nodes), zGeo_treeItems))
        pinned_zGeo_treeItems = list(
            filter(lambda n: QtCore.Qt.Checked == n.pin_state, valid_zGeo_treeItems))
        unpinned_zGeo_treeItems = set(valid_zGeo_treeItems) - set(pinned_zGeo_treeItems)

        # Update the pinned tree items
        pinned_zGeo_nodes = [item.data for item in pinned_zGeo_treeItems]
        unpinned_nodes = [item.data for item in unpinned_zGeo_treeItems]
        # Be careful about set operator precedence, the "-" has higher precedence than "|".
        # Refer to https://stackoverflow.com/questions/54735175/set-operator-precedence
        self._pinned_nodes = list((set(self._pinned_nodes) | set(pinned_zGeo_nodes)) -
                                  set(unpinned_nodes))
        self._wgtComponentRef.reset_model(self._builder,
                                          list(set(self._selected_nodes) | set(self._pinned_nodes)))

        not_found_nodes = [name for name in node_names if name not in scene_nodes]
        if not_found_nodes:
            cmds.warning("Nodes {} not found. Try to press refresh button.".format(not_found_nodes))

    # Begin zGeo TreeView pop-up menu
    def open_menu(self, position):
        """
        Generates menu for zSolver item.

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
        elif node.type == "group":
            menu = QtWidgets.QMenu(self)
            menu.setToolTipsVisible(True)
            method = self.open_group_node_menu
            method(menu, indexes[0])
            menu.exec_(self._tvGeo.viewport().mapToGlobal(position))

    def open_solver_menu(self, menu, node):
        solver_transform = node
        solver = node.children[0]

        self.add_zsolver_menu_action(menu, solver_transform, "Enable", "enable")
        self.add_zsolver_menu_action(menu, solver, "Collision Detection", "collisionDetection")
        self.add_zsolver_menu_action(menu, solver, "Show Bones", "showBones")
        self.add_zsolver_menu_action(menu, solver, "Show Tet Meshes", "showTetMeshes")
        self.add_zsolver_menu_action(menu, solver, "Show Muscle Fibers", "showMuscleFibers")
        self.add_zsolver_menu_action(menu, solver, "Show Attachments", "showAttachments")
        self.add_zsolver_menu_action(menu, solver, "Show Collisions", "showCollisions")
        self.add_zsolver_menu_action(menu, solver, "Show Materials", "showMaterials")
        menu.addSeparator()
        self.add_info_action(menu)
        self.add_set_default_action(menu)

    def add_info_action(self, menu):
        action = QtWidgets.QAction(self)
        action.setText("Info")
        action.setToolTip("Outputs solver statistics.")
        action.triggered.connect(self.run_info_command)
        menu.addAction(action)

    def run_info_command(self):
        sel = cmds.ls(sl=True)
        cmdOut = cmds.ziva(sel[0], i=True)  # only allow one
        print(cmdOut)  #print result in Maya

    def add_set_default_action(self, menu):
        action = QtWidgets.QAction(self)
        action.setText("Set Default")
        action.setToolTip(
            "Set the default solver to the solver inferred from selection."\
            "The default solver is used in case of solver ambiguity when there are 2 or more solvers in the scene."
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
        action.setChecked(node.attrs[attr]["value"])
        action.changed.connect(partial(self.toggle_attribute, node, attr))
        menu.addAction(action)

    def toggle_attribute(self, node, attr):
        value = node.attrs[attr]["value"]
        if isinstance(value, bool):
            value = not value
        elif isinstance(value, int):
            value = 1 - value
        else:
            cmds.error("Attribute is not bool/int: {}.{}".format(node.name, attr))
            return
        node.attrs[attr]["value"] = value
        cmds.setAttr("{}.{}".format(node.long_name, attr), value)

    def _select_group_hierarchy(self, group_index):
        def get_all_zGeo_indices(index_list):
            """ Given QModelIndex list, return all child QModelIndex that is zGeo node type
            """
            if not is_sequence(index_list):
                index_list = [index_list]

            zGeo_indices = []
            for index in index_list:
                treeitem = get_node_by_index(index, None)
                assert treeitem, "Can't get TreeItem through QModelIndex."

                if is_group_node(treeitem.data):
                    # Collect all child QModelIndex and recursively process
                    model = index.model()
                    child_index_list = [
                        model.index(i, 0, index) for i in range(model.rowCount(index))
                    ]
                    zGeo_indices.extend(get_all_zGeo_indices(child_index_list))
                else:
                    assert len(treeitem.children
                               ) == 0, "Non group node has child node. Need revamp code logic."
                    zGeo_indices.append(index)
            return zGeo_indices

        zGeo_indices = get_all_zGeo_indices(group_index)
        for index in zGeo_indices:
            self._tvGeo.selectionModel().select(index, QtCore.QItemSelectionModel.Select)

    def open_group_node_menu(self, menu, group_index):
        action = QtWidgets.QAction(self)
        action.setText("Select Hierarchy")
        action.triggered.connect(partial(self._select_group_hierarchy, group_index))
        menu.addAction(action)

    # End zGeo TreeView pop-up menu

    def get_expand_item_name(self):
        """ Returns name list of the current expanded items in zGeoTreeView
        """
        return [
            index.data(longNameRole) for index in self._tmGeo.persistentIndexList()
            if self._tvGeo.isExpanded(index)
        ]

    def expand_item_by_name(self, name_list):
        """
        Args:
            name_list (list(str)): names to expand in zGeoTreeView
        """
        # collapseAll added in case refreshing of zGeoTreeView needed
        # otherwise new items might not be displayed ( Qt bug )
        self._tvGeo.collapseAll()
        for name in name_list:
            indexes = self._tmGeo.match(self._tmGeo.index(0, 0), longNameRole, name, -1,
                                        QtCore.Qt.MatchExactly | QtCore.Qt.MatchRecursive)
            for index in indexes:
                self._tvGeo.expand(index)

    def create_group(self):
        """ Create Group node according to current selection.
        It follow the Maya's group node creation logic:
        - If selection is empty, append a new empty Group node at the end of top level;
        - If the selection has same parent, insert a new Group node at the last item position;
        - If the selection has different parent, append a new Group at the end of top level;
        """
        root_index = QtCore.QModelIndex()
        if self._tmGeo.rowCount(root_index) == 0:
            logger.warning("Can't create Group node since no zSolver node exists.")
            return

        # Exclude zSolver* items
        selected_index_list = list(
            filter(lambda index: not is_zsolver_node(index.data(nodeRole)),
                   self._tvGeo.selectedIndexes()))
        # Make sure all select items come from same zSolverTransform node.
        # Otherwise, do early return.
        solver_list = list(
            set([
                get_zSolverTransform_treeitem(get_node_by_index(index, None))
                for index in selected_index_list
            ]))
        if len(solver_list) != 1:
            logger.warning("Can't create group node. Selected items come from different zSolver.")
            return
        assert solver_list[0], "Selected items belong to different zSolverTransform nodes."\
            "There's bug in the code logic."

        # Find zSolverTransform index through TreeItem
        insertion_parent_index = None
        for rowIdx in range(self._tmGeo.rowCount(root_index)):
            cur_index = self._tmGeo.index(rowIdx, 0, root_index)
            if get_zSolverTransform_treeitem(get_node_by_index(cur_index, None)) == solver_list[0]:
                insertion_parent_index = cur_index
        assert insertion_parent_index, "Can't find solver index through zSolverTransform TreeItem."

        insertion_row = self._tmGeo.rowCount(insertion_parent_index)
        if selected_index_list:
            # Decide insertion position
            all_items_have_same_parent = all(index.parent() == selected_index_list[0].parent()
                                             for index in selected_index_list)
            if all_items_have_same_parent:
                # Get common parent index as insertion parent
                insertion_parent_index = selected_index_list[0].parent()
                # Get first row index as insertion point
                insertion_row = min(map(lambda index: index.row(), selected_index_list))

        # Create Group node with proper name
        names_to_check = []
        for rowIdx in range(self._tmGeo.rowCount(insertion_parent_index)):
            names_to_check.append(
                self._tmGeo.index(rowIdx, 0, insertion_parent_index).data(QtCore.Qt.DisplayRole))
        group_name = get_unique_name("Group1", names_to_check)
        group_node = GroupNode(group_name)
        expanded_item_list = self.get_expand_item_name()
        self._tmGeo.group_items(insertion_parent_index, insertion_row, group_node,
                                selected_index_list)
        self.expand_item_by_name(expanded_item_list)

    def _delete_zGeo_treeview_nodes(self):
        """ Delete top level group items in the current selection in the zGeo TreeView.
        Currently we only support delete group items.
        The child group nodes in the selection will not be deleted.
        """
        group_index_to_delete = list(
            filter(lambda index: is_group_node(index.data(nodeRole)),
                   self._tvGeo.selectedIndexes()))

        expanded_item_list = self.get_expand_item_name()
        self._tmGeo.delete_group_items(group_index_to_delete)
        self.expand_item_by_name(expanded_item_list)
        # TODO: Add support for zGeo node deletion

    # Override
    def eventFilter(self, obj, event):
        """ Handle key press event for TreeViews
        """
        if event.type() == QtCore.QEvent.KeyPress:
            # Delete operation on zGeo tree view
            if (obj is self._tvGeo) and (event.key() == QtCore.Qt.Key_Delete):
                self._delete_zGeo_treeview_nodes()
                return True

            # group creation
            elif (obj is self._tvGeo) and (event.key() == QtCore.Qt.Key_G) \
                and (event.modifiers() == QtCore.Qt.ControlModifier):
                self.create_group()
                return True

        # standard event processing
        return QtCore.QObject.eventFilter(self, obj, event)

    # Public functions
    def set_component_widget(self, wgtComponent):
        self._wgtComponentRef = weakref.proxy(wgtComponent)

    def reset_builder(self):
        """ Build and set the zGeo TreeView. This forces a complete redraw of the zGeo TreeView.
        """
        solver_nodes = cmds.ls(type="zSolver")
        if not solver_nodes:
            # Clear the TreeView and do early return if there's no solver node in the scene
            self._tmGeo.reset_model(None)
            self._wgtComponentRef.reset_model(None, [])
            return

        self._builder = zva.Ziva()
        self._builder.retrieve_connections()
        self._tmGeo.reset_model(self._builder)

        # show expanded view of the tree
        self._tvGeo.expandAll()

        # select item in TreeView that is selected in Maya
        sel = cmds.ls(sl=True, long=True)
        if sel:
            checked = self._tmGeo.match(self._tmGeo.index(0, 0), longNameRole, sel[0], -1,
                                        QtCore.Qt.MatchExactly | QtCore.Qt.MatchRecursive)
            for index in checked:
                self._tvGeo.selectionModel().select(index, QtCore.QItemSelectionModel.Select)

    def save(self):
        solver_nodes = cmds.ls(type="zSolver")
        if is_serialize_data_to_zsolver_node():
            cmds.select(cl=True)
            builder = zva.Ziva()
            builder.retrieve_connections()
            # TODO: resolve conflict
            root_node = self._zGeo_treemodel.root_node()
            for node in root_node.children:
                string_to_save = json_to_string(serialize_tree_model(node))
                cmds.setAttr("{}.scenePanelSerializedData".format(node.data.name),
                             string_to_save,
                             type="string")
            logger.info("zGeo TreeView data saved.")
