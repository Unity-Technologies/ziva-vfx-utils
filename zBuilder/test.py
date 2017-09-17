import misc_util as mu
mu.hard_reload('zBuilder')

mc.select('zSolver1')
import zBuilder.setup.Ziva2 as zva
z = zva.ZivaSetup()
z.retrieve_from_scene(mc.ls(sl=True)[0])
# z.print_(type_filter='zBone')
# z.stats()

z.apply()

z.write('C:\\Temp\\test.ziva', component_data=False)
z.retrieve_from_file('C:\\Temp\\test.ziva')



# for node in z.get_nodes():
#     print node
#     print node.__dict__
#     break


import zBuilder.nodes.base as base
#sol.__dict__

import zBuilder.nodes as nds
reload(nds)