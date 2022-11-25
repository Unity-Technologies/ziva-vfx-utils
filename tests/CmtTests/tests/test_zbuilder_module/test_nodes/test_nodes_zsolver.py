import os
import zBuilder.builders.ziva as zva

from maya import cmds
from maya import mel
from vfx_test_case import (VfxTestCase, ZivaMirrorTestCase, ZivaMirrorNiceNameTestCase,
                           ZivaUpdateTestCase, ZivaUpdateNiceNameTestCase)
from tests.utils import load_scene, get_tmp_file_location, get_ziva_node_names_from_builder
from zBuilder.commands import (rename_ziva_nodes, clean_scene, remove_solver, remove_all_solvers,
                               rig_cut, rig_copy, rig_paste, rig_transfer)
from zBuilder.nodes.ziva.zSolver import SolverNode
from zBuilder.builders.serialize import read, write


class ZivaSolverGenericTestCase(VfxTestCase):

    @classmethod
    def setUpClass(cls):
        cls.temp_file_path = get_tmp_file_location()

    def setUp(self):
        super(ZivaSolverGenericTestCase, self).setUp()
        load_scene("generic.ma")
        self.builder = zva.Ziva()
        self.builder.retrieve_from_scene()

    def tearDown(self):
        if os.path.exists(self.temp_file_path):
            os.remove(self.temp_file_path)
        super(ZivaSolverGenericTestCase, self).tearDown()

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

        solver_attrs = ['substeps', 'gravityY', 'framesPerSecond']

        self.assertEqual(solver.name, name)
        self.assertEqual(solver.type, "zSolver")

        for i, attr in enumerate(solver_attrs):
            if attrs:
                value = attrs[i]
            else:
                value = cmds.getAttr("{}.{}".format(solver.name, attr))
            self.assertEqual(value, solver.attrs[attr]['value'])

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

        solver_transform_attrs = ['enable', 'startFrame']

        solver_transform_children_expected = {
            'zSolver1Shape', 'r_tissue_2', 'c_tissue_3', 'l_tissue_1', 'c_bone_1', 'c_bone_2',
            'c_cloth_1', 'l_bone_1'
        }

        self.assertEqual(solver_transform.name, name)
        self.assertEqual(solver_transform.type, "zSolverTransform")

        for i, attr in enumerate(solver_transform_attrs):
            if attrs:
                value = attrs[i]
            else:
                value = cmds.getAttr("{}.{}".format(solver_transform.name, attr))
            self.assertEqual(value, solver_transform.attrs[attr]['value'])

        solver_transform_children = {obj.name for obj in solver_transform.children}
        self.assertGreaterEqual(solver_transform_children, solver_transform_children_expected)

    def test_retrieve(self):
        self.check_retrieve_zsolver_looks_good(self.builder, "zSolver1Shape", [])
        self.check_retrieve_zsolver_transform_looks_good(self.builder, "zSolver1", [])

    def check_solver_and_transform_looks_good(self, builder, solver_name, solver_transform_name):
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
        write(self.temp_file_path, self.builder)
        self.assertTrue(os.path.exists(self.temp_file_path))

        builder = zva.Ziva()
        read(self.temp_file_path, builder)
        self.check_solver_and_transform_looks_good(builder, "zSolver1Shape", "zSolver1")

    def test_build(self):
        solver_attrs = ['substeps', 'gravityY', 'framesPerSecond']

        solver_transform_attrs = ['enable', 'startFrame']

        solver_values = []
        for attr in solver_attrs:
            value = cmds.getAttr("{}.{}".format("zSolver1Shape", attr))
            solver_values.append(value)

        solver_transform_values = []
        for attr in solver_transform_attrs:
            value = cmds.getAttr("{}.{}".format("zSolver1", attr))
            solver_transform_values.append(value)

        # remove all Ziva nodes from the scene and build them
        clean_scene()
        self.builder.build()

        self.check_retrieve_zsolver_looks_good(self.builder, "zSolver1Shape", solver_values)
        self.check_retrieve_zsolver_transform_looks_good(self.builder, "zSolver1",
                                                         solver_transform_values)

    def test_build_from_file(self):
        write(self.temp_file_path, self.builder)

        builder = zva.Ziva()
        read(self.temp_file_path, builder)
        clean_scene()
        builder.build()
        self.check_solver_and_transform_looks_good(builder, "zSolver1Shape", "zSolver1")

    def test_remove_solver(self):
        node_names = get_ziva_node_names_from_builder(self.builder)
        cmds.select("zSolver1")
        remove_solver(askForConfirmation=False)
        self.assertEqual(cmds.ls(node_names), [])

    def test_remove_all_solvers(self):
        node_names = get_ziva_node_names_from_builder(self.builder)
        remove_all_solvers(confirmation=False)
        self.assertEqual(cmds.ls(node_names), [])

    def test_string_replace(self):
        self.builder.string_replace("zSolver1", "zSolver2")
        solver_nodes = self.builder.get_scene_items(name_filter=["zSolver2"])
        self.assertEqual(len(solver_nodes), 1)

        clean_scene()
        self.builder.build()
        self.builder.retrieve_from_scene()
        solver_nodes = self.builder.get_scene_items(name_filter=["zSolver2"])
        self.assertEqual(len(solver_nodes), 1)

        solver_nodes = self.builder.get_scene_items(name_filter=["zSolver1"])
        self.assertEqual(len(solver_nodes), 0)

    def test_cut_paste(self):
        # Act
        cmds.select('zSolver1')
        rig_cut()

        # Verify
        self.assertEqual(cmds.ls("zSolver1"), [])

        # Act
        rig_paste()
        builder = zva.Ziva()
        builder.retrieve_from_scene()

        # Verify
        self.check_retrieve_zsolver_looks_good(builder, "zSolver1Shape", [])
        self.check_retrieve_zsolver_transform_looks_good(builder, "zSolver1", [])

    def test_copy_paste(self):
        # Act
        cmds.select('zSolver1')
        rig_copy()

        # Verify
        self.assertSceneHasNodes(["zSolver1"])

        # Act
        clean_scene()
        rig_paste()
        builder = zva.Ziva()
        builder.retrieve_from_scene()

        # Verify
        self.check_retrieve_zsolver_looks_good(builder, "zSolver1Shape", [])
        self.check_retrieve_zsolver_transform_looks_good(builder, "zSolver1", [])

    def test_transfer(self):
        # Setup
        meshes = cmds.ls(type="mesh")
        meshes_transforms = cmds.listRelatives(meshes, p=True)
        # exclude duplicates
        meshes_transforms = list(set(meshes_transforms))

        for item in meshes_transforms:
            cmds.rename(item, 'warped_{}'.format(item))

        clean_scene()

        load_scene("generic.ma", new_scene=False)

        # Act
        # now do the trasnfer
        rig_transfer('zSolver1', 'warped_', '')

        # Verify
        # when done we should have some ziva nodes with a 'warped_' prefix
        nodes_in_scene = ['warped_zSolver1', 'warped_zSolver1Shape']
        self.assertSceneHasNodes(nodes_in_scene)


class ZivaSolverTestCase(VfxTestCase):

    def setUp(self):
        super(ZivaSolverTestCase, self).setUp()
        self.results = mel.eval('ziva -s')

    def test_rebuild_solver_shape_name(self):
        # tests the shape name when re-building a solver via zBuilder.

        cmds.rename(self.results[1], 'zSolver_fat')

        # use builder to retrieve from scene-----------------------------------
        z = zva.Ziva()
        z.retrieve_from_scene()

        cmds.delete('zSolver_fat')

        z.build()

        # get solver from zBuilder
        solver_node = z.get_scene_items(type_filter='zSolver')[0]

        self.assertSceneHasNodes([solver_node.name])


class ZivaSolverMirrorTestCase(ZivaMirrorTestCase):
    """This Class tests a specific type of "mirroring" so there are some assumptions made

    - geometry has an identifiable qualifier, in this case it is l_ and r_
    - Both sides geometry are in the scene
    - One side has Ziva VFX nodes and other side does not, in this case l_ has Ziva nodes
    - Ziva nodes are named default like so: zSolver1, zSolver2, zSolver3

    """

    def setUp(self):
        super(ZivaSolverMirrorTestCase, self).setUp()

        load_scene('mirror_example.ma')
        self.builder = zva.Ziva()
        self.builder.retrieve_from_scene()
        # gather info
        self.scene_items_retrieved = self.builder.get_scene_items(type_filter=SolverNode.type)
        self.l_item_geo = []

    def test_builder_change_with_string_replace(self):
        super(ZivaSolverMirrorTestCase, self).builder_change_with_string_replace()

    def test_builder_build_with_string_replace(self):
        super(ZivaSolverMirrorTestCase, self).builder_build_with_string_replace()


class ZivaSolverUpdateNiceNameTestCase(ZivaUpdateNiceNameTestCase):
    """This Class tests a specific type of "mirroring" so there are some assumptions made

    - geometry has an identifiable qualifier, in this case it is l_ and r_
    - Both sides geometry are in the scene
    - Both sides have Ziva VFX nodes
    - The Ziva Nodes have a side identifier same as geo

    """

    def setUp(self):
        super(ZivaSolverUpdateNiceNameTestCase, self).setUp()
        load_scene('mirror_example.ma')

        # NICE NAMES
        rename_ziva_nodes()

        # make FULL setup based on left
        builder = zva.Ziva()
        builder.retrieve_from_scene()
        builder.string_replace('^l_', 'r_')
        builder.build()

        # gather info
        cmds.select('l_armA_muscle_geo', 'l_armA_subtissue_geo')
        self.builder = zva.Ziva()
        self.builder.retrieve_from_scene_selection()

        self.scene_items_retrieved = self.builder.get_scene_items(type_filter=SolverNode.type)
        self.l_item_geo = []

    def test_builder_change_with_string_replace(self):
        super(ZivaSolverUpdateNiceNameTestCase, self).builder_change_with_string_replace()

    def test_builder_build_with_string_replace(self):
        super(ZivaSolverUpdateNiceNameTestCase, self).builder_build_with_string_replace()


class ZivaSolverMirrorNiceNameTestCase(ZivaMirrorNiceNameTestCase):
    """This Class tests a specific type of "mirroring" so there are some assumptions made

    - geometry has an identifiable qualifier, in this case it is l_ and r_
    - Both sides geometry are in the scene
    - One side has Ziva VFX nodes and other side does not, in this case l_ has Ziva nodes

    """

    def setUp(self):
        super(ZivaSolverMirrorNiceNameTestCase, self).setUp()
        # gather info

        # Bring in scene
        load_scene('mirror_example.ma')

        # force NICE NAMES
        rename_ziva_nodes()

        self.builder = zva.Ziva()
        self.builder.retrieve_from_scene()

        self.scene_items_retrieved = self.builder.get_scene_items(type_filter=SolverNode.type)
        self.l_item_geo = []

    def test_builder_change_with_string_replace(self):
        super(ZivaSolverMirrorNiceNameTestCase, self).builder_change_with_string_replace()

    def test_builder_build_with_string_replace(self):
        super(ZivaSolverMirrorNiceNameTestCase, self).builder_build_with_string_replace()


class ZivaSolverUpdateTestCase(ZivaUpdateTestCase):
    """This Class tests a specific type of "mirroring" so there are some assumptions made

    - geometry has an identifiable qualifier, in this case it is l_ and r_
    - Both sides geometry are in the scene
    - Both sides have Ziva nodes

    """

    def setUp(self):
        super(ZivaSolverUpdateTestCase, self).setUp()
        load_scene('mirror_example.ma')
        self.builder = zva.Ziva()
        self.builder.retrieve_from_scene()

        # VERIFY
        self.compare_builder_nodes_with_scene_nodes(self.builder)
        self.compare_builder_attrs_with_scene_attrs(self.builder)

        # gather info
        self.scene_items_retrieved = self.builder.get_scene_items(type_filter=SolverNode.type)
        self.l_item_geo = []

        new_builder = zva.Ziva()
        new_builder.retrieve_from_scene()
        new_builder.string_replace("^l_", "r_")
        new_builder.build()

    def test_builder_change_with_string_replace(self):
        super(ZivaSolverUpdateTestCase, self).builder_change_with_string_replace()

    def test_builder_build_with_string_replace(self):
        super(ZivaSolverUpdateTestCase, self).builder_build_with_string_replace()


class ZivaSolverDuplicateTestCase(VfxTestCase):

    @classmethod
    def setUpClass(cls):
        cls.temp_file_path = get_tmp_file_location()

    def setUp(self):
        super(ZivaSolverDuplicateTestCase, self).setUp()
        load_scene('generic_duplicate.ma')
        cmds.select('zSolver1')
        self.builder = zva.Ziva()
        self.builder.retrieve_from_scene()
        cmds.ziva('zSolver1', defaultSolver=True)

    def tearDown(self):
        if os.path.exists(self.temp_file_path):
            os.remove(self.temp_file_path)
        super(ZivaSolverDuplicateTestCase, self).tearDown()

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

        solver_attrs = ['substeps', 'gravityY', 'framesPerSecond']

        self.assertEqual(solver.name, name)
        self.assertEqual(solver.type, "zSolver")

        for i, attr in enumerate(solver_attrs):
            if attrs:
                value = attrs[i]
            else:
                value = cmds.getAttr("{}.{}".format(solver.long_name, attr))
            self.assertEqual(value, solver.attrs[attr]['value'])

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

        solver_transform_attrs = ['enable', 'startFrame']

        solver_transform_children_expected = {
            'zSolver1Shape', 'r_tissue_2', 'c_tissue_3', 'l_tissue_1', 'c_bone_1', 'c_bone_2',
            'c_cloth_1', 'l_bone_1'
        }

        self.assertEqual(solver_transform.name, name)
        self.assertEqual(solver_transform.type, "zSolverTransform")

        for i, attr in enumerate(solver_transform_attrs):
            if attrs:
                value = attrs[i]
            else:
                value = cmds.getAttr("{}.{}".format(solver_transform.long_name, attr))
            self.assertEqual(value, solver_transform.attrs[attr]['value'])

        solver_transform_children = {obj.name for obj in solver_transform.children}
        self.assertGreaterEqual(solver_transform_children, solver_transform_children_expected)

    def test_retrieve(self):
        self.check_retrieve_zsolver_looks_good(self.builder, "zSolver1Shape", [])
        self.check_retrieve_zsolver_transform_looks_good(self.builder, "zSolver1", [])

    def check_solver_and_transform_looks_good(self, builder, solver_name, solver_transform_name):
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
        write(self.temp_file_path, self.builder)
        self.assertTrue(os.path.exists(self.temp_file_path))

        builder = zva.Ziva()
        read(self.temp_file_path, builder)
        self.check_solver_and_transform_looks_good(builder, "zSolver1Shape", "zSolver1")

    def test_build(self):
        solver_attrs = ['substeps', 'gravityY', 'framesPerSecond']

        solver_transform_attrs = ['enable', 'startFrame']

        solver_values = []
        for attr in solver_attrs:
            value = cmds.getAttr("{}.{}".format("zSolver1|zSolver1Shape", attr))
            solver_values.append(value)

        solver_transform_values = []
        for attr in solver_transform_attrs:
            value = cmds.getAttr("{}.{}".format("zSolver1", attr))
            solver_transform_values.append(value)

        # remove all Ziva nodes from the scene and build them
        clean_scene()
        self.builder.build()

        self.check_retrieve_zsolver_looks_good(self.builder, "zSolver1Shape", solver_values)
        self.check_retrieve_zsolver_transform_looks_good(self.builder, "zSolver1",
                                                         solver_transform_values)

    def test_build_from_file(self):
        write(self.temp_file_path, self.builder)

        builder = zva.Ziva()
        read(self.temp_file_path, builder)
        clean_scene()
        builder.build()
        self.check_solver_and_transform_looks_good(builder, "zSolver1Shape", "zSolver1")

    def test_remove_solver(self):
        node_names = get_ziva_node_names_from_builder(self.builder, long=True)
        cmds.select("zSolver1")
        remove_solver(askForConfirmation=False)
        self.assertEqual(cmds.ls(node_names), [])

    def test_remove_all_solvers(self):
        node_names = get_ziva_node_names_from_builder(self.builder)
        remove_all_solvers(confirmation=False)
        self.assertEqual(cmds.ls(node_names), [])

    def test_string_replace(self):
        self.builder.string_replace("zSolver1", "zSolver2")
        solver_nodes = self.builder.get_scene_items(name_filter=["zSolver2"])
        self.assertEqual(len(solver_nodes), 1)

        clean_scene()
        self.builder.build()
        self.builder.retrieve_from_scene()
        solver_nodes = self.builder.get_scene_items(name_filter=["zSolver2"])
        self.assertEqual(len(solver_nodes), 1)

        solver_nodes = self.builder.get_scene_items(name_filter=["zSolver1"])
        self.assertEqual(len(solver_nodes), 0)

    def test_cut_paste(self):
        # Act
        cmds.select("zSolver1")
        rig_cut()

        # Verify
        self.assertEqual(cmds.ls("zSolver1"), [])

        # Act
        rig_paste()
        builder = zva.Ziva()
        cmds.select("zSolver1")
        builder.retrieve_from_scene()

        # Verify
        self.check_retrieve_zsolver_looks_good(builder, "zSolver1Shape", [])
        self.check_retrieve_zsolver_transform_looks_good(builder, "zSolver1", [])

    def test_copy_paste(self):
        # Act
        cmds.select("zSolver1")
        rig_copy()

        # Verify
        self.assertSceneHasNodes(["zSolver1"])

        # Act
        clean_scene()
        rig_paste()
        builder = zva.Ziva()
        builder.retrieve_from_scene()

        # Verify
        self.check_retrieve_zsolver_looks_good(builder, "zSolver1Shape", [])
        self.check_retrieve_zsolver_transform_looks_good(builder, "zSolver1", [])

    def test_transfer(self):
        # Setup
        meshes = cmds.ls(type='mesh')
        meshes_transforms = cmds.listRelatives(meshes, p=True)
        # exclude duplicates
        meshes_transforms = list(set(meshes_transforms))

        for item in meshes_transforms:
            cmds.rename('group1|' + item, 'warped_{}'.format(item))

        clean_scene()

        load_scene('generic_duplicate.ma', new_scene=False)

        # Act
        # now do the trasnfer
        rig_transfer('zSolver1', 'warped_', '')

        # Verify
        # when done we should have some ziva nodes with a 'warped_' prefix
        nodes_in_scene = ['warped_zSolver1', 'warped_zSolver1Shape']
        self.assertSceneHasNodes(nodes_in_scene)
