import zBuilder.builders.ziva as zva

from maya import cmds
from vfx_test_case import VfxTestCase
from zBuilder.nodes import SolverTransformNode, SolverNode, DGNode, MaterialNode
from zBuilder.nodes.base import Base
from zBuilder.builders.builder import Builder
from scenePanel.scenePanel2.groupNode import GroupNode
from scenePanel.scenePanel2.treeItem import TreeItem, build_scene_panel_tree, create_subtree
from scenePanel.scenePanel2.treeItem import pick_out_node, is_node_name_duplicate, fix_node_name_duplication


class ScenePanelTreeNodeTestCase(VfxTestCase):
    """ Test TreeItem class used for Scene Panel tree view
    """

    def test_basic_tree_node_behavior(self):
        """ Test some basic tree data structure operations
        """
        # Setup root node
        root = TreeItem(None, Base())
        # Verify
        self.assertIsNone(root.parent)
        self.assertTrue(root.is_root_node())
        self.assertEqual(root.child_count(), 0)
        self.assertEqual(root.children, [])
        self.assertIs(type(root.data), Base)

        # Action: create first child node
        child1 = TreeItem(root)
        # Verify
        self.assertIs(child1.parent, root)
        self.assertEqual(child1.children, [])
        self.assertIsNone(child1.data)
        self.assertEqual(root.child_count(), 1)

        # Action: create second child node
        child2 = TreeItem()
        child2.parent = root
        # Verify
        self.assertIs(child2.parent, root)
        self.assertEqual(child2.children, [])
        self.assertIsNone(child2.data)
        self.assertEqual(root.child_count(), 2)

        # Action: create grand child nodes
        grand_child1 = TreeItem(child1)
        grand_child2 = TreeItem()
        grand_child3 = TreeItem()
        child1.append_children([grand_child2, grand_child3])
        grand_child4 = TreeItem(child2)
        # Verify
        self.assertEqual(child1.child_count(), 3)
        self.assertEqual(child2.child_count(), 1)

        # Action: move grand child 3 from child1 to child2
        child2.append_children(grand_child3)
        # Verify
        self.assertEqual(child1.child_count(), 2)
        self.assertEqual(child2.child_count(), 2)
        self.assertCountsEqual(child1.children, (grand_child1, grand_child2))
        self.assertCountsEqual(child2.children, (grand_child3, grand_child4))

        # Action: remove grand child 3
        child2.remove_children(grand_child3)
        self.assertEqual(child2.child_count(), 1)
        self.assertCountsEqual(child2.children, (grand_child4, ))
        self.assertIsNone(grand_child3.parent)

    def test_tree_node_functions_for_qt(self):
        """ Test some TreeItem member functions for Qt tree model API
        """
        # Setup
        root = TreeItem()
        child1 = TreeItem(root)
        root.append_children([TreeItem(), TreeItem()])
        grand_child1 = TreeItem(child1)
        grand_child2 = TreeItem(child1)

        # Verify
        self.assertEqual(root.child_count(), 3)
        self.assertIs(root.child(0), child1)
        self.assertEqual(child1.child_count(), 2)
        self.assertEqual(child1.row(), 0)
        self.assertIs(child1.child(0), grand_child1)
        self.assertIs(child1.child(1), grand_child2)
        self.assertEqual(grand_child1.row(), 0)
        self.assertEqual(grand_child2.row(), 1)

    def test_build_treenode_with_empty_solver(self):
        # Setup
        # Create an empty solver and retrieve it
        cmds.ziva(s=True)
        builder = zva.Ziva()
        builder.retrieve_connections()

        # Action
        sp_root_tree_node = build_scene_panel_tree(builder)

        # Verify
        self.assertIsNotNone(sp_root_tree_node)
        sp_root_tree_node = sp_root_tree_node[0]
        self.assertTrue(sp_root_tree_node.is_root_node())
        self.assertEqual(sp_root_tree_node.child_count(), 1)

        solver_transform_tree_node = sp_root_tree_node.children[0]
        self.assertFalse(solver_transform_tree_node.is_root_node())
        self.assertEqual(solver_transform_tree_node.child_count(), 1)
        solver_transform_data = solver_transform_tree_node.data
        self.assertIsInstance(solver_transform_data, SolverTransformNode)

        solver_tree_node = solver_transform_tree_node.children[0]
        self.assertEqual(solver_tree_node.child_count(), 0)
        solver_data = solver_tree_node.data
        self.assertIsInstance(solver_data, SolverNode)

        self.assertTrue(isinstance(DGNode(), Base))
        self.assertTrue(isinstance(zva.Ziva(), Builder))

    def test_build_treenode_with_node_type_filter(self):
        """ Verify build_scene_panel_tree() function"s node_type_filter parameter
        Create a tissue with 2 material nodes.
        Use node_type_filter to create a tree structure as follows:
        ROOT
          `- Tissue
               |- Material1
               `- Material2
        """
        # Setup
        cmds.polyCube(n="tissue")
        cmds.ziva("tissue", t=True)
        cmds.ziva(m=True)  # Add second material
        builder = zva.Ziva()
        builder.retrieve_connections()

        # Action
        sp_root_tree_node = build_scene_panel_tree(builder, ["ui_zTissue_body", "zMaterial"])

        # Verify
        self.assertIsNotNone(sp_root_tree_node)
        sp_root_tree_node = sp_root_tree_node[0]
        self.assertTrue(sp_root_tree_node.is_root_node())
        self.assertEqual(sp_root_tree_node.child_count(), 1)

        tissue_tree_node = sp_root_tree_node.children[0]
        self.assertFalse(tissue_tree_node.is_root_node())
        self.assertEqual(tissue_tree_node.child_count(), 2)
        tissue_data = tissue_tree_node.data
        # Maya mesh is a DGNode, not a zTissue node
        self.assertIsInstance(tissue_data, DGNode)

        for material_tree_node in tissue_tree_node.children:
            self.assertEqual(material_tree_node.child_count(), 0)
            material_data = material_tree_node.data
            self.assertIsInstance(material_data, MaterialNode)


class ScenePanelGroupNodeTestCase(VfxTestCase):
    """ Test group node related operations
    """

    def test_group_selected_nodes(self):
        """ Setup some nested group nodes,
        create a new group node that includes some of them.
        """
        # Setup: construct tree structure as follows:
        # ROOT
        #   `- zSolverTransform
        #     |- zSolver
        #     |- Group1
        #     |  `- Subgroup1
        #     |    `- Subsubgroup1
        #     |      `- tissue1
        #     `- Group2
        #       `- Subgroup2
        #         `- tissue2
        cmds.polyCube(n="tissue1")
        cmds.polyCube(n="tissue2")
        cmds.ziva("tissue1", "tissue2", t=True)
        # Clear last created nodes so zBuilder can retrieve all nodes
        cmds.select(cl=True)
        builder = zva.Ziva()
        builder.retrieve_connections()
        root_node = build_scene_panel_tree(builder)[0]
        solverTM_node = root_node.children[0]
        child_nodes = solverTM_node.children
        # child_nodes[0] is zSolver node
        tissue1_node = child_nodes[1]
        tissue2_node = child_nodes[2]
        self.assertEqual(tissue1_node.data.type, "ui_zTissue_body")
        self.assertEqual(tissue1_node.data.name, "tissue1")
        self.assertEqual(tissue2_node.data.type, "ui_zTissue_body")
        self.assertEqual(tissue2_node.data.name, "tissue2")
        # Create nested group nodes
        group1_node = TreeItem(solverTM_node, GroupNode("Group1"))
        subgroup1_node = TreeItem(group1_node, GroupNode("Subgroup1"))
        subsubgroup1_node = TreeItem(subgroup1_node, GroupNode("Subsubgroup1"))
        subsubgroup1_node.append_children(tissue1_node)
        group2_node = TreeItem(solverTM_node, GroupNode("Group2"))
        subgroup2_node = TreeItem(group2_node, GroupNode("Subgroup2"))
        subgroup2_node.append_children(tissue2_node)

        # Action: build subtree with selected nodes
        # The selected nodes contains nested child nodes that should not be re-parented.
        group3_node = create_subtree(
            [tissue1_node, subgroup1_node, tissue2_node, subsubgroup1_node, subgroup2_node],
            GroupNode("Group3"))

        # Verify: Expected tree structure after action:
        # ROOT
        #   `- zSolverTransform
        #     |- zSolver
        #     |- Group1
        #     `- Group2
        #
        # The newly created Group3 node structure:
        # Group3
        #   |- Subgroup1
        #   | `- Subsubgroup1
        #   |    `- tissue1
        #   `- Subgroup2
        #     `- tissue2

        # Group1 and Group2 lose their children
        self.assertEqual(len(group1_node.children), 0)
        self.assertEqual(len(group2_node.children), 0)
        # Check Group3's children
        self.assertIsNone(group3_node.parent)  # Group3 has not parented yet
        self.assertEqual(len(group3_node.children), 2)
        self.assertIs(group3_node.children[0], subgroup1_node)
        self.assertIs(group3_node.children[1], subgroup2_node)
        self.assertEqual(len(subgroup1_node.children), 1)
        self.assertIs(subgroup1_node.children[0], subsubgroup1_node)
        self.assertEqual(len(subsubgroup1_node.children), 1)
        self.assertIs(subsubgroup1_node.children[0], tissue1_node)
        self.assertEqual(len(subgroup2_node.children), 1)
        self.assertIs(subgroup2_node.children[0], tissue2_node)

    def test_delete_group_nodes(self):
        """ Setup some nested group nodes,
        delete some group nodes while move their descendants to the existing position.
        Auto renaming shall apply when name conflict happens.
        """
        # Setup: construct tree structure as follows:
        # ROOT
        #   `- zSolverTransform
        #     |- zSolver
        #     |- Group1
        #     |  `- Subgroup1
        #     |    `- Subgroup1
        #     |      `- tissue1
        #     `- Group2
        #       `- Subgroup1
        #         `- tissue2
        cmds.polyCube(n="tissue1")
        cmds.polyCube(n="tissue2")
        cmds.ziva("tissue1", "tissue2", t=True)
        # Clear last created nodes so zBuilder can retrieve all nodes
        cmds.select(cl=True)
        builder = zva.Ziva()
        builder.retrieve_connections()
        root_node = build_scene_panel_tree(builder)[0]
        solverTM_node = root_node.children[0]
        child_nodes = solverTM_node.children
        # child_nodes[0] is zSolver node
        tissue1_node = child_nodes[1]
        tissue2_node = child_nodes[2]
        self.assertEqual(tissue1_node.data.type, "ui_zTissue_body")
        self.assertEqual(tissue1_node.data.name, "tissue1")
        self.assertEqual(tissue2_node.data.type, "ui_zTissue_body")
        self.assertEqual(tissue2_node.data.name, "tissue2")
        # Create nested group nodes
        group1_node = TreeItem(solverTM_node, GroupNode("Group1"))
        subgroup1_node = TreeItem(group1_node, GroupNode("Subgroup1"))
        subsubgroup1_node = TreeItem(subgroup1_node, GroupNode("Subgroup1"))
        subsubgroup1_node.append_children(tissue1_node)
        group2_node = TreeItem(solverTM_node, GroupNode("Group2"))
        subgroup2_node = TreeItem(group2_node, GroupNode("Subgroup1"))
        subgroup2_node.append_children(tissue2_node)

        # Action: delete some Group nodes
        # Note: Order of nodes to delete matters because the node name may conflict and
        # auto renaming applies to the latter nodes.
        pick_out_nodes = [group2_node, subgroup1_node, group1_node]
        for node in pick_out_nodes:
            pick_out_node(node, is_node_name_duplicate, fix_node_name_duplication)

        # Verify: Expected tree structure after action:
        # ROOT
        #   `- zSolverTransform
        #     |- zSolver
        #     |- Subgroup1
        #     |  `- tissue2
        #     `- Subgroup2
        #        `- tissue1

        # The zSolverTM still has 3 children
        self.assertEqual(len(child_nodes), 3)
        self.assertIs(child_nodes[1], subsubgroup1_node)
        self.assertIs(child_nodes[2], subgroup2_node)

        # Subsubgroup is escalated
        self.assertEqual(subsubgroup1_node.data.name, "Subgroup2")
        self.assertEqual(len(subsubgroup1_node.children), 1)
        self.assertIs(subsubgroup1_node.children[0], tissue1_node)

        self.assertEqual(subgroup2_node.data.name, "Subgroup1")
        self.assertEqual(len(subgroup2_node.children), 1)
        self.assertIs(subgroup2_node.children[0], tissue2_node)

    def test_move_child_nodes(self):
        """ Test move multiple consecutive or separate child nodes
        """
        # Setup: construct tree structure as follows:
        # ROOT
        #   `- zSolverTransform
        #     |- zSolver
        #     |- tissue1
        #     |- tissue2
        #     |- tissue3
        #     `- tissue4
        for i in range(4):
            tissue_name = "tissue{}".format(i + 1)
            cmds.polyCube(n=tissue_name)
            cmds.ziva(tissue_name, t=True)
        # Clear last created nodes so zBuilder can retrieve all nodes
        cmds.select(cl=True)
        builder = zva.Ziva()
        builder.retrieve_connections()
        root_node = build_scene_panel_tree(builder)[0]
        solverTM_node = root_node.children[0]
        child_nodes = solverTM_node.children
        # child_nodes[0] is zSolver node
        self.assertEqual(solverTM_node.child_count(), 5)
        tissue_nodes = child_nodes[1:]
        for i in range(4):
            tissue_name = "tissue{}".format(i + 1)
            self.assertEqual(tissue_nodes[i].data.type, "ui_zTissue_body")
            self.assertEqual(tissue_nodes[i].data.name, tissue_name)

        # ---------------------------------------------------------------------
        # Action: group tissue1, tissue2 to group1 node
        group1_node = TreeItem(solverTM_node, GroupNode("Group1"))
        group1_node.insert_children(0, tissue_nodes[:2])
        # Verify
        # ROOT
        #   `- zSolverTransform
        #     |- zSolver
        #     |- Group1
        #     |    |- tissue1
        #     |    `- tissue2
        #     |- tissue3
        #     `- tissue4
        self.assertEqual(len(child_nodes), 4)
        self.assertEqual(group1_node.child_count(), 2)
        self.assertIs(group1_node.children[0], tissue_nodes[0])
        self.assertIs(group1_node.children[1], tissue_nodes[1])

        # ---------------------------------------------------------------------
        # Action: group tissue3, tissue4 to group2/subgroup1 node
        group2_node = TreeItem(solverTM_node, GroupNode("Group2"))
        subgroup1_node = TreeItem(group2_node, GroupNode("Subgroup1"))
        subgroup1_node.insert_children(0, tissue_nodes[2:])
        # Verify
        # ROOT
        #   `- zSolverTransform
        #     |- zSolver
        #     |- Group1
        #     |    |- tissue1
        #     |    `- tissue2
        #     `- Group2
        #        `- Subgroup1
        #           |- tissue3
        #           `- tissue4
        self.assertEqual(len(child_nodes), 3)
        self.assertEqual(group2_node.child_count(), 1)
        self.assertEqual(subgroup1_node.child_count(), 2)
        self.assertIs(subgroup1_node.children[0], tissue_nodes[2])
        self.assertIs(subgroup1_node.children[1], tissue_nodes[3])

        # ---------------------------------------------------------------------
        # Action: Move tissue3, tissue1 to group2 node
        group2_node.insert_children(0, [tissue_nodes[2], tissue_nodes[0]])
        # Verify
        # ROOT
        #   `- zSolverTransform
        #     |- zSolver
        #     |- Group1
        #     |  `- tissue2
        #     `- Group2
        #        |- tissue3
        #        |- tissue1
        #        `- Subgroup1
        #           `- tissue4
        self.assertEqual(group1_node.child_count(), 1)
        self.assertIs(group1_node.children[0], tissue_nodes[1])
        self.assertEqual(subgroup1_node.child_count(), 1)
        self.assertIs(subgroup1_node.children[0], tissue_nodes[3])
        self.assertEqual(group2_node.child_count(), 3)
        self.assertIs(group2_node.children[0], tissue_nodes[2])
        self.assertIs(group2_node.children[1], tissue_nodes[0])

    def test_tree_path_from_builder(self):
        """ Test tree path generates correct result when moved around
        """
        # Verify get_tree_path() returns correct paths for the tree below
        # ROOT
        #   `- zSolverTransform
        #     |- zSolver
        #     |- Group1
        #     |- tissue1

        # generate above tree model
        cmds.polyCube(n="tissue1")
        cmds.ziva("tissue1", t=True)
        # Clear last created nodes so zBuilder can retrieve all nodes
        cmds.select(cl=True)
        builder = zva.Ziva()
        builder.retrieve_connections()
        root_node = build_scene_panel_tree(builder)[0]
        self.assertEqual(root_node.get_tree_path(), "|")
        solver_node = root_node.children[0]
        self.assertEqual(solver_node.get_tree_path(), "|zSolver1")
        solverShape_node = solver_node.children[0]
        self.assertEqual(solverShape_node.get_tree_path(), "|zSolver1|zSolver1Shape")
        tissue1_node = solver_node.children[1]
        self.assertEqual(tissue1_node.get_tree_path(), "|zSolver1|tissue1")

        # Add group and test path
        group1_node = TreeItem(solver_node, GroupNode("Group1"))
        self.assertEqual(group1_node.get_tree_path(), "|zSolver1|Group1")

        # Verify after moving items of the existing tree,
        # get_tree_path() returns right results.
        # ROOT
        #   `- zSolverTransform
        #     |- zSolver
        #     |- Group1
        #     |  - Group1
        #     |  - tissue1
        new_group1_node = TreeItem(solver_node, GroupNode("Group1"))
        new_group1_node.insert_children(0, group1_node)
        self.assertEqual(new_group1_node.child_count(), 1)
        new_group1_node.insert_children(1, tissue1_node)
        self.assertEqual(new_group1_node.child_count(), 2)
        self.assertEqual(new_group1_node.get_tree_path(), "|zSolver1|Group1")
        self.assertEqual(group1_node.get_tree_path(), "|zSolver1|Group1|Group1")
        self.assertEqual(tissue1_node.get_tree_path(), "|zSolver1|Group1|tissue1")

    def test_tree_path_from_solverTM(self):
        """ Test tree path from partial retrieve result
        """
        # Verify get_tree_path() returns correct paths for the tree below
        # ROOT
        #   `- zSolverTransform   <-- Provide TM node as root
        #     |- zSolver
        #     |- Group1
        #     |- tissue1

        # generate above tree model
        cmds.polyCube(n="tissue1")
        cmds.ziva("tissue1", t=True)
        # Clear last created nodes so zBuilder can retrieve all nodes
        cmds.select(cl=True)
        builder = zva.Ziva()
        builder.retrieve_connections()
        solverTM_node = builder.get_scene_items(type_filter="zSolverTransform")[0]
        solver_node = build_scene_panel_tree(solverTM_node)[0]
        self.assertEqual(solver_node.get_tree_path(), "|zSolver1")
        solverShape_node = solver_node.children[0]
        self.assertEqual(solverShape_node.get_tree_path(), "|zSolver1|zSolver1Shape")
        tissue1_node = solver_node.children[1]
        self.assertEqual(tissue1_node.get_tree_path(), "|zSolver1|tissue1")

        # Add group and test path
        group1_node = TreeItem(solver_node, GroupNode("Group1"))
        self.assertEqual(group1_node.get_tree_path(), "|zSolver1|Group1")


class ScenePanelPinStateTestCase(VfxTestCase):
    """ Test TreeItem pin state logic
    """

    def test_treeitem_pin_state(self):
        """ Test all kinds of pin state changes on different TreeItem structure
        """
        # Setup: construct tree structure as follows:
        # ROOT
        #   `- zSolverTransform
        #     |- zSolver
        #     |- Group1
        #     |  |- Subgroup1
        #     |  |   |- tissue1
        #     |  |   `- tissue2
        #     |  `- Subgroup2
        #     |      `- tissue3
        #     |- Group2
        #     `- tissue4
        for i in range(4):
            tissue_name = "tissue{}".format(i + 1)
            cmds.polyCube(n=tissue_name)
            cmds.ziva(tissue_name, t=True)
        # Clear last created nodes so zBuilder can retrieve all nodes
        cmds.select(cl=True)
        builder = zva.Ziva()
        builder.retrieve_connections()
        root_node = build_scene_panel_tree(builder)[0]
        solverTM_node = root_node.children[0]
        child_nodes = solverTM_node.children
        # child_nodes[0] is zSolver node
        tissue_nodes = child_nodes[1:]
        for i in range(4):
            tissue_name = "tissue{}".format(i + 1)
            self.assertEqual(tissue_nodes[i].data.type, "ui_zTissue_body")
            self.assertEqual(tissue_nodes[i].data.name, tissue_name)

        # Create group nodes
        group1_node = TreeItem(solverTM_node, GroupNode("Group1"))
        subgroup1_node = TreeItem(group1_node, GroupNode("Subgroup1"))
        subgroup2_node = TreeItem(group1_node, GroupNode("Subgroup2"))
        subgroup1_node.append_children([tissue_nodes[0], tissue_nodes[1]])
        subgroup2_node.append_children(tissue_nodes[2])
        group2_node = TreeItem(solverTM_node, GroupNode("Group2"))

        # ---------------------------------------------------------------------
        # Action 1
        # Check init state
        self.assertEqual(tissue_nodes[3].pin_state, TreeItem.Unpinned)
        self.assertEqual(group2_node.pin_state, TreeItem.Unpinned)
        # Pin tissue4 and Group2
        tissue_nodes[3].pin_state = TreeItem.Pinned
        group2_node.pin_state = TreeItem.Pinned
        # Verify
        self.assertEqual(tissue_nodes[3].pin_state, TreeItem.Pinned)
        self.assertEqual(group2_node.pin_state, TreeItem.Pinned)
        # Unpin tissue4 and Group2
        tissue_nodes[3].pin_state = TreeItem.Unpinned
        group2_node.pin_state = TreeItem.Unpinned
        # Verify
        self.assertEqual(tissue_nodes[3].pin_state, TreeItem.Unpinned)
        self.assertEqual(group2_node.pin_state, TreeItem.Unpinned)

        # ---------------------------------------------------------------------
        # Action 2
        # Check init state
        self.assertEqual(group1_node.pin_state, TreeItem.Unpinned)
        self.assertEqual(subgroup2_node.pin_state, TreeItem.Unpinned)
        self.assertEqual(tissue_nodes[2].pin_state, TreeItem.Unpinned)
        # Pin tissue3 to trigger Subgroup2 and Group1 pin state change
        tissue_nodes[2].pin_state = TreeItem.Pinned
        # Verify
        self.assertEqual(group1_node.pin_state, TreeItem.PartiallyPinned)
        self.assertEqual(subgroup2_node.pin_state, TreeItem.Pinned)
        self.assertEqual(tissue_nodes[2].pin_state, TreeItem.Pinned)
        # Unpin tissue3 to trigger Subgroup2 and Group1 pin state change
        tissue_nodes[2].pin_state = TreeItem.Unpinned
        # Verify
        self.assertEqual(group1_node.pin_state, TreeItem.Unpinned)
        self.assertEqual(subgroup2_node.pin_state, TreeItem.Unpinned)
        self.assertEqual(tissue_nodes[2].pin_state, TreeItem.Unpinned)

        # ---------------------------------------------------------------------
        # Action 3
        # Check init state
        self.assertEqual(group1_node.pin_state, TreeItem.Unpinned)
        self.assertEqual(subgroup1_node.pin_state, TreeItem.Unpinned)
        self.assertEqual(tissue_nodes[0].pin_state, TreeItem.Unpinned)
        self.assertEqual(tissue_nodes[1].pin_state, TreeItem.Unpinned)
        self.assertEqual(subgroup2_node.pin_state, TreeItem.Unpinned)
        self.assertEqual(tissue_nodes[2].pin_state, TreeItem.Unpinned)
        # Pin group1 to change all its descendants pin state
        group1_node.pin_state = TreeItem.Pinned
        # Verify
        self.assertEqual(group1_node.pin_state, TreeItem.Pinned)
        self.assertEqual(subgroup1_node.pin_state, TreeItem.Pinned)
        self.assertEqual(tissue_nodes[0].pin_state, TreeItem.Pinned)
        self.assertEqual(tissue_nodes[1].pin_state, TreeItem.Pinned)
        self.assertEqual(subgroup2_node.pin_state, TreeItem.Pinned)
        self.assertEqual(tissue_nodes[2].pin_state, TreeItem.Pinned)
        # Unpin subgroup1 to trigger its descendants and Group1 pin state change
        subgroup1_node.pin_state = TreeItem.Unpinned
        # Verify
        self.assertEqual(group1_node.pin_state, TreeItem.PartiallyPinned)
        self.assertEqual(subgroup1_node.pin_state, TreeItem.Unpinned)
        self.assertEqual(tissue_nodes[0].pin_state, TreeItem.Unpinned)
        self.assertEqual(tissue_nodes[1].pin_state, TreeItem.Unpinned)
        self.assertEqual(subgroup2_node.pin_state, TreeItem.Pinned)
        self.assertEqual(tissue_nodes[2].pin_state, TreeItem.Pinned)
