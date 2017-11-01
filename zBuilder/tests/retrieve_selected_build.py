# this removes any mention of zBuilder in sys.modules so you get a clean import
import zBuilder.tests.utils as utl
utl.hard_reload('zBuilder')

import maya.cmds as mc
import zBuilder.zMaya as mz
import zBuilder.builders.ziva as zva


# This builds the Zivas anatomical arm demo with no pop up dialog.
utl.build_arm()

mc.select('r_bicep_muscle')

# use builder to retrieve from scene--------------------------------------------
z = zva.Ziva()
z.retrieve_from_scene_selection()


# build
z.build(check_meshes=False)
