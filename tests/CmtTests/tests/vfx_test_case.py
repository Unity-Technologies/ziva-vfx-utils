import os
import sys
import maya.cmds as cmds
from cmt.test import TestCase
import logging

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
    return cmds.xform(mesh+'.vtx[*]', q=True, ws=True, t=True)

class VfxTestCase(TestCase):
    """Base class for unit test cases run for ZivaVFX plugin."""

    pluginPath = None

    def setUp(self):
        if not cmds.pluginInfo('ziva', query=True, loaded=True):
            cmds.loadPlugin("ziva")

    def tearDown(self):
        # We do not unload the plugin here on purpose.
        # because Maya goes wrong when load/unload plugin repeatedly.
        # We only clear the scene here.
        cmds.file(f=True, new=True)


    def assertSceneHasNodes(self, expected_nodes):
        """Fail iff a node in expected_nodes is not in the Maya scene."""
        expected_nodes = dict.fromkeys(expected_nodes)
        all_nodes = dict.fromkeys(cmds.ls())
        # using DictSubset gives nice error messages
        self.assertDictContainsSubset(expected_nodes, all_nodes)

    def assertApproxEqual(self, a, b, eps=1e-6):
        """Fail iff |a-b|>eps"""
        # all this negation is to make sure that NaN fails.
        if not (a>=b-eps) or not (a<=b+eps):
            raise AssertionError("{} and {} are not approximately equal, with tolerance {}".format(a,b,eps))

    def assertAllApproxEqual(self, a, b, eps=1e-6):
        """Fail iff |a[i]-b[i]|>eps for all i"""
        if len(a) != len(b):
            raise AssertionError("{} and {} are not approximately equal, with tolerance {}".format(
                a, b, eps))
        for ai, bi in zip(a, b):
            self.assertApproxEqual(ai, bi, eps)
