import zBuilder.builders.ziva as zva

from vfx_test_case import VfxTestCase
from zBuilder.scenePanel2.treeNode import TreeNode, build_scene_panel_tree
from zBuilder.nodes import SolverTransformNode, SolverNode, DGNode, MaterialNode
from zBuilder.nodes.base import Base
from zBuilder.builder import Builder
from maya import cmds


class ScenePanelTreeNodeTestCase(VfxTestCase):
    ''' Test TreeNode class used for Scene Panel tree view
    '''
    def test_basic_tree_node_behavior(self):
        ''' Test some basic tree data structure operations
        '''
        # Setup root node
        root = TreeNode()
        # Verify
        self.assertIsNone(root.parent)
        self.assertTrue(root.is_root_node())
        self.assertEqual(root.child_count(), 0)
        self.assertEqual(root.children, [])
        self.assertIsNone(root.data)

        # Action: create first child node
        child1 = TreeNode(root)
        # Verify
        self.assertIs(child1.parent, root)
        self.assertEqual(child1.children, [])
        self.assertIsNone(child1.data)
        self.assertEqual(root.child_count(), 1)

        # Action: create second child node
        child2 = TreeNode()
        child2.parent = root
        # Verify
        self.assertIs(child2.parent, root)
        self.assertEqual(child2.children, [])
        self.assertIsNone(child2.data)
        self.assertEqual(root.child_count(), 2)

        # Action: create grand child nodes
        grand_child1 = TreeNode(child1)
        grand_child2 = TreeNode()
        grand_child3 = TreeNode()
        child1.append_children([grand_child2, grand_child3])
        grand_child4 = TreeNode(child2)
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
        ''' Test some TreeNode member functions for Qt tree model API
        '''
        # Setup
        root = TreeNode()
        child1 = TreeNode(root)
        root.append_children([TreeNode(), TreeNode()])
        grand_child1 = TreeNode(child1)
        grand_child2 = TreeNode(child1)

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
        ''' Verify build_scene_panel_tree() function's node_type_filter parameter
        Create a tissue with 2 material nodes.
        Use node_type_filter to create a tree structure as follows:
        ROOT
          `- Tissue
               |- Material1
               `- Material2
        '''
        # Setup
        cmds.polyCube(n='tissue')
        cmds.ziva('tissue', t=True)
        cmds.ziva(m=True)  # Add second material
        builder = zva.Ziva()
        builder.retrieve_connections()

        # Action
        sp_root_tree_node = build_scene_panel_tree(builder, ['ui_zTissue_body', 'zMaterial'])

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
