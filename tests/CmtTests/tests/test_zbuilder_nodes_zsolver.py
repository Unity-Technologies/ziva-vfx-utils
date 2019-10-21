import maya.cmds as mc
import maya.mel as mm

import os
import zBuilder.builders.ziva as zva
import tests.utils as test_utils

import maya.OpenMaya as om

from vfx_test_case import VfxTestCase

current_directory_path = os.path.dirname(os.path.realpath(__file__))


class ZivaSolverNoChangesTestCase(VfxTestCase):
    """
    This class requires to have test that are not modify scene and zBuilder data
    """
    @classmethod
    def setUpClass(self):
        test_utils.build_generic_scene()
        self.builder = zva.Ziva()
        self.builder.retrieve_from_scene()

    def setUp(self):
        super(ZivaSolverNoChangesTestCase, self).setUp()

    def tearDown(self):
        super(ZivaSolverNoChangesTestCase, self).tearDown()

    def test_retrieve(self):
        # get solver from zBuilder
        solver_nodes = self.builder.get_scene_items(type_filter='zSolver')

        self.assertTrue(len(solver_nodes) == 1)

        solver = solver_nodes[0]
        solver_transform = solver.parent

        solver_attrs = ['substeps',
                        'gravityY',
                        'framesPerSecond']

        solver_transform_attrs = ['enable',
                                  'startFrame']

        solver_transform_children_expected = ['zSolver1Shape',
                                              'r_tissue_2',
                                              'c_tissue_3',
                                              'l_tissue_1',
                                              'bone_1',
                                              'bone_2',
                                              'cloth_1']

        self.assertTrue(solver.name == "zSolver1Shape")
        self.assertTrue(solver.type == "zSolver")
        self.assertTrue(isinstance(solver.mobject, om.MObject))

        for attr in solver_attrs:
            value = mc.getAttr("{}.{}".format(solver.name, attr))
            self.assertTrue(value == solver.attrs[attr]['value'])

        self.assertTrue(solver_transform.name == "zSolver1")
        self.assertTrue(solver_transform.type == "zSolverTransform")
        self.assertTrue(isinstance(solver_transform.mobject, om.MObject))

        for attr in solver_transform_attrs:
            value = mc.getAttr("{}.{}".format(solver_transform.name, attr))
            self.assertTrue(value == solver_transform.attrs[attr]['value'])

        solver_transform_children = [obj.name for obj in solver_transform.children]
        for child in solver_transform_children_expected:
            self.assertTrue(child in solver_transform_children)

    def test_write_read(self):
        temp_file_path = current_directory_path + "/tmp.zBuilder"
        self.builder.write(temp_file_path)

        self.assertTrue(os.path.exists(temp_file_path))

        builder = zva.Ziva()
        builder.retrieve_from_file(temp_file_path)

        solver_nodes = builder.get_scene_items(type_filter='zSolver')

        self.assertTrue(len(solver_nodes) == 1)

        solver = solver_nodes[0]
        solver_transform_nodes = builder.get_scene_items(type_filter='zSolverTransform')

        solver_transform = solver_transform_nodes[0]

        self.assertTrue(solver.name == "zSolver1Shape")
        self.assertTrue(solver.type == "zSolver")

        self.assertTrue(solver_transform.name == "zSolver1")
        self.assertTrue(solver_transform.type == "zSolverTransform")

        os.remove(temp_file_path)


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

