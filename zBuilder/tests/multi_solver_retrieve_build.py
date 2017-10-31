# this removes any mention of zBuilder in sys.modules so you get a clean import
import zBuilder.tests.utils as utl
utl.hard_reload('zBuilder')

import maya.cmds as mc
import maya.cmds as mm
import zBuilder.zMaya as mz
import zBuilder.builders.ziva as zva


# This builds the Zivas anatomical arm demo with no pop up dialog.  Use this as solver 1
import zBuilder.tests.utils as utl
utl.build_arm()

mc.select(cl=True)

# build another solver and add a tissue to it
# mm.eval('ziva -s')
sss = mc.ziva(s=True)
sphere = mc.polySphere()
mc.select(sphere[0], sss[0])
mc.ziva(t=True)

#
# use builder to retrieve from scene--------------------------------------------
z1 = zva.Ziva()
z1.retrieve_from_scene('zSolver1')

z2 = zva.Ziva()
z2.retrieve_from_scene('zSolver2')

# remove ziva nodes from scene so all we have left is geo
mz.clean_scene()
#
# build
z1.build(check_meshes=False)

z2.build(check_meshes=False)
