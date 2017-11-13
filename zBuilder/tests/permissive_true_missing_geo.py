# this removes any mention of zBuilder in sys.modules so you get a clean import
import zBuilder.tests.utils as utl
utl.hard_reload('zBuilder')

import maya.cmds as mc
import zBuilder.zMaya as mz
import zBuilder.builders.ziva as zva


# This builds the Zivas anatomical arm demo with no pop up dialog.
utl.build_arm()

mc.select(cl=True)

# use builder to retrieve from scene--------------------------------------------
z = zva.Ziva()
z.retrieve_from_scene()

# remove ziva nodes from scene so all we have left is geo
mz.clean_scene()

# now lets delete bicep to see how build handles it
mc.delete('r_bicep_muscle')

# build
z.build(permissive=True)