import os
import zBuilder.builders.ziva as zva
import tests.utils as test_utils
from vfx_test_case import VfxTestCase
from maya import cmds

try:
    from PySide2 import QtCore
    from zBuilder.ui import model
    wrong_maya_version = False
except ImportError:
    wrong_maya_version = True

from zBuilder.nodes.dg_node import DGNode


class ZivaScenePanelTestCase(VfxTestCase):
    def setUp(self):
        if wrong_maya_version:
            self.skipTest('Maya version is not supported')
        super(ZivaScenePanelTestCase, self).setUp()
        test_utils.load_scene()
        builder = zva.Ziva()
        builder.retrieve_connections()
        self.model = model.SceneGraphModel(builder)

    def tearDown(self):
        if os.path.exists(self.temp_file_path):
            os.remove(self.temp_file_path)
        super(ZivaScenePanelTestCase, self).tearDown()

    def check_model_data_returns_right_types(self, index):
        name = self.model.data(index, QtCore.Qt.DisplayRole)
        self.assertIn(type(name), [unicode, str])

        node_type = self.model.data(index, self.model.sortRole)
        self.assertIn(type(node_type), [unicode, str])

        node = self.model.data(index, self.model.nodeRole)
        self.assertIsInstance(node, DGNode)

        long_name = self.model.data(index, self.model.longNameRole)
        self.assertIn(type(long_name), [unicode, str])

        enable = self.model.data(index, self.model.enableRole)
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

