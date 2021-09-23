import zBuilder.builders.ziva as zva

from vfx_test_case import VfxTestCase
from zBuilder.scenePanel2.groupNode import GroupNode
from zBuilder.scenePanel2.treeItem import *
from zBuilder.scenePanel2.serialize import PendingTreeEntry
from maya import cmds


class PendingTreeEntryTestCase(VfxTestCase):
    """ Test PendingTreeEntry class
    """
    def test_treeitem_constructor(self):
        # Setup: construct tree structure as follows:
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
        solver_node = root_node.children[0]
        child_nodes = solver_node.children
        # Create tissue nodes
        tissue1_node = child_nodes[1]
        tissue2_node = child_nodes[2]
        tissue2_node.pin_state = TreeItem.Pinned
        # Create nested group nodes
        group1_item = TreeItem(solver_node, GroupNode("group1"))
        sub_group1_item = TreeItem(group1_item, GroupNode("Sub-group1"))
        sub_group1_item.append_children([tissue1_node, tissue2_node])
        tissue2_item = sub_group1_item.children[1]

        # ---------------------------------------------------------------------
        # Action, construct by TreeItem
        sub_group1_entry = PendingTreeEntry(sub_group1_item)
        tissue2_entry = PendingTreeEntry(tissue2_item)

        # Verify
        expected_sub_group1_json_object = ["|zSolver1|group1|Sub-group1", 0, "group", {}]
        self.assertEqual(sub_group1_entry.tree_path, expected_sub_group1_json_object[0])
        self.assertEqual(sub_group1_entry.dir_tree_path, "|zSolver1|group1")
        self.assertEqual(sub_group1_entry.group_name, "Sub-group1")
        self.assertEqual(sub_group1_entry.depth, 3)
        self.assertEqual(sub_group1_entry.row_index, expected_sub_group1_json_object[1])
        self.assertEqual(sub_group1_entry.node_type, expected_sub_group1_json_object[2])
        self.assertDictEqual(sub_group1_entry.node_data, expected_sub_group1_json_object[3])
        sub_group1_json_object = sub_group1_entry.to_json_object()
        self.assertListEqual(sub_group1_json_object, expected_sub_group1_json_object)

        expected_tissue2_json_object = [
            "|zSolver1|group1|Sub-group1|tissue2", 1, "ui_zTissue_body", {
                "pin_state": TreeItem.Pinned,
                "name": "|tissue2"
            }
        ]
        self.assertEqual(tissue2_entry.tree_path, expected_tissue2_json_object[0])
        self.assertEqual(tissue2_entry.dir_tree_path, "|zSolver1|group1|Sub-group1")
        with self.assertRaises(AssertionError):
            tissue2_entry.group_name
        self.assertEqual(tissue2_entry.depth, 4)
        self.assertEqual(tissue2_entry.row_index, expected_tissue2_json_object[1])
        self.assertEqual(tissue2_entry.node_type, expected_tissue2_json_object[2])
        self.assertDictEqual(tissue2_entry.node_data, expected_tissue2_json_object[3])
        tissue2_json_object = tissue2_entry.to_json_object()
        self.assertListEqual(tissue2_json_object, expected_tissue2_json_object)

        # ---------------------------------------------------------------------
        # Action, construct by json object
        another_sub_group1_entry = PendingTreeEntry(*sub_group1_json_object)
        another_tissue2_entry = PendingTreeEntry(*tissue2_json_object)

        # Verify
        self.assertEqual(another_sub_group1_entry.tree_path, expected_sub_group1_json_object[0])
        self.assertEqual(another_sub_group1_entry.dir_tree_path, "|zSolver1|group1")
        self.assertEqual(another_sub_group1_entry.group_name, "Sub-group1")
        self.assertEqual(another_sub_group1_entry.depth, 3)
        self.assertEqual(another_sub_group1_entry.row_index, expected_sub_group1_json_object[1])
        self.assertEqual(another_sub_group1_entry.node_type, expected_sub_group1_json_object[2])
        self.assertDictEqual(another_sub_group1_entry.node_data, expected_sub_group1_json_object[3])
        self.assertListEqual(another_sub_group1_entry.to_json_object(),
                             expected_sub_group1_json_object)

        self.assertEqual(another_tissue2_entry.tree_path, expected_tissue2_json_object[0])
        self.assertEqual(another_tissue2_entry.dir_tree_path, "|zSolver1|group1|Sub-group1")
        with self.assertRaises(AssertionError):
            another_tissue2_entry.group_name
        self.assertEqual(another_tissue2_entry.depth, 4)
        self.assertEqual(another_tissue2_entry.row_index, expected_tissue2_json_object[1])
        self.assertEqual(another_tissue2_entry.node_type, expected_tissue2_json_object[2])
        self.assertDictEqual(another_tissue2_entry.node_data, expected_tissue2_json_object[3])
        self.assertListEqual(another_tissue2_entry.to_json_object(), expected_tissue2_json_object)