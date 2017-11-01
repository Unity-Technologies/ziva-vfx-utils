import maya.cmds as mc
import maya.mel as mm
import sys

'''
These are small utilities to help with testing zBuilder.  
'''


def build_mirror_sample_geo():
    """ Builds 2 sphere and a cube to test some basic mirroring stuff.
    """

    sph = mc.polySphere(name='r_muscle')[0]
    mc.setAttr(sph + '.t', -10, 5, 0)
    sph = mc.polySphere(name='l_muscle')[0]
    mc.setAttr(sph + '.t', 10, 5, 0)
    mc.setAttr(sph + '.s', -1, 1, 1)
    cub = mc.polyCube(name='bone')[0]
    mc.setAttr(cub + '.s', 15, 15, 3)
    mc.polyNormal('l_muscle', normalMode=0, userNormalMode=0, ch=0)
    mc.delete('r_muscle', 'l_muscle', 'bone', ch=True)
    mc.makeIdentity('r_muscle', 'l_muscle', 'bone', apply=True)


def ziva_mirror_sample_geo():
    """ sets up a bone and a tissue with constraint on the mirror geo sample
    """
    mc.select('bone')
    mm.eval('ziva -b')
    mc.select('r_muscle')
    mm.eval('ziva -t')

    mm.eval(
        'select -r r_muscle.vtx[60] r_muscle.vtx[78:81] r_muscle.vtx[97:101] r_muscle.vtx[117:122] r_muscle.vtx[137:142] r_muscle.vtx[157:162] r_muscle.vtx[177:179] r_muscle.vtx[197:199]')
    mc.select('bone', add=True)
    mm.eval('ziva -a')


def hard_reload(package):
    """
    This removes references to a package in the sys.module.  Useful for re-loading
    a module without having to restart maya.

    note:
        You should do a hard_reload then re-import what you need.
    Args:
        package:  The package you want to remove.

    Returns:
        nothing
    """
    tmp = []
    for item in sys.modules:
        if item.startswith(package):
            tmp.append(item)
    for i in tmp:
        del (sys.modules[i])


def build_arm():
    """
    This simply builds Ziva's anatomical arm demo for testing purposes.

    Returns:
        nothing
    """

    mc.loadPlugin('ziva')
    mc.file(new=True, f=True)
    mm.eval('ziva_loadArmGeometry_anatomicalArmDemo();')
    mm.eval('ziva -s;')

    mm.eval('ziva_makeBones_anatomicalArmDemo();')
    mm.eval('ziva_makeTissues_anatomicalArmDemo(1);')
    mm.eval('ziva_makeAttachments_anatomicalArmDemo();')
    mm.eval('ziva_makeMuscleFibers_anatomicalArmDemo();')
    mm.eval('ziva_setupMuscleFibersActivation();')

    mc.setAttr('zSolver1.collisionDetection', 1)
    mc.setAttr('zSolver1.substeps', 1)
    mc.setAttr('zSolver1.maxNewtonIterations', 2)
