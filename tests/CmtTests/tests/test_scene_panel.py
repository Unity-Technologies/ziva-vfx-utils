import zBuilder.builders.ziva as zva
import os

from tests.utils import load_scene
from vfx_test_case import VfxTestCase
from zBuilder.commonUtils import is_string
from zBuilder.ui.model import SceneGraphModel
from zBuilder.uiUtils import sortRole, nodeRole, longNameRole, enableRole, validate_group_node_name
from zBuilder.nodes.dg_node import DGNode
from PySide2 import QtCore
from maya import cmds


class ZivaScenePanelTestCase(VfxTestCase):
    def setUp(self):
        super(ZivaScenePanelTestCase, self).setUp()
        load_scene()
        builder = zva.Ziva()
        builder.retrieve_connections()
        self.model = SceneGraphModel(builder)

    def tearDown(self):
        if os.path.exists(self.temp_file_path):
            os.remove(self.temp_file_path)
        super(ZivaScenePanelTestCase, self).tearDown()

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

    def test_group_name_validation(self):
        """ Only starts with alphabet, digits and underscore are allowed after that.
        """
        self.assertTrue(validate_group_node_name("A1b2c"))
        self.assertTrue(validate_group_node_name("a1b2c_"))
        self.assertFalse(validate_group_node_name("1b2c_"))
        self.assertFalse(validate_group_node_name("_a1b2c_"))
        self.assertFalse(validate_group_node_name("abc**"))
