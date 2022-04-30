import zBuilder.builders.ziva as zva

from maya import cmds
from vfx_test_case import VfxTestCase
from scenePanel.scenePanel2.groupNode import GroupNode
from scenePanel.scenePanel2.treeItem import TreeItem, build_scene_panel_tree
from scenePanel.scenePanel2.serialize import (flatten_tree, to_tree_entry_list, construct_tree,
                                              to_json_string, _version)


class ScenePanelSerializationTestCase(VfxTestCase):
    # Tree structure for the test cases:
    # ROOT
    #   `- zSolver1
    #     |- zSolver1Shape
    #     |- group1
    #     |  `- Sub-group1
    #     |    `- Sub-sub-group1
    #     |      `- tissue1
    #     `- group2
    #        `- Sub-group2
    #          `- tissue2
    # The list is arranged in DFS order.
    test_tree_data = [
        ["|zSolver1", "zSolverTransform", {
            "name": "|zSolver1",
            "pin_state": 0
        }],
        ["|zSolver1|zSolver1Shape", "zSolver", {
            "name": "|zSolver1|zSolver1Shape",
            "pin_state": 0
        }],
        ["|zSolver1|group1", "group", {}],
        ["|zSolver1|group1|Sub-group1", "group", {}],
        ["|zSolver1|group1|Sub-group1|Sub-sub-group1", "group", {}],
        [
            "|zSolver1|group1|Sub-group1|Sub-sub-group1|tissue1", "ui_zTissue_body", {
                "name": "|tissue1",
                "pin_state": 2
            }
        ],
        ["|zSolver1|group2", "group", {}],
        ["|zSolver1|group2|Sub-group2", "group", {}],
        [
            "|zSolver1|group2|Sub-group2|tissue2", "ui_zTissue_body", {
                "name": "|tissue2",
                "pin_state": 0
            }
        ],
    ]

    def setup_tree_structure(self):
        """ Helper function to:
        1. Create a Maya scene
        2. Retrive the scene connection with zBuilder
        3. Add some Group node to the tree structure
        It returns the root node.
        """
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
        # Get tissue nodes
        tissue1_node = child_nodes[1]
        tissue1_node.pin_state = TreeItem.Pinned
        tissue2_node = child_nodes[2]
        # Create nested group nodes
        group1_node = TreeItem(solverTM, GroupNode("group1"))
        sub_group1_node = TreeItem(group1_node, GroupNode("Sub-group1"))
        sub_sub_group1_node = TreeItem(sub_group1_node, GroupNode("Sub-sub-group1"))
        sub_sub_group1_node.append_children(tissue1_node)
        group2_node = TreeItem(solverTM, GroupNode("group2"))
        sub_group2_node = TreeItem(group2_node, GroupNode("Sub-group2"))
        sub_group2_node.append_children(tissue2_node)
        return root_node

    def test_flatten_tree_function(self):
        # Setup
        root_node = self.setup_tree_structure()

        # Action
        serialized_data = [entry.to_json_object() for entry in flatten_tree(root_node)]

        # Verify
        self.assertEqual(type(serialized_data), list)
        self.assertEqual(len(serialized_data), 9)
        self.assertListEqual(ScenePanelSerializationTestCase.test_tree_data, serialized_data)

    def test_construct_tree_function(self):
        # Action
        solverTM, pinned_item_list = construct_tree(
            to_tree_entry_list(ScenePanelSerializationTestCase.test_tree_data, _version), True)

        # Verify: return value constructs the test_tree_data tree structure.
        # Note the ROOT node is not included.
        self.assertIsNone(solverTM.parent)
        self.assertEqual(solverTM.data.type, "zSolverTransform")
        self.assertEqual(solverTM.data.name, "zSolver1")
        self.assertEqual(solverTM.pin_state, TreeItem.Unpinned)
        solver_node = solverTM.children[0]
        self.assertEqual(solver_node.data.type, "zSolver")
        self.assertEqual(solver_node.data.name, "zSolver1Shape")
        self.assertEqual(solver_node.pin_state, TreeItem.Unpinned)

        group1_node = solverTM.children[1]
        group2_node = solverTM.children[2]
        self.assertEqual(group1_node.data.type, "group")
        self.assertEqual(group1_node.child_count(), 1)
        self.assertEqual(group2_node.data.type, "group")
        self.assertEqual(group2_node.child_count(), 1)

        sub_group1 = group1_node.children[0]
        sub_group2 = group2_node.children[0]
        self.assertEqual(sub_group1.data.type, "group")
        self.assertEqual(sub_group1.child_count(), 1)
        self.assertEqual(sub_group2.data.type, "group")
        self.assertEqual(sub_group2.child_count(), 1)

        sub_sub_group1 = sub_group1.children[0]
        tissue2 = sub_group2.children[0]
        self.assertEqual(sub_sub_group1.data.type, "group")
        self.assertEqual(sub_sub_group1.child_count(), 1)

        self.assertEqual(tissue2.data.type, "ui_zTissue_body")
        self.assertEqual(tissue2.data.name, "tissue2")
        self.assertEqual(tissue2.pin_state, TreeItem.Unpinned)
        self.assertEqual(tissue2.child_count(), 0)

        tissue1 = sub_sub_group1.children[0]
        self.assertEqual(tissue1.data.type, "ui_zTissue_body")
        self.assertEqual(tissue1.data.name, "tissue1")
        self.assertEqual(tissue1.pin_state, TreeItem.Pinned)
        self.assertEqual(tissue1.child_count(), 0)

        # Verify pinned item list
        self.assertEqual(pinned_item_list, [tissue1])

    def test_construct_tree_function2(self):
        """ Test if construct_tree() can handle consecutive tree items
        """
        # Setup: data to construct
        serialized_data = [
            ["|zSolver1", "zSolverTransform", {
                "pin_state": 0,
                "name": "|zSolver1",
            }],
            [
                "|zSolver1|zSolver1Shape", "zSolver", {
                    "pin_state": 0,
                    "name": "|zSolver1|zSolver1Shape",
                }
            ],
            ["|zSolver1|group1", "group", {}],
            ["|zSolver1|group1|Sub-group1", "group", {}],
            ["|zSolver1|group1|Sub-group2", "group", {}],
            ["|zSolver1|group1|Sub-group3", "group", {}],
            [
                "|zSolver1|group1|Sub-group3|tissue1", "ui_zTissue_body", {
                    "pin_state": 2,
                    "name": "|tissue1",
                }
            ],
        ]

        # Action
        solverTM, pinned_item_list = construct_tree(to_tree_entry_list(serialized_data, _version),
                                                    True)

        # Verify above data returns a tree structure as follows:
        # zSolver1
        #   |- zSolver1Shape
        #   `- group1
        #      |- Sub-group1
        #      |- Sub-group2
        #      `- Sub-group3
        #        `- tissue1
        self.assertIsNone(solverTM.parent)
        self.assertEqual(solverTM.data.type, "zSolverTransform")
        self.assertEqual(solverTM.data.name, "zSolver1")
        solver = solverTM.children[0]
        self.assertEqual(solver.data.type, "zSolver")
        self.assertEqual(solver.data.name, "zSolver1Shape")

        group1_node = solverTM.children[1]
        self.assertEqual(group1_node.data.type, "group")
        self.assertEqual(group1_node.child_count(), 3)

        sub_group1_node = group1_node.children[0]
        self.assertEqual(sub_group1_node.data.type, "group")
        self.assertEqual(sub_group1_node.child_count(), 0)

        sub_group2_node = group1_node.children[1]
        self.assertEqual(sub_group2_node.data.type, "group")
        self.assertEqual(sub_group2_node.child_count(), 0)

        sub_sub_group3 = group1_node.children[2]
        self.assertEqual(sub_sub_group3.data.type, "group")
        self.assertEqual(sub_sub_group3.child_count(), 1)

        tissue1_node = sub_sub_group3.children[0]
        self.assertEqual(tissue1_node.data.type, "ui_zTissue_body")
        self.assertEqual(tissue1_node.data.name, "tissue1")
        self.assertEqual(tissue1_node.pin_state, TreeItem.Pinned)
        self.assertEqual(tissue1_node.child_count(), 0)

        # Verify pinned item list
        self.assertEqual(pinned_item_list, [tissue1_node])

    def test_round_trip_of_json_tree_data(self):
        """ Test the functions that do the conversion between json string and TreeItem tree.
        """
        # Setup
        root_node = self.setup_tree_structure()

        # Action
        json_string = to_json_string(flatten_tree(root_node))
        deserialized_solverTM, pinned_item_list = construct_tree(to_tree_entry_list(json_string),
                                                                 True)

        # Verify: compare results with original tree items
        self.assertIsNone(deserialized_solverTM.parent)
        self.assertEqual(deserialized_solverTM.data.type, "zSolverTransform")
        self.assertEqual(deserialized_solverTM.data.name, "zSolver1")
        self.assertEqual(deserialized_solverTM.pin_state, TreeItem.Unpinned)
        deserialized_solver = deserialized_solverTM.children[0]
        self.assertEqual(deserialized_solver.data.type, "zSolver")
        self.assertEqual(deserialized_solver.data.name, "zSolver1Shape")
        self.assertEqual(deserialized_solver.pin_state, TreeItem.Unpinned)

        deserialized_group1_node = deserialized_solverTM.children[1]
        deserialized_group2_node = deserialized_solverTM.children[2]
        self.assertEqual(deserialized_group1_node.data.type, "group")
        self.assertEqual(deserialized_group1_node.child_count(), 1)
        self.assertEqual(deserialized_group2_node.data.type, "group")
        self.assertEqual(deserialized_group2_node.child_count(), 1)

        deserialized_sub_group1_node = deserialized_group1_node.children[0]
        self.assertEqual(deserialized_sub_group1_node.data.type, "group")
        self.assertEqual(deserialized_sub_group1_node.child_count(), 1)

        deserialized_sub_sub_group1_node = deserialized_sub_group1_node.children[0]
        self.assertEqual(deserialized_sub_sub_group1_node.data.type, "group")
        self.assertEqual(deserialized_sub_sub_group1_node.child_count(), 1)

        deserialized_tissue1_node = deserialized_sub_sub_group1_node.children[0]
        self.assertEqual(deserialized_tissue1_node.data.type, "ui_zTissue_body")
        self.assertEqual(deserialized_tissue1_node.data.name, "tissue1")
        self.assertEqual(deserialized_tissue1_node.pin_state, TreeItem.Pinned)
        self.assertEqual(deserialized_tissue1_node.child_count(), 0)

        deserialized_sub_group2_node = deserialized_group2_node.children[0]
        self.assertEqual(deserialized_sub_group2_node.data.type, "group")
        self.assertEqual(deserialized_sub_group2_node.child_count(), 1)

        deserialized_tissue2_node = deserialized_sub_group2_node.children[0]
        self.assertEqual(deserialized_tissue2_node.data.type, "ui_zTissue_body")
        self.assertEqual(deserialized_tissue2_node.data.name, "tissue2")
        self.assertEqual(deserialized_tissue2_node.pin_state, TreeItem.Unpinned)
        self.assertEqual(deserialized_tissue2_node.child_count(), 0)

        # Verify pinned item list
        self.assertEqual(pinned_item_list, [deserialized_tissue1_node])

    def test_construct_multiple_solvers(self):
        """ Test construct of multiple solvers separately.
        """
        # Setup: construct tree structure as follows:
        # ROOT
        #   |- zSolver1
        #   | |- zSolver1Shape
        #   | `- group1
        #   |    - tissue1
        #   |- zSolver2
        #   | |- zSolver2Shape
        #   | `- group2
        #   |    - tissue2
        #   `- zSolver3
        #     |- zSolver3Shape
        #     `- tissue3
        cmds.ziva(s=True)
        cmds.polyCube(n="tissue1")
        cmds.ziva("tissue1", t=True)
        cmds.ziva(s=True)
        cmds.polyCube(n="tissue2")
        cmds.ziva("tissue2", t=True)
        cmds.ziva(s=True)
        cmds.polyCube(n="tissue3")
        cmds.ziva("tissue3", t=True)
        cmds.select(cl=True)
        builder = zva.Ziva()
        builder.retrieve_connections()
        root_node = build_scene_panel_tree(builder,
                                           ["zSolver", "zSolverTransform", "ui_zTissue_body"])[0]
        # get tissue nodes
        solver1 = root_node.children[0]
        tissue1 = solver1.children[1]
        solver2 = root_node.children[1]
        tissue2 = solver2.children[1]
        tissue2.pin_state = TreeItem.Pinned
        solver3 = root_node.children[2]
        # Create group nodes and add tissue nodes as child
        group1 = TreeItem(solver1, GroupNode("group1"))
        group1.append_children(tissue1)
        group2 = TreeItem(solver2, GroupNode("group2"))
        group2.append_children(tissue2)

        # ---------------------------------------------------------------------
        # Action: serialized data for solver1 tree below
        # zSolver1
        #   |- zSolver1Shape
        #   `- group1
        #      - tissue1
        serialized_solver1_data = [entry.to_json_object() for entry in flatten_tree(solver1)]

        # Verify
        self.assertEqual(type(serialized_solver1_data), list)
        self.assertEqual(len(serialized_solver1_data), 4)
        expected_result1 = [
            ["|zSolver1", "zSolverTransform", {
                "pin_state": 0,
                "name": "|zSolver1",
            }],
            [
                "|zSolver1|zSolver1Shape", "zSolver", {
                    "pin_state": 0,
                    "name": "|zSolver1|zSolver1Shape",
                }
            ],
            ["|zSolver1|group1", "group", {}],
            ["|zSolver1|group1|tissue1", "ui_zTissue_body", {
                "pin_state": 0,
                "name": "|tissue1",
            }],
        ]
        self.assertListEqual(expected_result1, serialized_solver1_data)

        # ---------------------------------------------------------------------
        # Action: serialized data for solver2 tree below
        # zSolver2
        #   |- zSolver2Shape
        #   `- group2
        #      - tissue2
        serialized_solver2_data = [entry.to_json_object() for entry in flatten_tree(solver2)]

        # Verify
        self.assertEqual(len(serialized_solver2_data), 4)
        expected_result2 = [
            ["|zSolver2", "zSolverTransform", {
                "pin_state": 0,
                "name": "|zSolver2",
            }],
            [
                "|zSolver2|zSolver2Shape", "zSolver", {
                    "pin_state": 0,
                    "name": "|zSolver2|zSolver2Shape",
                }
            ],
            ["|zSolver2|group2", "group", {}],
            ["|zSolver2|group2|tissue2", "ui_zTissue_body", {
                "pin_state": 2,
                "name": "|tissue2",
            }],
        ]
        self.assertListEqual(expected_result2, serialized_solver2_data)

        # ---------------------------------------------------------------------
        # Action: serialized data for solver3 tree below
        # zSolver3
        #   |- zSolver3Shape
        #   `- tissue3
        serialized_solver3_data = [entry.to_json_object() for entry in flatten_tree(solver3)]

        # Verify
        self.assertEqual(len(serialized_solver3_data), 3)
        expected_result3 = [
            ["|zSolver3", "zSolverTransform", {
                "pin_state": 0,
                "name": "|zSolver3",
            }],
            [
                "|zSolver3|zSolver3Shape", "zSolver", {
                    "pin_state": 0,
                    "name": "|zSolver3|zSolver3Shape",
                }
            ],
            ["|zSolver3|tissue3", "ui_zTissue_body", {
                "pin_state": 0,
                "name": "|tissue3",
            }],
        ]
        self.assertListEqual(expected_result3, serialized_solver3_data)