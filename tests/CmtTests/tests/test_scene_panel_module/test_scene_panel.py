import zBuilder.builders.ziva as zva
import os

from maya import cmds
from PySide2 import QtCore
from vfx_test_case import VfxTestCase
from tests.utils import load_scene
from zBuilder.utils.commonUtils import is_string
from zBuilder.nodes.dg_node import DGNode
from scenePanel.uiUtils import (validate_group_node_name, get_zSolverTransform_treeitem, sortRole,
                                nodeRole, longNameRole, enableRole)
from scenePanel.ui.model import SceneGraphModel
from scenePanel.scenePanel2.groupNode import GroupNode
from scenePanel.scenePanel2.treeItem import TreeItem, build_scene_panel_tree


class ScenePanelTestCase(VfxTestCase):

    def setUp(self):
        super(ScenePanelTestCase, self).setUp()
        load_scene("generic.ma")
        builder = zva.Ziva()
        builder.retrieve_connections()
        self.model = SceneGraphModel(builder)

    def tearDown(self):
        if os.path.exists(self.temp_file_path):
            os.remove(self.temp_file_path)
        super(ScenePanelTestCase, self).tearDown()

    def check_model_data_returns_right_types(self, index):
        name = self.model.data(index, QtCore.Qt.DisplayRole)
        self.assertTrue(is_string(name))

        node_type = self.model.data(index, sortRole)
        self.assertTrue(is_string(node_type))

        node = self.model.data(index, nodeRole)
        self.assertIsInstance(node, DGNode)

        long_name = self.model.data(index, longNameRole)
        self.assertTrue(is_string(long_name))

        enable = self.model.data(index, enableRole)
        self.assertIn(enable, [True, False, 0, 1])

    def recursive_check_model_data_returns_right_types(self, index):
        row_count = self.model.rowCount(index)
        if row_count:
            for i in range(row_count):
                child_index = index.child(i, 0)
                self.check_model_data_returns_right_types(index)
                self.recursive_check_model_data_returns_right_types(child_index)
        else:
            self.check_model_data_returns_right_types(index)

    def test_model_data_returns_right_types(self):
        root_index = self.model.index(0, 0, QtCore.QModelIndex())
        self.recursive_check_model_data_returns_right_types(root_index)

    def test_set_data_rename_node(self):
        ## SETUP
        root_index = self.model.index(0, 0, QtCore.QModelIndex())
        # This should be zSolver transform
        child_index = root_index.child(1, 0)
        ## VERIFY
        self.assertEqual(len(cmds.ls("zSolver1")), 1)
        self.assertEqual(len(cmds.ls("renamed_zSolver")), 0)

        ## ACT
        result = self.model.setData(child_index, "renamed_zSolver")

        ## VERIFY
        # check if index is valid
        self.assertTrue(result)
        # new node exists
        self.assertEqual(len(cmds.ls("renamed_zSolver")), 1)
        # zBuilder node has a new name
        node = child_index.internalPointer()
        self.assertEqual(node.name, "renamed_zSolver")


class ScenePanel2UtilityTestCase(VfxTestCase):
    """ Test Scene Panel 2 helper functions
    """

    def test_group_name_validation(self):
        """ Check validate_group_node_name() function logic.
        Group node name only starts with alphabet,
        digits and underscore are allowed after that.
        """
        self.assertTrue(validate_group_node_name("A1b2c"))
        self.assertTrue(validate_group_node_name("a1b2c_"))
        self.assertFalse(validate_group_node_name("1b2c_"))
        self.assertFalse(validate_group_node_name("_a1b2c_"))
        self.assertFalse(validate_group_node_name("abc**"))
        self.assertFalse(validate_group_node_name("not valid"))

    def test_get_zSolverTransform_treeitem_function(self):
        """ Check get_zSolverTransform_treeitem() function logic
        """
        # Setup: construct tree structure as follows:
        # ROOT
        #   |- zSolver1
        #   | |- zSolver1Shape
        #   | `- Group1
        #   |   `- Subgroup1
        #   |     `- tissue1
        #   `- zSolver2
        #     |- zSolver2Shape
        #     `- Group2
        #       `- Subgroup2
        #         `- tissue2
        cmds.polyCube(n="tissue1")
        cmds.polyCube(n="tissue2")
        cmds.ziva("tissue1", t=True)  # First solver with tissue1
        # Create second solver with tissue2
        cmds.ziva(s=True)
        cmds.ziva("tissue2", t=True)
        # Clear last created nodes so zBuilder can retrieve all nodes
        cmds.select(cl=True)
        builder = zva.Ziva()
        builder.retrieve_connections()
        root_node = build_scene_panel_tree(builder)[0]
        self.assertEqual(len(root_node.children), 2)
        solverTM1 = root_node.children[0]
        tissue1_node = solverTM1.children[1]  # solverTM1.children[0] is zSolver node
        solverTM2 = root_node.children[1]
        tissue2_node = solverTM2.children[1]
        self.assertEqual(tissue1_node.data.type, "ui_zTissue_body")
        self.assertEqual(tissue1_node.data.name, "tissue1")
        self.assertEqual(tissue2_node.data.type, "ui_zTissue_body")
        self.assertEqual(tissue2_node.data.name, "tissue2")
        # Create nested group nodes
        group1_node = TreeItem(solverTM1, GroupNode("Group1"))
        subgroup1_node = TreeItem(group1_node, GroupNode("Subgroup1"))
        subgroup1_node.append_children(tissue1_node)
        group2_node = TreeItem(solverTM2, GroupNode("Group2"))
        subgroup2_node = TreeItem(group2_node, GroupNode("Subgroup2"))
        subgroup2_node.append_children(tissue2_node)

        # Action
        result1 = get_zSolverTransform_treeitem(group1_node)
        result2 = get_zSolverTransform_treeitem(subgroup1_node)
        result3 = get_zSolverTransform_treeitem(tissue1_node)
        combined_result1 = list(set([result1, result2, result3]))

        result4 = get_zSolverTransform_treeitem(group2_node)
        result5 = get_zSolverTransform_treeitem(subgroup2_node)
        result6 = get_zSolverTransform_treeitem(tissue2_node)
        combined_result2 = list(set([result4, result5, result6]))

        # Verify
        self.assertEqual(len(combined_result1), 1)
        self.assertIs(combined_result1[0], solverTM1)
        self.assertEqual(len(combined_result2), 1)
        self.assertIs(combined_result2[0], solverTM2)

        # Verify: return None for invalid treeitem
        result7 = get_zSolverTransform_treeitem(TreeItem(None, GroupNode("Isolate node")))
        self.assertIsNone(result7)
