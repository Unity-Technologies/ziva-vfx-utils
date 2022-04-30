import zBuilder.builders.ziva as zva

from maya import cmds
from vfx_test_case import VfxTestCase
from zBuilder.utils.vfxUtils import get_zGeo_nodes_by_solverTM
from zBuilder.utils.mayaUtils import safe_rename
from zBuilder.nodes.ziva.zSolverTransform import SolverTransformNode
from zBuilder.nodes.ziva.zSolver import SolverNode
from scenePanel.scenePanel2.groupNode import GroupNode
from scenePanel.scenePanel2.treeItem import TreeItem, build_scene_panel_tree
from scenePanel.scenePanel2.serialize import PendingTreeEntry, flatten_tree, merge_tree_data, _version


def setup_scene():
    # Construct tree structure as follows:
    # ROOT
    #   `- zSolverTransform
    #     |- zSolver
    #     `- group1
    #        `- Sub-group1
    #          |- tissue1
    #          `- tissue2
    cmds.polyCube(n="tissue1")
    cmds.polyCube(n="tissue2")
    cmds.ziva("tissue1", "tissue2", t=True)
    # Clear last created nodes so zBuilder can retrieve all nodes
    cmds.select(cl=True)
    builder = zva.Ziva()
    builder.retrieve_connections()
    root_node = build_scene_panel_tree(builder,
                                       ["zSolver", "zSolverTransform", "ui_zTissue_body"])[0]
    solverTM = root_node.children[0]
    child_nodes = solverTM.children
    solver = child_nodes[0]
    # Create tissue nodes
    tissue1_item = child_nodes[1]
    tissue2_item = child_nodes[2]
    tissue2_item.pin_state = TreeItem.Pinned
    # Create nested group nodes
    group1_item = TreeItem(solverTM, GroupNode("group1"))
    sub_group1_item = TreeItem(group1_item, GroupNode("Sub-group1"))
    sub_group1_item.append_children([tissue1_item, tissue2_item])
    # Return items used for unit test verification
    return builder, root_node, solverTM, solver, group1_item, sub_group1_item, tissue1_item, tissue2_item


def get_mesh_node_by_zGeo_node(builder, node_name):
    """ Return Maya mesh DGNode given zGeo node name.
    Return None if not found or invalid input.
    """
    zGeo_node = builder.get_scene_items(name_filter=node_name)
    if not zGeo_node:
        return None
    return builder.geo.get(zGeo_node[0].long_name, None)


class PendingTreeEntryTestCase(VfxTestCase):
    """ Test PendingTreeEntry class
    """

    def test_treeitem_and_json_constructor(self):
        """ Test PendingTreeEntry overload ctor
        """
        # Setup
        _, _, _, _, _, sub_group1_item, _, tissue2_item = setup_scene()

        # ---------------------------------------------------------------------
        # Action, construct by TreeItem
        sub_group1_entry = PendingTreeEntry(sub_group1_item)
        tissue2_entry = PendingTreeEntry(tissue2_item)

        # Verify
        expected_sub_group1_json_object = ["|zSolver1|group1|Sub-group1", "group", {}]
        self.assertEqual(sub_group1_entry.tree_path, expected_sub_group1_json_object[0])
        self.assertEqual(sub_group1_entry.dir_tree_path, "|zSolver1|group1")
        self.assertEqual(sub_group1_entry.group_name, "Sub-group1")
        self.assertEqual(sub_group1_entry.depth, 3)
        self.assertEqual(sub_group1_entry.node_type, expected_sub_group1_json_object[1])
        self.assertDictEqual(sub_group1_entry.node_data, expected_sub_group1_json_object[2])
        sub_group1_json_object = sub_group1_entry.to_json_object()
        self.assertListEqual(sub_group1_json_object, expected_sub_group1_json_object)

        expected_tissue2_json_object = [
            "|zSolver1|group1|Sub-group1|tissue2", "ui_zTissue_body", {
                "pin_state": TreeItem.Pinned,
                "name": "|tissue2"
            }
        ]
        self.assertEqual(tissue2_entry.tree_path, expected_tissue2_json_object[0])
        self.assertEqual(tissue2_entry.dir_tree_path, "|zSolver1|group1|Sub-group1")
        with self.assertRaises(AssertionError):
            tissue2_entry.group_name
        self.assertEqual(tissue2_entry.depth, 4)
        self.assertEqual(tissue2_entry.node_type, expected_tissue2_json_object[1])
        self.assertDictEqual(tissue2_entry.node_data, expected_tissue2_json_object[2])
        tissue2_json_object = tissue2_entry.to_json_object()
        self.assertListEqual(tissue2_json_object, expected_tissue2_json_object)

        # ---------------------------------------------------------------------
        # Action, construct by json object
        another_sub_group1_entry = PendingTreeEntry(*(sub_group1_json_object + [_version]))
        another_tissue2_entry = PendingTreeEntry(*(tissue2_json_object + [_version]))

        # Verify
        self.assertEqual(another_sub_group1_entry.tree_path, expected_sub_group1_json_object[0])
        self.assertEqual(another_sub_group1_entry.dir_tree_path, "|zSolver1|group1")
        self.assertEqual(another_sub_group1_entry.group_name, "Sub-group1")
        self.assertEqual(another_sub_group1_entry.depth, 3)
        self.assertEqual(another_sub_group1_entry.node_type, expected_sub_group1_json_object[1])
        self.assertDictEqual(another_sub_group1_entry.node_data, expected_sub_group1_json_object[2])
        self.assertListEqual(another_sub_group1_entry.to_json_object(),
                             expected_sub_group1_json_object)

        self.assertEqual(another_tissue2_entry.tree_path, expected_tissue2_json_object[0])
        self.assertEqual(another_tissue2_entry.dir_tree_path, "|zSolver1|group1|Sub-group1")
        with self.assertRaises(AssertionError):
            another_tissue2_entry.group_name
        self.assertEqual(another_tissue2_entry.depth, 4)
        self.assertEqual(another_tissue2_entry.node_type, expected_tissue2_json_object[1])
        self.assertDictEqual(another_tissue2_entry.node_data, expected_tissue2_json_object[2])
        self.assertListEqual(another_tissue2_entry.to_json_object(), expected_tissue2_json_object)

        # ---------------------------------------------------------------------
        # Action & Verify, zBuilder_node property can only set to zBuilder tree item.
        # The zBuilder_node property only applies to TreeItem that is a non-Group node,
        # otherwise it triggers assertion.
        # This test tries to assign zBuilder_node value to a Group node,
        # which triggers the assertion and get caught.
        with self.assertRaises(AssertionError):
            sub_group1_entry.zBuilder_node = None


class MergeTreeDataTestCase(VfxTestCase):
    """ Test merge_tree_data logic
    """

    def test_no_serialize_data(self):
        """ Test merge with no tree view data case.
        This happens when loading ZivaVFX setup whose solver node has no scene panel data.
        """
        # Setup
        _, _, solverTM, _, _, _, tissue1, tissue2 = setup_scene()

        # Action
        new_solverTM, pinned_node_list = merge_tree_data([solverTM.data], None)

        # Verify
        self.assertIsNot(new_solverTM, solverTM)
        self.assertIsInstance(new_solverTM, TreeItem)
        self.assertIsInstance(new_solverTM.data, SolverTransformNode)
        self.assertEqual(len(new_solverTM.children), 3)

        new_solver = new_solverTM.children[0]
        self.assertIsInstance(new_solver, TreeItem)
        self.assertIsInstance(new_solver.data, SolverNode)
        self.assertEqual(len(new_solver.children), 0)

        new_tissue1 = new_solverTM.children[1]
        self.assertIsInstance(new_tissue1, TreeItem)
        self.assertEqual(new_tissue1.pin_state, TreeItem.Unpinned)
        # The new merge tree item refer to the input zBuilder nodes
        self.assertIs(new_tissue1.data, tissue1.data)
        self.assertEqual(len(new_tissue1.children), 0)

        new_tissue2 = new_solverTM.children[2]
        self.assertIsInstance(new_tissue2, TreeItem)
        # Since no tree view data, the pin status is reset
        self.assertEqual(new_tissue2.pin_state, TreeItem.Unpinned)
        # The new merge tree item refer to the input zBuilder nodes
        self.assertIs(new_tissue2.data, tissue2.data)
        self.assertEqual(len(new_tissue2.children), 0)

        # Verify
        # pinned node list is empty because scene panel data is not loaded.
        self.assertEqual(pinned_node_list, [])

    def test_no_conflict_merge(self):
        """ Test merge zBuilder result and tree entry list without conflict.
        """
        # Setup
        builder, _, solverTM, _, _, _, tissue1, tissue2 = setup_scene()
        solverTM_maya_node = cmds.ls(solverTM.data.long_name)
        # Action
        tree_entry_list = flatten_tree(solverTM)
        zGeo_node_list = get_zGeo_nodes_by_solverTM(builder, solverTM_maya_node)
        new_solverTM, pinned_node_list = merge_tree_data(zGeo_node_list, tree_entry_list)

        # Verify
        self.assertIsNot(new_solverTM, solverTM)
        self.assertIsInstance(new_solverTM, TreeItem)
        self.assertIsInstance(new_solverTM.data, SolverTransformNode)
        self.assertEqual(len(new_solverTM.children), 2)

        new_solver = new_solverTM.children[0]
        self.assertIsInstance(new_solver, TreeItem)
        self.assertIsInstance(new_solver.data, SolverNode)
        self.assertEqual(len(new_solver.children), 0)

        new_group1 = new_solverTM.children[1]
        self.assertIsInstance(new_group1, TreeItem)
        self.assertIsInstance(new_group1.data, GroupNode)
        self.assertEqual(len(new_group1.children), 1)

        new_subgroup1 = new_group1.children[0]
        self.assertIsInstance(new_subgroup1, TreeItem)
        self.assertIsInstance(new_subgroup1.data, GroupNode)
        self.assertEqual(len(new_subgroup1.children), 2)

        new_tissue1 = new_subgroup1.children[0]
        self.assertIsInstance(new_tissue1, TreeItem)
        self.assertEqual(new_tissue1.pin_state, TreeItem.Unpinned)
        # The new merge tree item refer to the input zBuilder nodes
        self.assertIs(new_tissue1.data, tissue1.data)
        self.assertEqual(len(new_tissue1.children), 0)

        new_tissue2 = new_subgroup1.children[1]
        self.assertIsInstance(new_tissue2, TreeItem)
        self.assertEqual(new_tissue2.pin_state, TreeItem.Pinned)
        # The new merge tree item refer to the input zBuilder nodes
        self.assertIs(new_tissue2.data, tissue2.data)
        self.assertEqual(len(new_tissue2.children), 0)

        # Verify pinned node list
        self.assertEqual(pinned_node_list, [new_tissue2.data])

    def test_merge_on_new_node_added(self):
        """ Test merge zBuilder w/ new node added with tree entry list.
        """
        # Construct tree structure as follows:
        # ROOT
        #   `- zSolverTransform
        #     |- zSolver
        #     `- group1
        #        `- Sub-group1
        #          |- tissue1
        #          `- tissue2
        #      * tissue3 <-- new item append here

        # Setup
        _, _, solverTM, _, _, _, _, _ = setup_scene()
        tree_entry_list = flatten_tree(solverTM)
        solverTM_maya_node = cmds.ls(solverTM.data.long_name)

        # Action: add new tissue, then mock the Scene Panel "Refresh" operation
        cmds.polyCube(n="tissue3")
        cmds.ziva("tissue3", t=True)
        # Clear last created nodes so zBuilder can retrieve all nodes
        cmds.select(cl=True)
        new_builder = zva.Ziva()
        new_builder.retrieve_connections()
        tissue1_node = get_mesh_node_by_zGeo_node(new_builder, "tissue1")
        tissue2_node = get_mesh_node_by_zGeo_node(new_builder, "tissue2")
        tissue3_node = get_mesh_node_by_zGeo_node(new_builder, "tissue3")

        zGeo_node_list = get_zGeo_nodes_by_solverTM(new_builder, solverTM_maya_node)
        new_solverTM, pinned_node_list = merge_tree_data(zGeo_node_list, tree_entry_list)

        # Verify: new node should append at the end of solverTM child list
        self.assertIsNot(new_solverTM, solverTM)
        self.assertIsInstance(new_solverTM, TreeItem)
        self.assertIsInstance(new_solverTM.data, SolverTransformNode)
        self.assertEqual(len(new_solverTM.children), 3)

        new_solver = new_solverTM.children[0]
        self.assertIsInstance(new_solver, TreeItem)
        self.assertIsInstance(new_solver.data, SolverNode)
        self.assertEqual(len(new_solver.children), 0)

        new_group1 = new_solverTM.children[1]
        self.assertIsInstance(new_group1, TreeItem)
        self.assertIsInstance(new_group1.data, GroupNode)
        self.assertEqual(len(new_group1.children), 1)

        new_subgroup1 = new_group1.children[0]
        self.assertIsInstance(new_subgroup1, TreeItem)
        self.assertIsInstance(new_subgroup1.data, GroupNode)
        self.assertEqual(len(new_subgroup1.children), 2)

        new_tissue1 = new_subgroup1.children[0]
        self.assertIsInstance(new_tissue1, TreeItem)
        self.assertEqual(new_tissue1.pin_state, TreeItem.Unpinned)
        # The new merge tree item refer to the input zBuilder nodes
        self.assertIs(new_tissue1.data, tissue1_node)
        self.assertEqual(len(new_tissue1.children), 0)

        new_tissue2 = new_subgroup1.children[1]
        self.assertIsInstance(new_tissue2, TreeItem)
        self.assertEqual(new_tissue2.pin_state, TreeItem.Pinned)
        # The new merge tree item refer to the input zBuilder nodes
        self.assertIs(new_tissue2.data, tissue2_node)
        self.assertEqual(len(new_tissue2.children), 0)

        new_tissue3 = new_solverTM.children[2]
        self.assertIsInstance(new_tissue3, TreeItem)
        self.assertEqual(new_tissue3.pin_state, TreeItem.Unpinned)
        # The new merge tree item refer to the input zBuilder nodes
        self.assertIs(new_tissue3.data, tissue3_node)
        self.assertEqual(len(new_tissue3.children), 0)

        # Verify pinned node list
        self.assertEqual(pinned_node_list, [new_tissue2.data])

    def test_merge_on_node_deleted(self):
        """ Test merge zBuilder w/ existing node deleted with tree entry list.
        """
        # Construct tree structure as follows:
        # ROOT
        #   `- zSolverTransform
        #     |- zSolver
        #     `- group1
        #        `- Sub-group1
        #          |- tissue1  <-- This item will be deleted
        #          `- tissue2

        # Setup
        _, _, solverTM, _, _, _, _, _ = setup_scene()
        tree_entry_list = flatten_tree(solverTM)
        solverTM_maya_node = cmds.ls(solverTM.data.long_name)

        # Action: delete tissue1, then mock the Scene Panel "Refresh" operation
        cmds.select("tissue1")
        cmds.ziva(rm=True)
        # Clear last created nodes so zBuilder can retrieve all nodes
        cmds.select(cl=True)
        new_builder = zva.Ziva()
        new_builder.retrieve_connections()
        tissue2_node = get_mesh_node_by_zGeo_node(new_builder, "tissue2")

        zGeo_node_list = get_zGeo_nodes_by_solverTM(new_builder, solverTM_maya_node)
        new_solverTM, pinned_node_list = merge_tree_data(zGeo_node_list, tree_entry_list)

        # Verify: new node should append at the end of solverTM child list
        self.assertIsNot(new_solverTM, solverTM)
        self.assertIsInstance(new_solverTM, TreeItem)
        self.assertIsInstance(new_solverTM.data, SolverTransformNode)
        self.assertEqual(len(new_solverTM.children), 2)

        new_solver = new_solverTM.children[0]
        self.assertIsInstance(new_solver, TreeItem)
        self.assertIsInstance(new_solver.data, SolverNode)
        self.assertEqual(len(new_solver.children), 0)

        new_group1 = new_solverTM.children[1]
        self.assertIsInstance(new_group1, TreeItem)
        self.assertIsInstance(new_group1.data, GroupNode)
        self.assertEqual(len(new_group1.children), 1)

        new_subgroup1 = new_group1.children[0]
        self.assertIsInstance(new_subgroup1, TreeItem)
        self.assertIsInstance(new_subgroup1.data, GroupNode)
        self.assertEqual(len(new_subgroup1.children), 1)

        new_tissue2 = new_subgroup1.children[0]
        self.assertIsInstance(new_tissue2, TreeItem)
        self.assertEqual(new_tissue2.pin_state, TreeItem.Pinned)
        # The new merge tree item refer to the input zBuilder nodes
        self.assertIs(new_tissue2.data, tissue2_node)
        self.assertEqual(len(new_tissue2.children), 0)

        # Verify pinned node list
        self.assertEqual(pinned_node_list, [new_tissue2.data])

    def test_merge_on_node_renamed(self):
        """ Test merge zBuilder w/ existing node renamed with tree entry list.
        The renamed item will move to the end of the zSolverTM child list.
        The renamed zSolverTM/zSolver nodes will not be moved.
        """
        # Construct tree structure as follows:
        # ROOT
        #   `- zSolver1         <-- rename to new1_zSolver
        #     |- zSolver1Shape  <-- rename to new2_zSolver1Shape
        #     `- group1
        #        `- Sub-group1
        #          |- tissue1   <-- delete after rename
        #          `- tissue2
        #      * new_tissue1    <-- "tissue1" is appended as new node

        # Setup
        _, _, solverTM, solver, _, _, _, _ = setup_scene()
        tree_entry_list = flatten_tree(solverTM)
        solverTM_maya_node = cmds.ls(solverTM.data.long_name)
        solver_maya_node = cmds.ls(solver.data.long_name)

        # Action
        # Rename tissue1 mesh, zSolverTM/zSolver nodes,
        # then mock the Scene Panel "Refresh" operation
        safe_rename("tissue1", "new_tissue1")
        new_solverTM_name = "new1_{}".format(solverTM_maya_node[0])
        new_solver_name = "new2_{}".format(solver_maya_node[0])
        safe_rename(solverTM_maya_node, new_solverTM_name)
        safe_rename(solver_maya_node, new_solver_name)
        # Clear last created nodes so zBuilder can retrieve all nodes
        cmds.select(cl=True)
        new_builder = zva.Ziva()
        new_builder.retrieve_connections()
        tissue1_node = get_mesh_node_by_zGeo_node(new_builder, "new_tissue1")
        tissue2_node = get_mesh_node_by_zGeo_node(new_builder, "tissue2")

        zGeo_node_list = get_zGeo_nodes_by_solverTM(new_builder, new_solverTM_name)
        new_solverTM, pinned_node_list = merge_tree_data(zGeo_node_list, tree_entry_list)

        # Verify: new node should append at the end of solverTM child list
        self.assertIsNot(new_solverTM, solverTM)
        self.assertIsInstance(new_solverTM, TreeItem)
        self.assertIsInstance(new_solverTM.data, SolverTransformNode)
        self.assertEqual(len(new_solverTM.children), 3)

        new_solver = new_solverTM.children[0]
        self.assertIsInstance(new_solver, TreeItem)
        self.assertIsInstance(new_solver.data, SolverNode)
        self.assertEqual(len(new_solver.children), 0)

        new_group1 = new_solverTM.children[1]
        self.assertIsInstance(new_group1, TreeItem)
        self.assertIsInstance(new_group1.data, GroupNode)
        self.assertEqual(len(new_group1.children), 1)

        new_subgroup1 = new_group1.children[0]
        self.assertIsInstance(new_subgroup1, TreeItem)
        self.assertIsInstance(new_subgroup1.data, GroupNode)
        self.assertEqual(len(new_subgroup1.children), 1)

        new_tissue2 = new_subgroup1.children[0]
        self.assertIsInstance(new_tissue2, TreeItem)
        self.assertEqual(new_tissue2.pin_state, TreeItem.Pinned)
        # The new merge tree item refer to the input zBuilder nodes
        self.assertIs(new_tissue2.data, tissue2_node)
        self.assertEqual(len(new_tissue2.children), 0)

        new_tissue1 = new_solverTM.children[2]
        self.assertIsInstance(new_tissue1, TreeItem)
        self.assertEqual(new_tissue1.pin_state, TreeItem.Unpinned)
        # The new merge tree item refer to the input zBuilder nodes
        self.assertIs(new_tissue1.data, tissue1_node)
        self.assertEqual(len(new_tissue1.children), 0)

        # Verify pinned node list
        self.assertEqual(pinned_node_list, [new_tissue2.data])
