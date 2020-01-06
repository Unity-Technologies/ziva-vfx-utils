import os
import maya.cmds as cmds
from cmt.test import TestCase
import zBuilder.zMaya as mz
import maya.cmds as mc
import zBuilder.builders.ziva as zva
import tests.utils as test_utils
import zBuilder.utils as utils


def isApprox(a, b, eps=1e-6):
    if hasattr(type(a), '__iter__'):
        if len(a) != len(b):
            return False
        return all([isApprox(ai, bi, eps) for ai, bi in zip(a, b)])
    else:
        return abs(a - b) <= eps


def get_mesh_vertex_positions(mesh):
    """ Given the name of a mesh, return a flat list of its world-space vertex positions."""
    # See comments here: http://www.fevrierdorian.com/blog/post/2011/09/27/Quickly-retrieve-vertex-positions-of-a-Maya-mesh-%28English-Translation%29
    return cmds.xform(mesh + '.vtx[*]', q=True, ws=True, t=True)


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
    temp_file_path = test_utils.get_tmp_file_location()

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
            node_type (string): Node type to check: zTissue, zBone, ...
        """
        nodes = builder.get_scene_items(type_filter=node_type)

        self.assertItemsEqual(node_names, [x.name for x in nodes])

        for node in nodes:
            self.assertEqual(node.type, node_type)

        zbuilder_plugs = attr_values_from_zbuilder_nodes(nodes)
        expected_plugs = expected_plugs or attr_values_from_scene(zbuilder_plugs.keys())
        self.assertGreaterEqual(zbuilder_plugs, expected_plugs)

    def check_build_restores_attr_values(self, builder, node_names, node_attrs):
        plug_names = {
            '{}.{}'.format(geo, attr)
            for geo in node_names for attr in node_attrs
        }
        attrs_before = attr_values_from_scene(plug_names)

        # remove all Ziva nodes from the scene and build them
        mz.clean_scene()
        builder.build()

        attrs_after = attr_values_from_scene(plug_names)
        self.assertEqual(attrs_before, attrs_after)

    def check_ziva_remove_command(self, builder, node_type):
        ## SETUP
        tissue_nodes = builder.get_scene_items(type_filter=node_type)
        # clear selection
        mc.select(cl=True)
        for tissue in tissue_nodes:
            mc.select(tissue.long_association, add=True)

        ## ACT
        mc.ziva(rm=True)

        ## VERIFY
        mc.select(cl=True)
        builder = zva.Ziva()
        builder.retrieve_from_scene()
        tissue_nodes = builder.get_scene_items(type_filter=node_type)
        self.assertEqual(tissue_nodes, [])

    def get_builder_after_writing_and_reading_from_disk(self, builder):
        builder.write(self.temp_file_path)
        self.assertTrue(os.path.exists(self.temp_file_path))

        builder = zva.Ziva()
        builder.retrieve_from_file(self.temp_file_path)
        return builder

    def get_builder_after_clean_and_build(self, builder):
        ## SETUP
        mz.clean_scene()

        ## ACT
        builder.build()

        builder = zva.Ziva()
        builder.retrieve_from_scene()
        return builder

    def get_builder_after_write_and_retrieve_from_file(self, builder):
        ## SETUP
        builder.write(self.temp_file_path)
        mz.clean_scene()

        ## ACT
        builder = zva.Ziva()
        builder.retrieve_from_file(self.temp_file_path)
        builder.build()

        builder = zva.Ziva()
        builder.retrieve_from_scene()
        return builder
        
    def get_builder_after_cut_paste(self, mesh_name, node_name):
        """
        Checks if node can be cut and pasted from and to the mesh
        Args:
            mesh_name (string): mesh name to cut from
            node_name (string): Ziva node to check
        """
        ## ACT
        mc.select(mesh_name)
        utils.rig_cut()

        ## VERIFY
        self.assertEqual(mc.ls(node_name), [])

        ## ACT
        mc.select(mesh_name)
        utils.rig_paste()

        builder = zva.Ziva()
        builder.retrieve_from_scene()
        return builder

    def get_builder_after_copy_paste(self, mesh_name, node_name):
        """
        Checks if node can be copy and pasted from and to the mesh
        Args:
            mesh_name (string): mesh name to cut from
            node_name (string): Ziva node to check
        """
        ## ACT
        # check if node exists
        self.assertEqual(len(mc.ls(node_name)), 1)
        mc.select(mesh_name)
        utils.rig_copy()

        ## VERIFY
        # check that node was not removed
        self.assertEqual(len(mc.ls(node_name)), 1)

        ## SETUP
        mc.ziva(rm=True)

        ## ACT
        mc.select(mesh_name)
        utils.rig_paste()

        builder = zva.Ziva()
        builder.retrieve_from_scene()
        return builder
