import maya.cmds as mc
import maya.mel as mm

import os
import zBuilder.builders.ziva as zva
import tests.utils as test_utils
import zBuilder.utils as utils
import zBuilder.zMaya as mz

import maya.OpenMaya as om

from vfx_test_case import VfxTestCase


class ZivaSolverGenericTestCase(VfxTestCase):
    @classmethod
    def setUpClass(cls):
        pass

    def setUp(self):
        super(ZivaSolverGenericTestCase, self).setUp()
        test_utils.build_generic_scene()
        self.builder = zva.Ziva()
        self.builder.retrieve_from_scene()
        if 'MAYA_APP_DIR' in os.environ:
            self.temp_file_path = os.environ['MAYA_APP_DIR'].split(';')[0] + "/tmp.zBuilder"
        else:
            self.temp_file_path = os.path.expanduser("~").replace("\\", "/") + "/tmp.zBuilder"

    def tearDown(self):
        super(ZivaSolverGenericTestCase, self).tearDown()
        if os.path.exists(self.temp_file_path):
            os.remove(self.temp_file_path)

    def check_retrieve_zsolver_looks_good(self, builder, name, attrs):
        """Args:
            builder (builders.ziva.Ziva()): builder object
            name (string): name of the solver transform to check
            attrs (list): compares to stored zBuilder values for zSolver
                          if empty - getting values from the scene
        """
        # get solver from zBuilder
        solver_nodes = builder.get_scene_items(type_filter='zSolver')

        self.assertEqual(len(solver_nodes), 1)

        solver = solver_nodes[0]

        solver_attrs = ['substeps',
                        'gravityY',
                        'framesPerSecond']

        self.assertEqual(solver.name, name)
        self.assertEqual(solver.type, "zSolver")
        self.assertIsInstance(solver.mobject, om.MObject)

        for i, attr in enumerate(solver_attrs):
            if attrs:
                value = attrs[i]
            else:
                value = mc.getAttr("{}.{}".format(solver.name, attr))
            self.assertTrue(value == solver.attrs[attr]['value'])

    def check_retrieve_zsolver_transform_looks_good(self, builder, name, attrs):
        """Args:
            builder (builders.ziva.Ziva()): builder object
            name (string): name of the solver transform to check
            attrs (list): compares to stored zBuilder values for zSolverTransform
                          if empty - getting values from the scene
        """
        # get solver transform from zBuilder
        solver_transform_nodes = builder.get_scene_items(type_filter='zSolverTransform')

        self.assertEqual(len(solver_transform_nodes), 1)

        solver_transform = solver_transform_nodes[0]

        solver_transform_attrs = ['enable',
                                  'startFrame']

        solver_transform_children_expected = {'zSolver1Shape',
                                              'r_tissue_2',
                                              'c_tissue_3',
                                              'l_tissue_1',
                                              'bone_1',
                                              'bone_2',
                                              'cloth_1'}

        self.assertEqual(solver_transform.name, name)
        self.assertEqual(solver_transform.type, "zSolverTransform")
        self.assertIsInstance(solver_transform.mobject, om.MObject)

        for i, attr in enumerate(solver_transform_attrs):
            if attrs:
                value = attrs[i]
            else:
                value = mc.getAttr("{}.{}".format(solver_transform.name, attr))
            self.assertEqual(value, solver_transform.attrs[attr]['value'])

        solver_transform_children = {obj.name for obj in solver_transform.children}
        self.assertGreaterEqual(solver_transform_children,
                                solver_transform_children_expected)

    def test_retrieve(self):
        self.check_retrieve_zsolver_looks_good(self.builder, "zSolver1Shape", [])
        self.check_retrieve_zsolver_transform_looks_good(self.builder, "zSolver1", [])

    def check_solver_and_transform_looks_good(self, builder,
                                              solver_name,
                                              solver_transform_name):
        solver_nodes = builder.get_scene_items(type_filter='zSolver')
        self.assertEqual(len(solver_nodes), 1)

        solver = solver_nodes[0]
        self.assertEqual(solver.name, solver_name)
        self.assertEqual(solver.type, "zSolver")

        solver_transform_nodes = builder.get_scene_items(type_filter='zSolverTransform')
        self.assertEqual(len(solver_transform_nodes), 1)

        solver_transform = solver_transform_nodes[0]
        self.assertEqual(solver_transform.name, solver_transform_name)
        self.assertEqual(solver_transform.type, "zSolverTransform")

    def test_builder_has_same_solver_node_after_roundtrip_to_disk(self):
        self.builder.write(self.temp_file_path)
        self.assertTrue(os.path.exists(self.temp_file_path))

        builder = zva.Ziva()
        builder.retrieve_from_file(self.temp_file_path)
        self.check_solver_and_transform_looks_good(builder, "zSolver1Shape", "zSolver1")

    def test_build(self):
        solver_attrs = ['substeps',
                        'gravityY',
                        'framesPerSecond']

        solver_transform_attrs = ['enable',
                                  'startFrame']

        solver_values = []
        for attr in solver_attrs:
            value = mc.getAttr("{}.{}".format("zSolver1Shape", attr))
            solver_values.append(value)

        solver_transform_values = []
        for attr in solver_transform_attrs:
            value = mc.getAttr("{}.{}".format("zSolver1", attr))
            solver_transform_values.append(value)

        # remove all Ziva nodes from the scene and build them
        mz.clean_scene()
        self.builder.build()

        self.check_retrieve_zsolver_looks_good(self.builder, "zSolver1Shape", solver_values)
        self.check_retrieve_zsolver_transform_looks_good(self.builder,
                                                         "zSolver1",
                                                         solver_transform_values)

    def test_build_from_file(self):
        self.builder.write(self.temp_file_path)

        builder = zva.Ziva()
        builder.retrieve_from_file(self.temp_file_path)
        mz.clean_scene()
        builder.build()
        self.check_solver_and_transform_looks_good(builder, "zSolver1Shape", "zSolver1")


class ZivaSolverTestCase(VfxTestCase):
    @classmethod
    def setUpClass(cls):
        pass

    def setUp(self):
        super(ZivaSolverTestCase, self).setUp()

        self.results = mm.eval('ziva -s')

    def tearDown(self):
        super(ZivaSolverTestCase, self).tearDown()

    def test_rebuild_solver_shape_name(self):
        # tests the shape name when re-building a solver via zBuilder.

        mc.rename(self.results[1], 'zSolver_fat')

        # use builder to retrieve from scene-----------------------------------
        z = zva.Ziva()
        z.retrieve_from_scene()

        mc.delete('zSolver_fat')

        z.build()

        # get solver from zBuilder
        solver_node = z.get_scene_items(type_filter='zSolver')[0]

        self.assertSceneHasNodes([solver_node.name])

