""" This is the widget contains tree model and view for the zGeo view.
"""
import logging
import weakref
import zBuilder.builders.ziva as zva

from functools import partial
from maya import cmds
from PySide2 import QtCore, QtWidgets, QtGui
from zBuilder.utils.commonUtils import is_sequence
from zBuilder.utils.vfxUtils import get_zGeo_nodes_by_solverTM
from zBuilder.nodes.base import Base
from ..uiUtils import (nodeRole, longNameRole, SCENE_PANEL_DATA_ATTR_NAME, zGeo_UI_node_types,
                       get_unique_name, get_zSolverTransform_treeitem, is_zsolver_node,
                       get_node_by_index, get_icon_path_from_name)
from .groupNode import GroupNode
from .serialize import is_serialize_data_to_zsolver_node, to_json_string, flatten_tree, to_tree_entry_list, merge_tree_data
from .treeItem import TreeItem, build_scene_panel_tree
from .zGeoContextMenu import create_general_context_menu, create_solver_context_menu, create_group_context_menu
from .zGeoTreeModel import zGeoTreeModel
from .zTreeView import zTreeView

logger = logging.getLogger(__name__)


def is_group_node(node):
    return node.type == "group"


class zGeoWidget(QtWidgets.QWidget):

    def __init__(self, parent=None):
        super(zGeoWidget, self).__init__(parent)
        # member variable declaration and initialization
        self._tmGeo = None
        self._tvGeo = None
        self._wgtComponent_ref = None
        self._builder = None
        self._whole_scene_tree = None  # hold whole scene tree data, with Group nodes
        self._cur_selection_tree = None  # hold current selection tree data, no Group nodes
        self._is_partial_tree_view = False  # Show current tree view status
        self._selected_nodes = list()
        self._pinned_nodes = list()

        self._setup_ui()
        self._setup_actions()

    def _setup_ui(self):
        # Refresh button
        icon = QtGui.QIcon(QtGui.QPixmap(get_icon_path_from_name("refresh")))
        self._btnRefresh = QtWidgets.QPushButton(icon, "Refresh")

        # Tree view
        self._tmGeo = zGeoTreeModel(self)
        self._tvGeo = zTreeView(self)
        self._tvGeo.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self._tvGeo.customContextMenuRequested.connect(self._create_context_menu)
        # selection and move setup
        self._tvGeo.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        self._tvGeo.setDragEnabled(True)
        self._tvGeo.setDragDropMode(QtWidgets.QAbstractItemView.InternalMove)
        self._tvGeo.setAcceptDrops(True)
        self._tvGeo.setDropIndicatorShown(True)
        self._tvGeo.setModel(self._tmGeo)

        self._lytGeo = QtWidgets.QVBoxLayout()
        self._lytGeo.addWidget(self._btnRefresh)
        self._lytGeo.addWidget(self._tvGeo)
        self.setLayout(self._lytGeo)

    def _setup_actions(self):
        self._btnRefresh.clicked.connect(partial(self.reset_builder, False, False))
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

        # create a list of unique maya dag node to view on the component widget
        self._wgtComponent_ref.reset_model(
            self._builder, self._get_unique_node_items(self._selected_nodes, self._pinned_nodes))

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
        # only include unique pinned items from previously pinned and current pinned items.
        # since we switch between full view and partial view, there can be duplicate items
        self._pinned_nodes = self._get_unique_node_items(self._pinned_nodes, pinned_zGeo_nodes)
        # exclude items that have been unpinned
        self._pinned_nodes = self._get_nodes_to_pin(unpinned_nodes)

        # create a list of unique maya dag node to view on the component widget
        self._wgtComponent_ref.reset_model(
            self._builder, self._get_unique_node_items(self._selected_nodes, self._pinned_nodes))

        not_found_nodes = [name for name in node_names if name not in scene_nodes]
        if not_found_nodes:
            cmds.warning("Nodes {} not found. Try to press refresh button.".format(not_found_nodes))

    def _create_context_menu(self, position):
        indexes = self._tvGeo.selectedIndexes()
        if not indexes:
            menu = create_general_context_menu(self)
            menu.exec_(self._tvGeo.viewport().mapToGlobal(position))
            return

        # TODO: Support multiple selection context menu
        if len(indexes) != 1:
            return

        node = indexes[0].data(nodeRole)
        if node.type == "zSolverTransform":
            menu = create_solver_context_menu(self, node)
            menu.exec_(self._tvGeo.viewport().mapToGlobal(position))
        elif node.type == "group":
            menu = create_group_context_menu(self, indexes[0])
            menu.exec_(self._tvGeo.viewport().mapToGlobal(position))

    def _get_expand_item_name(self):
        """ Returns name list of the current expanded items in zGeoTreeView
        """
        return [
            index.data(longNameRole) for index in self._tmGeo.persistentIndexList()
            if self._tvGeo.isExpanded(index)
        ]

    def _get_unique_node_items(self, node_list_1, node_list_2):
        """
        Returns a list of unique node items based on long name
        Args:
            node_list_1 (list): list of nodes
            node_list_2 (list): list of nodes
        """
        node_long_name_dict = {
            node.long_name: node
            for node in list(node_list_1) + list(node_list_2)
        }
        return list(node_long_name_dict.values())

    def _get_nodes_to_pin(self, exclude_nodes):
        """ returns nodes that are pinned but not in 'exclude_nodes'
        """
        node_long_name_dict = {
            node.long_name: node
            for node in self._pinned_nodes if node not in exclude_nodes
        }
        return list(node_long_name_dict.values())

    def _expand_item_by_name(self, name_list):
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

        if self._is_partial_tree_view:
            logger.warning("Can't create group node because current scene is partial view."
                           "Please deselect and click Refresh button.")
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
        if len(solver_list) > 1:
            logger.warning("Can't create group node. Selected items come from different zSolver.")
            return
        if len(solver_list) == 0:
            logger.warning("Please select the items other than zSolver nodes to create the group.")
            return
        assert solver_list[0], "Selected items should only belong to one zSolverTransform node."\
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
        expanded_item_list = self._get_expand_item_name()
        self._tmGeo.group_items(insertion_parent_index, insertion_row, group_node,
                                selected_index_list)
        self._expand_item_by_name(expanded_item_list)

    def _delete_zGeo_treeview_nodes(self):
        """ Delete top level group items in the current selection in the zGeo TreeView.
        Currently we only support delete group items.
        The child group nodes in the selection will not be deleted.
        """
        group_index_to_delete = list(
            filter(lambda index: is_group_node(index.data(nodeRole)),
                   self._tvGeo.selectedIndexes()))

        expanded_item_list = self._get_expand_item_name()
        self._tmGeo.delete_group_items(group_index_to_delete)
        self._expand_item_by_name(expanded_item_list)
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
        self._wgtComponent_ref = weakref.proxy(wgtComponent)

    def reset_builder(self, load_plug_data, clear_state):
        """ Update and merge zBuilder parse result with zGeo Tree View then set the zGeo TreeView.
        This forces a complete redraw of the zGeo TreeView.

        Args:
            load_plug_data(bool): Whether to load json data from solverTM plug.
            clear_state(bool): Whether to clear the existing selected and pinned nodes.
        """

        solverTM_nodes = cmds.ls(type="zSolverTransform", l=True)
        # Clear all the TreeView variables
        if not solverTM_nodes or clear_state:
            self._wgtComponent_ref.reset_model(None, [])
            self._tmGeo.reset_model(None, None, False)
            self._builder = None
            self._whole_scene_tree = None
            self._cur_selection_tree = None
            self._is_partial_tree_view = False
            self._selected_nodes = list()
            self._pinned_nodes = list()
            # Do early return if there's no solver node in the scene
            if not solverTM_nodes:
                return

        self._builder = zva.Ziva()
        self._builder.retrieve_connections()
        self._is_partial_tree_view = bool(cmds.ls(sl=True))
        if self._is_partial_tree_view:
            # Current selection is not None, show partial tree view.
            self._cur_selection_tree = build_scene_panel_tree(
                self._builder, zGeo_UI_node_types + ["zSolver", "zSolverTransform"])[0]
            self._tmGeo.reset_model(self._builder, self._cur_selection_tree,
                                    self._is_partial_tree_view)
            self._wgtComponent_ref.reset_model(None, [])
            self._sync_pin_state_full_to_partial_view()
        else:
            # Reset component view
            if not self._pinned_nodes:
                self._wgtComponent_ref.reset_model(None, [])
            merged_tree = TreeItem(None, Base())
            # Merge each zBuilder solver tree with zGeo view tree
            for solverTM in solverTM_nodes:
                entry_list = None
                if load_plug_data:
                    # Only zSolverTM node after zBuilder v2.0 has this attribute
                    attr_exists = cmds.attributeQuery(SCENE_PANEL_DATA_ATTR_NAME,
                                                      node=solverTM,
                                                      exists=True)
                    if attr_exists:
                        json_string = cmds.getAttr("{}.{}".format(solverTM,
                                                                  SCENE_PANEL_DATA_ATTR_NAME))
                        if json_string:
                            entry_list = to_tree_entry_list(json_string)
                elif self._whole_scene_tree:
                    # Try finding the solver tree and convert it to tree entry list
                    for solverTM_item in self._whole_scene_tree.children:
                        if solverTM_item.data.long_name == solverTM:
                            entry_list = flatten_tree(solverTM_item)
                            break
                else:
                    # Edge case handling:
                    # Scene Panel launches with Ziva objects selected, which enters partial view.
                    # Then user pin some nodes, deselect and refresh.
                    # Now enter the full view, and the self._whole_scene_tree is None.
                    # We need to create a tree view temporarily,
                    # flatten it for the follow-up sync operation.
                    # By doing this, the pinned nodes info are carried to the zGeo tree view.
                    zBuilder_solverTM_nodes = self._builder.get_scene_items(
                        type_filter='zSolverTransform')
                    for zBuilder_node in zBuilder_solverTM_nodes:
                        if zBuilder_node.long_name == solverTM:
                            temp_solverTM_item = build_scene_panel_tree(
                                zBuilder_node,
                                zGeo_UI_node_types + ["zSolver", "zSolverTransform"])[0]
                            entry_list = flatten_tree(temp_solverTM_item)
                            break

                # update pin state to match with partial view when not load plug data,
                # otherwise it clears self._pinned_nodes.
                if entry_list and not load_plug_data:
                    self._sync_pin_state_partial_to_full_view(entry_list)
                # Merge current zBuilder nodes with tree view
                resolved_tree, pinned_node_list = merge_tree_data(
                    get_zGeo_nodes_by_solverTM(self._builder, solverTM), entry_list)
                merged_tree.append_children(resolved_tree)
                self._pinned_nodes.extend(pinned_node_list)

            self._whole_scene_tree = merged_tree
            self._tmGeo.reset_model(self._builder, self._whole_scene_tree,
                                    self._is_partial_tree_view)

        # show expanded view of the tree
        self._tvGeo.expandAll()
        # select item in TreeView that is selected in Maya
        for sel in cmds.ls(sl=True, long=True):
            checked = self._tmGeo.match(self._tmGeo.index(0, 0), longNameRole, sel, -1,
                                        QtCore.Qt.MatchExactly | QtCore.Qt.MatchRecursive)
            for index in checked:
                self._tvGeo.selectionModel().select(index, QtCore.QItemSelectionModel.Select)

    def save(self):
        """ Save the zGeo tree data to solver node respectively.
        It first rebuilds the whole scene, then merge it with current TreeItem data.
        Finally save data to each solver's plug.
        """
        solverTM_nodes = cmds.ls(type="zSolverTransform")
        if not solverTM_nodes:
            logger.debug("No solver node found, skip saving process.")
            return
        if not is_serialize_data_to_zsolver_node():
            return

        # Save data to each solver node's plug.
        # It's fine to save staled zBuilder nodes info.
        # When loading them back, they will be merged with latest tree structure.
        if self._whole_scene_tree:
            for solverTM_item in self._whole_scene_tree.children:
                string_to_save = to_json_string(flatten_tree(solverTM_item))
                cmds.setAttr("{}.{}".format(solverTM_item.data.name, SCENE_PANEL_DATA_ATTR_NAME),
                             string_to_save,
                             type="string")
            logger.info("zGeo tree data saved.")

    def select_group_hierarchy(self, group_index):

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

    def _sync_pin_state_full_to_partial_view(self):
        """ update pin state of partial tree based on whole tree view
        """
        if not self._cur_selection_tree.children:
            return

        selected_nodes = [item.data for item in self._cur_selection_tree.children[0].children]
        nodes_to_pin_item = [
            TreeItem(None, node) for node in self._get_nodes_to_pin(selected_nodes)
        ]
        self._cur_selection_tree.children[0].append_children(nodes_to_pin_item)

        # update node pin states
        for node in self._cur_selection_tree.children[0].children:
            if node.data in self._pinned_nodes:
                node.pin_state = TreeItem.Pinned
            else:
                node.pin_state = TreeItem.Unpinned

    def _sync_pin_state_partial_to_full_view(self, node_list):
        """ update pin state of whole tree based on partial tree view
        Args:
            node_list: partial tree node list
        """
        pinned_node_long_names = [pinned_node.long_name for pinned_node in self._pinned_nodes]

        for node in node_list:
            # skip if it's a group node
            if node.node_type != "group":
                if node.long_name in pinned_node_long_names:
                    node._node_data["pin_state"] = TreeItem.Pinned
                else:
                    node._node_data["pin_state"] = TreeItem.Unpinned
