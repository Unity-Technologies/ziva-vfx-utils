import os
import zBuilder.builders.ziva as zva
import tests.utils as test_utils
try:
    from PySide2 import QtCore
except ImportError:
    from PySide import QtCore
from zBuilder.ui import model
from vfx_test_case import VfxTestCase
from zBuilder.nodes import base


class ZivaScenePanelTestCase(VfxTestCase):
    def setUp(self):
        super(ZivaScenePanelTestCase, self).setUp()
        test_utils.build_generic_scene()
        builder = zva.Ziva()
        builder.retrieve_connections()
        self.model = model.SceneGraphModel(builder.root_node)

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
        self.assertIsInstance(node, base.Base)

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
