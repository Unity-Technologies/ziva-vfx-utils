import os
import maya.cmds as cmds

from cmt.test import TestCase

class ZMayaTestCase(TestCase):
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
    # zMayaRootDir = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir, os.pardir))

    # mayaYear = get_maya_year()
    # paths = [
    #     os.path.join(zMayaRootDir, 'x64', 'Debug' + mayaYear, 'ziva_debug.mll'),
    #     os.path.join(zMayaRootDir, 'x64', 'Develop' + mayaYear, 'ziva_devel.mll'),
    #     os.path.join(zMayaRootDir, 'x64', 'Release' + mayaYear, 'ziva.mll'),
    #     os.path.join(zMayaRootDir, 'ziva-maya{year}.so'.format(year=mayaYear)),
    # ]

    # pathsExist = [x for x in paths if os.path.isfile(x)]
    # if not pathsExist:
    #     raise RuntimeError('None of the ZivaVFX plugins were found. The following paths were examined: ' + str(paths))

    #return pathsExist[0] # return the first one that exists
    return r'C:\Users\lonniek.ZIVADYNAMICS\Documents\plugins\2018\20181128-5ba1175-win2018-devel\ziva.mll'

def get_maya_year():
    """This function makes sure that version can be safely used in a file path, 
       as cmds.about(v=True) does not guarantee that for all maya versions"""

    ver = cmds.about(v=True)
    ver = ver.replace(" x64", "")
    ver = ver.replace(" x86", "")
    ver = ver.replace(' Extension 2', '.5')
    ver = ver.strip()
    
    return ver
