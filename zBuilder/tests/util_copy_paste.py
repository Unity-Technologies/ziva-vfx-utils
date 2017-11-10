# this removes any mention of zBuilder in sys.modules so you get a clean import
import zBuilder.tests.utils as utl

utl.hard_reload('zBuilder')

import maya.cmds as mc
import zBuilder.zMaya as mz
import zBuilder.builders.ziva as zva

# This builds the Zivas anatomical arm demo with no pop up dialog.
utl.build_arm()

mc.select(cl=True)

mc.duplicate('r_bicep_muscle', name='dupe')
mc.polySmooth('dupe')
mc.select('r_bicep_muscle', 'dupe')

import zBuilder.util as utl

utl.copy_paste()
