import tempfile
import glob
import os

from maya import cmds
from maya import mel

import zBuilder.builders.ziva as zva
'''
These are small utilities to help with testing zBuilder.  Probably no real value
outside of testing. 
'''

CURRENT_DIRECTORY_PATH = os.path.dirname(os.path.realpath(__file__))


def get_tmp_file_location():
    """Using the tempfile module this creates a tempfile and deletes it (os.close) and 
    returns the name/location which is all we need to deal with files.
    
    Returns:
        string: file path 
    """
    temp = tempfile.TemporaryFile()

    # this closes the file and deletes it.  We just need to name of it.
    temp.close()

    return temp.name


def build_mirror_sample_geo():
    """ Builds 2 sphere and a cube to test some basic mirroring stuff.
    """

    sph = cmds.polySphere(name='r_muscle')[0]
    cmds.setAttr(sph + '.t', -10, 5, 0)
    sph = cmds.polySphere(name='l_muscle')[0]
    cmds.setAttr(sph + '.t', 10, 5, 0)
    cmds.setAttr(sph + '.s', -1, 1, 1)
    cub = cmds.polyCube(name='bone')[0]
    cmds.setAttr(cub + '.s', 15, 15, 3)
    cmds.polyNormal('l_muscle', normalMode=0, userNormalMode=0, ch=0)
    cmds.delete('r_muscle', 'l_muscle', 'bone', ch=True)
    cmds.makeIdentity('r_muscle', 'l_muscle', 'bone', apply=True)


def ziva_mirror_sample_geo():
    """ sets up a bone and a tissue with constraint on the mirror geo sample
    """
    cmds.select('bone')
    mel.eval('ziva -b')
    cmds.select('r_muscle')
    mel.eval('ziva -t')

    mel.eval(
        'select -r r_muscle.vtx[60] r_muscle.vtx[78:81] r_muscle.vtx[97:101] r_muscle.vtx[117:122] r_muscle.vtx[137:142] r_muscle.vtx[157:162] r_muscle.vtx[177:179] r_muscle.vtx[197:199]'
    )
    cmds.select('bone', add=True)
    mel.eval('ziva -a')


def get_ziva_node_names_from_builder(builder, long=False):
    # get items that has z + Capital case letter and don't have dots ( to exclude maps )
    # this will list all Ziva nodes excluding meshes and maps
    node_names = [
        obj.name if not long else obj.long_name
        for obj in builder.get_scene_items(name_regex="z[A-Z][^\.]*$")
    ]
    return node_names


def reference_scene(new_scene=True, scene_name='generic.ma', namespace="TEMP"):
    """Loading a maya test scene based on name.  These are maya files in the repo
    so it searches for proper file based on current directoy.

    Args:
        new_scene (bool, optional): If True forces a new scene.. Defaults to True.
        scene_name (str, optional): Name of the file to reference. Defaults to 'generic.ma'.
        namespace (str, optional): The namespace to use for referenced file.
                                            ":" is equal to no namespace. Defaults to "TEMP".
    """
    path = "{}/assets/{}".format(CURRENT_DIRECTORY_PATH, scene_name)
    if new_scene:
        cmds.file(new=True, force=True)

    cmds.file(path, reference=True, namespace=namespace, ignoreVersion=True)


def load_scene(new_scene=True, scene_name='generic.ma'):
    path = "{}/assets/{}".format(CURRENT_DIRECTORY_PATH, scene_name)
    if new_scene:
        cmds.file(new=True, force=True)

    # import with no namespace
    cmds.file(path, i=True, ns=":", ignoreVersion=True)


def get_1_7_builder_files():
    """Part of the test assets includes zBuilder files saved in 1_7.  This is to test 
    backwards compatibility.  Building with these should still work after 1_9.

    Returns:
        list of str: list of paths to 1_7 zBuilder files. 
    """
    directory = "{}/assets".format(CURRENT_DIRECTORY_PATH)
    builders = glob.glob(directory + '/*.zBuilder')
    return builders


def build_anatomical_arm_with_no_popup(ziva_setup=True, new_scene=True):
    """This simply builds Ziva's anatomical arm demo for testing purposes.

    Args:
        ziva_setup (bool): If True this will do the Ziva setup on arm.  Else it 
        just brings in geometry.
        new_scene (bool): If true it forces a new scene.
    Returns:
        nothing
    """
    if new_scene:
        cmds.file(new=True, force=True)

    mel.eval('ziva_loadArmGeometry_anatomicalArmDemo();')

    if ziva_setup:
        mel.eval('ziva -s;')

        mel.eval('ziva_makeBones_anatomicalArmDemo();')
        mel.eval('ziva_makeTissues_anatomicalArmDemo(1);')
        mel.eval('ziva_makeAttachments_anatomicalArmDemo();')
        mel.eval('ziva_makeMuscleFibers_anatomicalArmDemo();')
        mel.eval('ziva_setupMuscleFibersActivation();')

        cmds.setAttr('zSolver1.collisionDetection', 1)
        cmds.setAttr('zSolver1.substeps', 1)
        cmds.setAttr('zSolver1.maxNewtonIterations', 2)


def retrieve_builder_from_scene():
    """ Get a new zBuilder.builders.ziva.Ziva() with everything retrieved from scene."""
    original_selection = cmds.ls(selection=True)
    cmds.select(clear=True)
    builder = zva.Ziva()
    builder.retrieve_from_scene()
    cmds.select(original_selection, replace=True)
    return builder


def retrieve_builder_from_file(file_name):
    """ Get a new zBuilder.builders.ziva.Ziva() retrieved from the given file. """
    builder = zva.Ziva()
    builder.retrieve_from_file(file_name)
    return builder
