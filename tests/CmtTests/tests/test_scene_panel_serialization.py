import zBuilder.builders.ziva as zva

from vfx_test_case import VfxTestCase
from zBuilder.scenePanel2.groupNode import GroupNode
from zBuilder.scenePanel2.treeItem import *
from zBuilder.scenePanel2.serialize import *
from maya import cmds


class ScenePanelSerializationTestCase(VfxTestCase):
    def test_serialized_node_data(self):
        """ Setup some nodes, both group and DgNode and
        test serialized data.
        """
        # Setup: construct tree structure as follows:
        # ROOT
        #   `- zSolverTransform
        #     |- zSolver
        #     |- group1
        #     |  `- Sub-group1
        #     |    `- Sub-sub-group1
        #     |      `- tissue1
        #     |- group2
        #     |  `- Sub-group2
        #     |    `- tissue2
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
        tissue1_node.pin_state = TreeItem.Pinned
        tissue2_node = child_nodes[2]

        # Create nested group nodes
        group1_node = TreeItem(solver_node, GroupNode("group1"))
        sub_group1_node = TreeItem(group1_node, GroupNode("Sub-group1"))
        sub_sub_group1_node = TreeItem(sub_group1_node, GroupNode("Sub-sub-group1"))
        sub_sub_group1_node.append_children(tissue1_node)
        group2_node = TreeItem(solver_node, GroupNode("group2"))
        sub_group2_node = TreeItem(group2_node, GroupNode("Sub-group2"))
        sub_group2_node.append_children(tissue2_node)

        # Action
        serialized_data = serialize_tree_model(root_node)

        # Verify
        self.assertEqual(type(serialized_data), list)
        self.assertEqual(len(serialized_data), 9)
        expected_result = [
            ["|zSolver1", 0, "zSolverTransform", {
                "pin_state": 0,
                "name": "|zSolver1"
            }],
            [
                "|zSolver1|zSolver1Shape", 0, "zSolver", {
                    "pin_state": 0,
                    "name": "|zSolver1|zSolver1Shape",
                }
            ],
            ["|zSolver1|group1", 1, "group", {}],
            ["|zSolver1|group2", 2, "group", {}],
            ["|zSolver1|group1|Sub-group1", 0, "group", {}],
            ["|zSolver1|group2|Sub-group2", 0, "group", {}],
            ["|zSolver1|group1|Sub-group1|Sub-sub-group1", 0, "group", {}],
            [
                "|zSolver1|group2|Sub-group2|tissue2", 0, "ui_zTissue_body", {
                    "pin_state": 0,
                    "name": "|tissue2",
                }
            ],
            [
                "|zSolver1|group1|Sub-group1|Sub-sub-group1|tissue1", 0, "ui_zTissue_body", {
                    "pin_state": 2,
                    "name": "|tissue1",
                }
            ],
        ]
        self.assertListEqual(expected_result, serialized_data)

    def test_deserialized_data_group_with_children(self):
        """ Test de-serialization of scene panel data where all group
        nodes have children and the tree has multiple depth levels.
        """
        # data to de-serialize
        serialized_data = [
            ["|zSolver1", 0, "zSolverTransform", {
                "pin_state": 0,
                "name": "|zSolver1",
            }],
            [
                "|zSolver1|zSolver1Shape", 0, "zSolver", {
                    "pin_state": 0,
                    "name": "|zSolver1|zSolver1Shape",
                }
            ],
            ["|zSolver1|group1", 1, "group", {}],
            ["|zSolver1|group2", 2, "group", {}],
            ["|zSolver1|group1|Sub-group1", 0, "group", {}],
            ["|zSolver1|group2|Sub-group2", 0, "group", {}],
            ["|zSolver1|group1|Sub-group1|Sub-sub-group1", 0, "group", {}],
            [
                "|zSolver1|group2|Sub-group2|tissue2", 0, "ui_zTissue_body", {
                    "pin_state": 0,
                    "name": "|tissue2",
                }
            ],
            [
                "|zSolver1|group1|Sub-group1|Sub-sub-group1|tissue1", 0, "ui_zTissue_body", {
                    "pin_state": 2,
                    "name": "|tissue1",
                }
            ],
        ]

        # Action
        tree_root_node = deserialize_tree_model(serialized_data, 1)

        # Verify above data returns a tree structure as follows:
        # ROOT
        #   `- zSolverTransform
        #     |- zSolver
        #     |- group1
        #     |  `- Sub-group1
        #     |    `- Sub-sub-group1
        #     |      `- tissue1
        #     |- group2
        #     |  `- Sub-group2
        #     |    `- tissue2
        self.assertIsNone(tree_root_node.parent)
        self.assertTrue(tree_root_node.is_root_node())
        solver_node = tree_root_node.children[0]
        self.assertEqual(solver_node.data.type, "zSolverTransform")
        self.assertEqual(solver_node.data.name, "zSolver1")
        self.assertEqual(solver_node.pin_state, TreeItem.Unpinned)
        solver_shape_node = solver_node.children[0]
        self.assertEqual(solver_shape_node.data.type, "zSolver")
        self.assertEqual(solver_shape_node.data.name, "zSolver1Shape")
        self.assertEqual(solver_shape_node.pin_state, TreeItem.Unpinned)

        group1_node = solver_node.children[1]
        group2_node = solver_node.children[2]
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

    def test_deserialized_data_top_group_with_children(self):
        """ Test de-serialization of scene panel data where the top
        group node has children but other group node is empty.
        This test manifests that we can handle an empty group.
        """
        # data to de-serialize
        serialized_data = [
            ["|zSolver1", 0, "zSolverTransform", {
                "pin_state": 0,
                "name": "|zSolver1",
            }],
            [
                "|zSolver1|zSolver1Shape", 0, "zSolver", {
                    "pin_state": 0,
                    "name": "|zSolver1|zSolver1Shape",
                }
            ],
            ["|zSolver1|group1", 1, "group", {}],
            ["|zSolver1|group2", 2, "group", {}],
            ["|zSolver1|group1|Sub-group1", 0, "group", {}],
            ["|zSolver1|group1|Sub-group1|Sub-sub-group1", 0, "group", {}],
            [
                "|zSolver1|group1|Sub-group1|Sub-sub-group1|tissue1", 0, "ui_zTissue_body", {
                    "pin_state": 2,
                    "name": "|tissue1",
                }
            ],
        ]

        # Action
        tree_root_node = deserialize_tree_model(serialized_data, 1)

        # Verify above data returns a tree structure as follows:
        # ROOT
        #   `- zSolverTransform
        #     |- zSolver
        #     |- group1
        #     |  `- Sub-group1
        #     |    `- Sub-sub-group1
        #     |      `- tissue1
        #     |- group2
        self.assertIsNone(tree_root_node.parent)
        self.assertTrue(tree_root_node.is_root_node())
        solver_node = tree_root_node.children[0]
        self.assertEqual(solver_node.data.type, "zSolverTransform")
        self.assertEqual(solver_node.data.name, "zSolver1")
        self.assertEqual(solver_node.pin_state, TreeItem.Unpinned)
        solver_shape_node = solver_node.children[0]
        self.assertEqual(solver_shape_node.data.type, "zSolver")
        self.assertEqual(solver_shape_node.data.name, "zSolver1Shape")
        self.assertEqual(solver_shape_node.pin_state, TreeItem.Unpinned)

        group1_node = solver_node.children[1]
        group2_node = solver_node.children[2]
        self.assertEqual(group1_node.data.type, "group")
        self.assertEqual(group1_node.child_count(), 1)
        self.assertEqual(group2_node.data.type, "group")
        self.assertEqual(group2_node.child_count(), 0)

        sub_group1_node = group1_node.children[0]
        self.assertEqual(sub_group1_node.data.type, "group")
        self.assertEqual(sub_group1_node.child_count(), 1)

        sub_sub_group1_node = sub_group1_node.children[0]
        self.assertEqual(sub_sub_group1_node.data.type, "group")
        self.assertEqual(sub_sub_group1_node.child_count(), 1)

        tissue1_node = sub_sub_group1_node.children[0]
        self.assertEqual(tissue1_node.data.type, "ui_zTissue_body")
        self.assertEqual(tissue1_node.data.name, "tissue1")
        self.assertEqual(tissue1_node.pin_state, TreeItem.Pinned)
        self.assertEqual(tissue1_node.child_count(), 0)

    def test_deserialized_data_bottom_group_with_children(self):
        """ Test de-serialization of scene panel data where the bottom
        group node has children but top group node is empty.
        This test demonstrates that we can find the right parent
        when we encounter a group node without children.
        """
        # data to de-serialize
        serialized_data = [
            ["|zSolver1", 0, "zSolverTransform", {
                "pin_state": 0,
                "name": "|zSolver1",
            }],
            [
                "|zSolver1|zSolver1Shape", 0, "zSolver", {
                    "pin_state": 0,
                    "name": "|zSolver1|zSolver1Shape",
                }
            ],
            ["|zSolver1|group1", 1, "group", {}],
            ["|zSolver1|group2", 2, "group", {}],
            ["|zSolver1|group2|Sub-group1", 0, "group", {}],
            ["|zSolver1|group2|Sub-group1|Sub-sub-group1", 0, "group", {}],
            [
                "|zSolver1|group2|Sub-group1|Sub-sub-group1|tissue1", 0, "ui_zTissue_body", {
                    "pin_state": 0,
                    "name": "|tissue1",
                }
            ],
        ]

        # Action
        tree_root_node = deserialize_tree_model(serialized_data, 1)

        # Verify above data returns a tree structure as follows:
        # ROOT
        #   `- zSolverTransform
        #     |- zSolver
        #     |- group1
        #     |- group2
        #     |  `- Sub-group1
        #     |    `- Sub-sub-group1
        #     |      `- tissue1
        self.assertIsNone(tree_root_node.parent)
        self.assertTrue(tree_root_node.is_root_node())
        solver_node = tree_root_node.children[0]
        self.assertEqual(solver_node.data.type, "zSolverTransform")
        self.assertEqual(solver_node.data.name, "zSolver1")
        self.assertEqual(solver_node.pin_state, TreeItem.Unpinned)
        solver_shape_node = solver_node.children[0]
        self.assertEqual(solver_shape_node.data.type, "zSolver")
        self.assertEqual(solver_shape_node.data.name, "zSolver1Shape")
        self.assertEqual(solver_shape_node.pin_state, TreeItem.Unpinned)

        group1_node = solver_node.children[1]
        group2_node = solver_node.children[2]
        self.assertEqual(group1_node.data.type, "group")
        self.assertEqual(group1_node.child_count(), 0)
        self.assertEqual(group2_node.data.type, "group")
        self.assertEqual(group2_node.child_count(), 1)

        sub_group1_node = group2_node.children[0]
        self.assertEqual(sub_group1_node.data.type, "group")
        self.assertEqual(sub_group1_node.child_count(), 1)

        sub_sub_group1_node = sub_group1_node.children[0]
        self.assertEqual(sub_sub_group1_node.data.type, "group")
        self.assertEqual(sub_sub_group1_node.child_count(), 1)

        tissue1_node = sub_sub_group1_node.children[0]
        self.assertEqual(tissue1_node.data.type, "ui_zTissue_body")
        self.assertEqual(tissue1_node.data.name, "tissue1")
        self.assertEqual(tissue1_node.pin_state, TreeItem.Unpinned)
        self.assertEqual(tissue1_node.child_count(), 0)

    def test_round_trip_of_serialized_data(self):
        """ Here we serialize and then de-serialize the same data
        and test that the data we get back is the same we serialized.
        """
        # Setup: construct tree structure as follows:
        # ROOT
        #   `- zSolverTransform
        #     |- zSolver
        #     |- group1
        #     |  `- Sub-group1
        #     |    `- Sub-sub-group1
        #     |      `- tissue1
        #     |- group2
        #     |  `- Sub-group2
        #     |    `- tissue2
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
        tissue1_node.pin_state = TreeItem.Pinned
        tissue2_node = child_nodes[2]
        # Create nested group nodes
        group1_node = TreeItem(solver_node, GroupNode("group1"))
        sub_group1_node = TreeItem(group1_node, GroupNode("Sub-group1"))
        sub_sub_group1_node = TreeItem(sub_group1_node, GroupNode("Sub-sub-group1"))
        sub_sub_group1_node.append_children(tissue1_node)
        group2_node = TreeItem(solver_node, GroupNode("group2"))
        sub_group2_node = TreeItem(group2_node, GroupNode("Sub-group2"))
        sub_group2_node.append_children(tissue2_node)

        # Action: serialize and then de-serialize the serialized data
        serialized_data = serialize_tree_model(root_node)
        print("serialized_data: ", serialized_data)
        deserialized_root_node = deserialize_tree_model(serialized_data, 1)

        # Verify: compare results with original tree items
        self.assertIsNone(deserialized_root_node.parent)
        self.assertTrue(deserialized_root_node.is_root_node())
        deserialized_solver_node = deserialized_root_node.children[0]
        self.assertEqual(deserialized_solver_node.data.type, "zSolverTransform")
        self.assertEqual(deserialized_solver_node.data.name, "zSolver1")
        self.assertEqual(deserialized_solver_node.pin_state, TreeItem.Unpinned)
        deserialized_solver_shape_node = deserialized_solver_node.children[0]
        self.assertEqual(deserialized_solver_shape_node.data.type, "zSolver")
        self.assertEqual(deserialized_solver_shape_node.data.name, "zSolver1Shape")
        self.assertEqual(deserialized_solver_shape_node.pin_state, TreeItem.Unpinned)

        deserialized_group1_node = deserialized_solver_node.children[1]
        deserialized_group2_node = deserialized_solver_node.children[2]
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

    def test_data_serialization_with_non_root_node(self):
        """ Test serialization of multiple solver trees.
        """
        # Setup: construct tree structure as follows:
        # ROOT
        #   `- zSolver1Transform
        #     |- zSolver1
        #     |- group1
        #     |   - tissue1
        #   `- zSolver2Transform
        #     |- zSolver2
        #     |- group2
        #     |   - tissue2
        #   `- zSolver3Transform
        #     |- zSolver3
        #     |- tissue3
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
        # ROOT
        #   `- zSolver1Transform
        #     |- zSolver1
        #     |- group1
        #     |   - tissue1
        serialized_solver1_data = serialize_tree_model(solver1)

        # Verify
        self.assertEqual(type(serialized_solver1_data), list)
        self.assertEqual(len(serialized_solver1_data), 4)
        expected_result1 = [
            ["|zSolver1", 0, "zSolverTransform", {
                "pin_state": 0,
                "name": "|zSolver1",
            }],
            [
                "|zSolver1|zSolver1Shape", 0, "zSolver", {
                    "pin_state": 0,
                    "name": "|zSolver1|zSolver1Shape",
                }
            ],
            ["|zSolver1|group1", 1, "group", {}],
            [
                "|zSolver1|group1|tissue1", 0, "ui_zTissue_body", {
                    "pin_state": 0,
                    "name": "|tissue1",
                }
            ],
        ]
        print("serialized_solver1_data:", serialized_solver1_data)
        self.assertListEqual(expected_result1, serialized_solver1_data)

        # ---------------------------------------------------------------------
        # Action: serialized data for solver2 tree below
        # ROOT
        #   `- zSolver2Transform
        #     |- zSolver2
        #     |- group2
        #     |   - tissue2
        serialized_solver2_data = serialize_tree_model(solver2)

        # Verify
        self.assertEqual(len(serialized_solver2_data), 4)
        print("serialized_solver2_data:", serialized_solver2_data)
        expected_result2 = [
            ["|zSolver2", 1, "zSolverTransform", {
                "pin_state": 0,
                "name": "|zSolver2",
            }],
            [
                "|zSolver2|zSolver2Shape", 0, "zSolver", {
                    "pin_state": 0,
                    "name": "|zSolver2|zSolver2Shape",
                }
            ],
            ["|zSolver2|group2", 1, "group", {}],
            [
                "|zSolver2|group2|tissue2", 0, "ui_zTissue_body", {
                    "pin_state": 2,
                    "name": "|tissue2",
                }
            ],
        ]
        self.assertListEqual(expected_result2, serialized_solver2_data)

        # ---------------------------------------------------------------------
        # Action: serialized data for solver3 tree below
        # ROOT
        #   `- zSolver3Transform
        #     |- zSolver3
        #     |- tissue3
        serialized_solver3_data = serialize_tree_model(solver3)

        # Verify
        self.assertEqual(len(serialized_solver3_data), 3)
        print("serialized_solver3_data: ", serialized_solver3_data)
        expected_result3 = [
            ["|zSolver3", 2, "zSolverTransform", {
                "pin_state": 0,
                "name": "|zSolver3",
            }],
            [
                "|zSolver3|zSolver3Shape", 0, "zSolver", {
                    "pin_state": 0,
                    "name": "|zSolver3|zSolver3Shape",
                }
            ],
            ["|zSolver3|tissue3", 1, "ui_zTissue_body", {
                "pin_state": 0,
                "name": "|tissue3",
            }],
        ]
        self.assertListEqual(expected_result3, serialized_solver3_data)