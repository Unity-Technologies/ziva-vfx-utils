# this removes any mention of zBuilder in sys.modules so you get a clean import
import zBuilder.tests.utils as utl
utl.hard_reload('zBuilder')

import maya.cmds as mc
import zBuilder.zMaya as mz
import zBuilder.builders.ziva as zva


# ------------------------------------------------------------------------------
mc.file(new=True, f=True)

# Build a basic setup
utl.build_mirror_sample_geo()
utl.ziva_mirror_sample_geo()


mc.select(cl=True)

# use builder to retrieve from scene--------------------------------------------
z = zva.Ziva()
z.retrieve_from_scene()

# string replace
z.string_replace('^r_', 'l_')

# remove ziva nodes from scene so all we have left is geo
mz.clean_scene()

# build it on live scene
z.build()