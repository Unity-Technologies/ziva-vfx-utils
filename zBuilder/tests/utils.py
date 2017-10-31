import maya.cmds as mc
import maya.mel as mm

import sys


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
        del(sys.modules[i])


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
