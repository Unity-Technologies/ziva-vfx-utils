import os
import zBuilder.builders.ziva as zva

from maya import cmds
from cmt.test import TestCase
from tests.utils import get_tmp_file_location
from zBuilder.utils.commonUtils import is_sequence
from zBuilder.utils.paintable_maps import split_map_name, get_paintable_map
from zBuilder.commands import clean_scene, rig_cut, rig_paste, rig_copy
from zBuilder.builders.serialize import read, write


def isApprox(a, b, eps=1e-6):
    if hasattr(type(a), '__iter__'):
        if len(a) != len(b):
            return False
        return all([isApprox(ai, bi, eps) for ai, bi in zip(a, b)])
    else:
        return abs(a - b) <= eps


def get_mesh_vertex_positions(mesh, index_range='*'):
    """ Given the name of a mesh, return a flat list of its world-space vertex positions."""
    # See comments here: http://www.fevrierdorian.com/blog/post/2011/09/27/Quickly-retrieve-vertex-positions-of-a-Maya-mesh-%28English-Translation%29
    return cmds.xform("{}.vtx[{}]".format(mesh, index_range), q=True, ws=True, t=True)


def get_all_mesh_vertex_positions():
    """ Concatenation of all mesh vertex positions in the scene """
    pos = []
    meshes = cmds.ls(dag=True, type='mesh', noIntermediate=True)
    meshes.sort()  # So we get the same order between calls
    for mesh in meshes:
        pos.extend(get_mesh_vertex_positions(mesh))
    return pos


def attr_values_from_zbuilder_nodes(nodes):
    """ From a list of zBuilder nodes get all of the attributes and their values as a dict.
    e.g. Input: builder.get_scene_items(type_filter="zTissue")
         Output: {'zTissue1.collisions':True, 'my_zTetNode.tetSize:4.5, ... }
    """
    result = {}
    for node in nodes:
        for attr, attr_dict in node.attrs.items():
            plug_name = "{}.{}".format(node.name, attr)
            plug_value = attr_dict["value"]
            result[plug_name] = plug_value
    return result


def attr_values_from_scene(plug_names):
    """ From a collection of attribute names, get a dict of attr/value pairs.
    e.g Input: ['zTissue1.collisions', 'my_zTetNode.tetSize', ...]
        Output: {'zTissue1.collisions':True, 'my_zTetNode.tetSize:4.5, ... }
    """
    return {plug_name: cmds.getAttr(plug_name) for plug_name in plug_names}


class VfxTestCase(TestCase):
    temp_file_path = get_tmp_file_location()
    """Base class for unit test cases run for ZivaVFX plugin."""

    def assertSceneHasNodes(self, expected_nodes):
        """Fail iff a node in expected_nodes is not in the Maya scene."""
        expected_nodes = dict.fromkeys(expected_nodes)
        all_nodes = dict.fromkeys(cmds.ls())
        # using DictSubset gives nice error messages
        self.assertDictContainsSubset(expected_nodes, all_nodes)

    def assertApproxEqual(self, a, b, eps=1e-6):
        """Fail iff |a-b|>eps"""
        # all this negation is to make sure that NaN fails.
        if not (a >= b - eps) or not (a <= b + eps):
            raise AssertionError("{} and {} are not approximately equal, with tolerance {}".format(
                a, b, eps))

    def assertAllApproxEqual(self, a, b, eps=1e-6):
        """Fail iff |a[i]-b[i]|>eps for all i"""
        if len(a) != len(b):
            raise AssertionError("{} and {} are not approximately equal, with tolerance {}".format(
                a, b, eps))
        for ai, bi in zip(a, b):
            self.assertApproxEqual(ai, bi, eps)

    def assertCountsEqual(self, a, b):
        """
        TODO: Remove this function after Python2 retires.
        This is an adapter to meet the coexistense of Python2 and Python3.
        """
        import sys
        if sys.version_info[0] < 3:
            self.assertItemsEqual(a, b)
        else:
            self.assertCountEqual(a, b)

    def check_tissue_node_subtissue_builder_and_scene(self, scene_items):

        # Tissue specific sub-tissue check
        parents = {
            x.name: x.parent_tissue.name
            for x in scene_items if x.type == 'zTissue' and x.parent_tissue
        }

        if parents:
            for key, value in parents.items():
                self.assertEqual(value, cmds.listConnections(key + '.iParentTissue')[0])

    def check_node_association_amount_equal(self, scene_items, startswith='r_', amount=0):
        geo = []
        for scene_item in scene_items:
            if scene_item.association:
                if scene_item.association[0].startswith(startswith):
                    geo.append(scene_item)
        self.assertEqual(len(geo), amount)

    def check_node_association_amount_not_equal(self, scene_items, startswith='r_', amount=0):
        geo = [x for x in scene_items if x.association[0].startswith(startswith)]
        self.assertNotEqual(len(geo), amount)

    def compare_builder_nodes_with_scene_nodes(self, builder):
        # goes every node in a builder and checks by name if they are in the scene.
        # useful for checking after a build if everything built.
        items = builder.get_scene_items(type_filter=['map', 'mesh'], invert_match=True)

        for item in items:
            self.assertTrue(cmds.objExists(item.name))

    def compare_builder_attrs_with_scene_attrs(self, builder):
        # goes through every attribute in builder and checks if the same nodes in scene have same
        # value.  Useful for checking if a build worked on attribute changes.
        items = builder.get_scene_items(type_filter=['map', 'mesh'], invert_match=True)

        for item in items:
            for attr, v in item.attrs.items():
                self.assertEquals(v['value'], cmds.getAttr('{}.{}'.format(item.name, attr)))

    def compare_builder_maps_with_scene_maps(self, builder):
        """
        Checking maps in builder against ones in scene
        """
        items = builder.get_scene_items(type_filter=['map'])
        for item in items:
            node_name, attr_name = split_map_name(item.name)
            scene_map_value = get_paintable_map(node_name, attr_name, item._mesh)
            self.assertEqual(item.values, scene_map_value)

    def compare_builder_restshapes_with_scene_restshapes(self, builder):
        # checking the actual restshapes got hooked up in maya
        for item in self.builder.get_scene_items(type_filter='zRestShape'):
            connections = cmds.listConnections('{}.target'.format(item.name))
            connections_long_name = cmds.ls(connections, long=True)
            self.assertEqual(item.targets, connections_long_name)

    def check_retrieve_looks_good(self, builder, expected_plugs, node_names, node_type):
        """Args:
            builder (builders.ziva.Ziva()): builder object
            expected_plugs (dict): A dict of expected attribute/value pairs.
                                   {'zTissue1.collisions':True, ...}.
                                   If None/empty/False, then attributes are taken from zBuilder
                                   and values are taken from the scene.
                                   Test fails if zBuilder is missing any of the keys
                                   or has any keys with different values.
            node_names (list): A list of expected node names like zTissue1, zBone1, ...
            node_type (string/list): Node type to check: zTissue, zBone, ...
        """
        if not is_sequence(node_type):
            node_type = [node_type]

        nodes = builder.get_scene_items(type_filter=node_type)

        self.assertCountsEqual(node_names, [x.name for x in nodes])

        for node in nodes:
            self.assertIn(node.type, node_type)

        zbuilder_plugs = attr_values_from_zbuilder_nodes(nodes)
        expected_plugs = expected_plugs or attr_values_from_scene(zbuilder_plugs.keys())
        self.assertTrue(set(zbuilder_plugs).issuperset(set(expected_plugs)))

    def check_build_restores_attr_values(self, builder, node_names, node_attrs):
        plug_names = {'{}.{}'.format(geo, attr) for geo in node_names for attr in node_attrs}
        attrs_before = attr_values_from_scene(plug_names)

        # remove all Ziva nodes from the scene and build them
        clean_scene()
        builder.build()

        attrs_after = attr_values_from_scene(plug_names)
        self.assertEqual(attrs_before, attrs_after)

    def find_body(self, node):
        # Find the body for the given zbuilder node
        # body includes meshes for the nodes: zTissue, zBone, zCloth
        if hasattr(node, "parent"):
            if hasattr(node.parent, "depends_on"):
                return node.parent
            else:
                return self.find_body(node.parent)

    def check_ziva_remove_command(self, builder, node_type):
        ## SETUP
        nodes = builder.get_scene_items(type_filter=node_type)
        # clear selection
        cmds.select(cl=True)
        for node in nodes:
            body = self.find_body(node)
            cmds.select(body.long_name, add=True)

        ## ACT
        cmds.ziva(rm=True)

        ## VERIFY
        cmds.select(cl=True)
        builder = zva.Ziva()
        builder.retrieve_from_scene()
        nodes = builder.get_scene_items(type_filter=node_type)
        self.assertEqual(nodes, [])

    def check_map_interpolation(self, builder, node_name, expected_weights, map_index, eps=1e-6):
        """Args:
            builder (builders.ziva.Ziva()): builder object
            node_name (string): name of the Ziva node with a map
            expected_weights (list): list if expected weights for the map
            map_index (int): map index, 0 or 1, to choose between source/target, source/endPoints
                             weights
            eps (float): Epsilon for approximation.
        """
        ## ACT
        builder.build(interp_maps=True)

        ## VERIFY
        cmds.select(cl=True)
        builder = zva.Ziva()
        builder.retrieve_from_scene()
        node = builder.get_scene_items(name_filter=node_name)[0]
        self.assertAllApproxEqual(expected_weights, node.parameters["map"][map_index].values, eps)

    def get_builder_after_writing_and_reading_from_disk(self, builder):
        write(self.temp_file_path, builder)
        self.assertTrue(os.path.exists(self.temp_file_path))

        builder = zva.Ziva()
        read(self.temp_file_path, builder)
        return builder

    def get_builder_after_clean_and_build(self, builder):
        ## SETUP
        clean_scene()

        ## ACT
        builder.build()

        builder = zva.Ziva()
        builder.retrieve_from_scene()
        return builder

    def get_builder_after_write_and_read(self, builder):
        ## SETUP
        write(self.temp_file_path, builder)
        self.assertTrue(os.path.exists(self.temp_file_path))
        clean_scene()

        ## ACT
        builder = zva.Ziva()
        read(self.temp_file_path, builder)
        builder.build()

        builder = zva.Ziva()
        builder.retrieve_from_scene()
        return builder

    def get_builder_after_cut_paste(self, mesh_name, node_name):
        """
        Get builder after node cut and pasted from and to the mesh
        Args:
            mesh_name (string): mesh name to cut from
            node_name (string): Ziva node to check
        """
        ## ACT
        cmds.select(mesh_name)
        rig_cut()

        ## VERIFY
        self.assertEqual(cmds.ls(node_name), [])

        ## ACT
        cmds.select(mesh_name)
        rig_paste()

        builder = zva.Ziva()
        builder.retrieve_from_scene()
        return builder

    def get_builder_after_copy_paste(self, mesh_name, node_name):
        """
        Get builder after node copy and pasted from and to the mesh
        Args:
            mesh_name (string): mesh name to cut from
            node_name (string): Ziva node to check
        """
        ## ACT
        # check if node exists
        self.assertEqual(len(cmds.ls(node_name)), 1)
        cmds.select(mesh_name)
        rig_copy()

        ## VERIFY
        # check that node was not removed
        self.assertEqual(len(cmds.ls(node_name)), 1)

        ## SETUP
        cmds.ziva(rm=True)

        ## ACT
        cmds.select(mesh_name)
        rig_paste()

        builder = zva.Ziva()
        builder.retrieve_from_scene()
        return builder


class ZivaMirrorTestCase(VfxTestCase):
    """This Class tests a specific type of "mirroring" so there are some assumptions made

    - geometry has an identifiable qualifier, in this case it is l_ and r_
    - Both sides geometry are in the scene
    - One side has Ziva VFX nodes and other side does not, in this case l_ has Ziva nodes
    - Ziva nodes are named default like so: zTissue1, zTissue2, zTissue3

    """

    def builder_change_with_string_replace(self):
        # VERIFY
        self.compare_builder_nodes_with_scene_nodes(self.builder)
        self.compare_builder_attrs_with_scene_attrs(self.builder)

        self.check_node_association_amount_equal(self.scene_items_retrieved, 'r_', 0)
        self.check_node_association_amount_equal(self.scene_items_retrieved, 'l_',
                                                 len(self.l_item_geo))

        # ACT
        self.builder.string_replace("^l_", "r_")

        # VERIFY
        self.check_node_association_amount_equal(self.scene_items_retrieved, 'l_', 0)
        self.check_node_association_amount_equal(self.scene_items_retrieved, 'r_',
                                                 len(self.l_item_geo))

    def builder_build_with_string_replace(self):
        self.compare_builder_nodes_with_scene_nodes(self.builder)
        self.compare_builder_attrs_with_scene_attrs(self.builder)

        # ACT
        self.builder.string_replace("^l_", "r_")
        self.builder.build()

        # VERIFY
        self.compare_builder_nodes_with_scene_nodes(self.builder)
        self.compare_builder_attrs_with_scene_attrs(self.builder)
        self.compare_builder_maps_with_scene_maps(self.builder)
        self.compare_builder_restshapes_with_scene_restshapes(self.builder)
        self.check_tissue_node_subtissue_builder_and_scene(self.scene_items_retrieved)


class ZivaUpdateNiceNameTestCase(VfxTestCase):
    """This Class tests a specific type of "mirroring" so there are some assumptions made

    - geometry has an identifiable qualifier, in this case it is l_ and r_
    - Both sides geometry are in the scene
    - Both sides have Ziva VFX nodes
    - The Ziva Nodes have a side identifier same as geo

    """

    def builder_change_with_string_replace(self):
        # VERIFY
        self.compare_builder_nodes_with_scene_nodes(self.builder)
        self.compare_builder_attrs_with_scene_attrs(self.builder)

        self.check_node_association_amount_equal(self.scene_items_retrieved, 'r_', 0)
        self.check_node_association_amount_equal(self.scene_items_retrieved, 'l_',
                                                 len(self.l_item_geo))

        # ACT
        self.builder.string_replace("^l_", "r_")

        # VERIFY
        self.check_node_association_amount_equal(self.scene_items_retrieved, 'l_', 0)
        self.check_node_association_amount_equal(self.scene_items_retrieved, 'r_',
                                                 len(self.l_item_geo))

    def builder_build_with_string_replace(self):
        self.compare_builder_nodes_with_scene_nodes(self.builder)
        self.compare_builder_attrs_with_scene_attrs(self.builder)

        # ACT
        self.builder.string_replace("^l_", "r_")
        self.builder.build()

        # VERIFY
        self.compare_builder_nodes_with_scene_nodes(self.builder)
        self.compare_builder_attrs_with_scene_attrs(self.builder)
        self.compare_builder_maps_with_scene_maps(self.builder)
        self.compare_builder_restshapes_with_scene_restshapes(self.builder)
        self.check_tissue_node_subtissue_builder_and_scene(self.scene_items_retrieved)


class ZivaUpdateTestCase(VfxTestCase):
    """This Class tests a specific type of "mirroring" so there are some assumptions made

    - geometry has an identifiable qualifier, in this case it is l_ and r_
    - Both sides geometry are in the scene
    - Both sides have Ziva nodes

    """

    def builder_change_with_string_replace(self):

        self.check_node_association_amount_equal(self.scene_items_retrieved, 'r_', 0)
        self.check_node_association_amount_equal(self.scene_items_retrieved, 'l_',
                                                 len(self.l_item_geo))

        # ACT
        self.builder.string_replace("^l_", "r_")

        # VERIFY
        self.check_node_association_amount_equal(self.scene_items_retrieved, 'l_', 0)
        self.check_node_association_amount_equal(self.scene_items_retrieved, 'r_',
                                                 len(self.l_item_geo))

    def builder_build_with_string_replace(self):

        # ACT
        self.builder.string_replace("^l_", "r_")
        self.builder.build()

        # VERIFY
        self.compare_builder_nodes_with_scene_nodes(self.builder)
        self.compare_builder_attrs_with_scene_attrs(self.builder)
        self.compare_builder_maps_with_scene_maps(self.builder)
        self.compare_builder_restshapes_with_scene_restshapes(self.builder)
        self.check_tissue_node_subtissue_builder_and_scene(self.scene_items_retrieved)


class ZivaMirrorNiceNameTestCase(VfxTestCase):
    """This Class tests a specific type of "mirroring" so there are some assumptions made

    - geometry has an identifiable qualifier, in this case it is l_ and r_
    - Both sides geometry are in the scene
    - One side has Ziva VFX nodes and other side does not, in this case l_ has Ziva nodes

    """

    def builder_change_with_string_replace(self):
        # VERIFY
        self.compare_builder_nodes_with_scene_nodes(self.builder)
        self.compare_builder_attrs_with_scene_attrs(self.builder)

        self.check_node_association_amount_equal(self.scene_items_retrieved, 'r_', 0)
        self.check_node_association_amount_equal(self.scene_items_retrieved, 'l_',
                                                 len(self.l_item_geo))

        # ACT
        self.builder.string_replace("^l_", "r_")

        # VERIFY
        self.check_node_association_amount_equal(self.scene_items_retrieved, 'l_', 0)
        self.check_node_association_amount_equal(self.scene_items_retrieved, 'r_',
                                                 len(self.l_item_geo))

    def builder_build_with_string_replace(self):
        self.compare_builder_nodes_with_scene_nodes(self.builder)
        self.compare_builder_attrs_with_scene_attrs(self.builder)

        # ACT
        self.builder.string_replace("^l_", "r_")
        self.builder.build()

        # VERIFY
        self.compare_builder_nodes_with_scene_nodes(self.builder)
        self.compare_builder_attrs_with_scene_attrs(self.builder)
        self.compare_builder_maps_with_scene_maps(self.builder)
        self.compare_builder_restshapes_with_scene_restshapes(self.builder)
        self.check_tissue_node_subtissue_builder_and_scene(self.scene_items_retrieved)
