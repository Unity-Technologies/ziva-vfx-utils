import os
import yaml
import maya.cmds as cmds

from cmt.test import TestCase

class VfxTestCase(TestCase):
    """Base class for unit test cases run for ZivaVFX plugin."""
    
    pluginPath = None

    def setUp(self):
        print('loading plugin ...')
        self.pluginPath = get_plugin_path()
        cmds.loadPlugin(self.pluginPath)        
        print('plugin loaded: '+self.pluginPath)

    def tearDown(self):
        print('unloading plugin ...')
        cmds.file(f=True, new=True)        # this trick releases a plugin so that it could be safely unloaded
        cmds.unloadPlugin(os.path.basename(self.pluginPath))   # plugin gets unloaded by file name only
        print('plugin unloaded')

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

def get_plugin_path():
    with open(os.path.dirname(__file__) + '/../settings.yaml', 'r') as stream:
        try:
            data = yaml.load(stream)
        except yaml.YAMLError as exc:
            exc

    return data['settings']['plugin_path']

