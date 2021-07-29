from vfx_test_case import VfxTestCase
from zBuilder.scenePanel2.treeNode import TreeNode


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
