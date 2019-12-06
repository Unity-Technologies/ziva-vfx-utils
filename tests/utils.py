import tempfile
import maya.cmds as mc
import maya.mel as mm
import os
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
        'select -r r_muscle.vtx[60] r_muscle.vtx[78:81] r_muscle.vtx[97:101] r_muscle.vtx[117:122] r_muscle.vtx[137:142] r_muscle.vtx[157:162] r_muscle.vtx[177:179] r_muscle.vtx[197:199]'
    )
    mc.select('bone', add=True)
    mm.eval('ziva -a')


def get_ziva_node_names_from_builder(builder):
    # get items that has z + Capital case letter and don't have dots ( to exclude maps )
    # this will list all Ziva nodes excluding meshes and maps
    node_names = [obj.name for obj in builder.get_scene_items(name_regex="z[A-Z][^\.]*$")]
    return node_names


def build_generic_scene(new_scene=True, scene_name='generic.ma'):
    path = CURRENT_DIRECTORY_PATH + "{}/assets/{}".format(CURRENT_DIRECTORY_PATH, scene_name)
    if new_scene:
        mc.file(new=True, force=True)
    # import with no namespace
    mc.file(path, i=True, ns=":", ignoreVersion=True)


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
        mc.file(new=True, force=True)

    mm.eval('ziva_loadArmGeometry_anatomicalArmDemo();')

    if ziva_setup:
        mm.eval('ziva -s;')

        mm.eval('ziva_makeBones_anatomicalArmDemo();')
        mm.eval('ziva_makeTissues_anatomicalArmDemo(1);')
        mm.eval('ziva_makeAttachments_anatomicalArmDemo();')
        mm.eval('ziva_makeMuscleFibers_anatomicalArmDemo();')
        mm.eval('ziva_setupMuscleFibersActivation();')

        mc.setAttr('zSolver1.collisionDetection', 1)
        mc.setAttr('zSolver1.substeps', 1)
        mc.setAttr('zSolver1.maxNewtonIterations', 2)


def retrieve_builder_from_scene():
    """ Get a new zBuilder.builders.ziva.Ziva() with everything retrieved from scene."""
    original_selection = mc.ls(selection=True)
    mc.select(clear=True)
    builder = zva.Ziva()
    builder.retrieve_from_scene()
    mc.select(original_selection, replace=True)
    return builder


def retrieve_builder_from_file(file_name):
    """ Get a new zBuilder.builders.ziva.Ziva() retrieved from the given file. """
    builder = zva.Ziva()
    builder.retrieve_from_file(file_name)
    return builder
