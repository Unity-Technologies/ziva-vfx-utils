# this removes any mention of zBuilder in sys.modules so you get a clean import
import zBuilder.tests.utils as utl
utl.hard_reload('zBuilder')

import maya.cmds as mc
import zBuilder.zMaya as mz
import zBuilder.builders.ziva as zva

TEMP = 'C:\\Temp\\retrieve_build_test.ziva'
""" Where to save temp builder file """

# This builds the Zivas anatomical arm demo with no pop up dialog.
utl.build_arm()

mc.select(cl=True)
# use builder to retrieve from scene--------------------------------------------
z = zva.Ziva()
z.retrieve_from_scene()

# write out---------------------------------------------------------------------
z.write(TEMP)

# remove ziva nodes from scene so all we have left is geo
mz.clean_scene()

# retrieve from file
z = zva.Ziva()
z.retrieve_from_file(TEMP)

# build
z.build(check_meshes=False)



















