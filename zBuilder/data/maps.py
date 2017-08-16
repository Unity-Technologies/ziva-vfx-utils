import maya.cmds as mc
import maya.mel as mm
import zBuilder.zMaya as mz

import logging

logger = logging.getLogger(__name__)


class Map(object):
    TYPE = 'map'

    def __init__(self, *args, **kwargs):

        self._class = (self.__class__.__module__, self.__class__.__name__)

        self._name = None
        self._mesh = None
        self._value = None
        if args:
            map_name = args[0]
            mesh_name = args[1]

            if map_name and mesh_name:
                self.create(map_name, mesh_name)

    def __str__(self):
        name = self.get_name()
        if self.get_value():
            length = len(self.get_value())
        else:
            length = 'null'
        output = ''
        output += '< MAP: {} -- length: {} >'.format(name, length)
        return output

    def __repr__(self):
        return self.__str__()

    def create(self, map_name, mesh_name):
        """

        Args:
            map_name:
            mesh_name:

        Returns:

        """
        weight_value = get_weights(map_name, mesh_name)

        self.set_name(map_name)
        self.set_mesh(mesh_name)
        self.set_value(weight_value)

    def get_name(self, long_name=False):
        """

        Args:
            long_name:

        Returns:

        """
        if self._name:
            if long_name:
                return self._name
            else:
                return self._name.split('|')[-1]
        else:
            return None
        
    def set_name(self, name):
        self._name = name   

    def set_mesh(self, mesh):
        self._mesh = mesh   

    def get_mesh(self, long_name=False):

        if self._mesh:
            if long_name:
                return self._mesh
            else:
                return self._mesh.split('|')[-1]
        else:
            return None

    def set_value(self, value):
        self._value = value

    def get_value(self):
        return self._value

    def string_replace(self, search, replace):
        # name replace----------------------------------------------------------
        name = self.get_name(long_name=True)
        newName = mz.replace_long_name(search, replace, name)
        self.set_name(newName)

        mesh = self.get_mesh(long_name=True)
        newMesh = mz.replace_long_name(search, replace, mesh)
        self.set_mesh(newMesh)



def set_weights(nodes,data,interp_maps=False):
    logger.info('DEPRECATED: Use .set_maya_weights_for_builder_node')
    for node in nodes:
        maps = node.get_maps()
        name = node.get_name()

        for mp in maps:
            mapData = data.get_data_by_key_name('map',mp)
            meshData = data.get_data_by_key_name('mesh',mapData.get_mesh(long_name=True))
            mname= meshData.get_name(long_name=True)
            mnameShort = meshData.get_name(long_name=False)
            wList = mapData.get_value()


            #mname= maps[attr]['mesh'] 
            #wList = maps[attr]['value']
            #mnameShort = mname.split('|')[-1]

            if mc.objExists(mnameShort):
                #mesh = meshes[mname]

                if interp_maps == 'auto':
                    
                    cur_conn = get_mesh_connectivity(mnameShort)

                    #print len(cur_conn['points']),len(mesh.get_point_list())
                    if len(cur_conn['points']) != len(meshData.get_point_list()):
                        interp_maps=True

                if interp_maps == True:
                    logger.info('interpolating maps...{}'.format(mp))
                    origMesh = meshData.build( )
                    wList = interpolateValues(origMesh,mnameShort,wList)

                if mc.objExists('%s[0]' % (mp)):
                    if not mc.getAttr('%s[0]' % (mp),l=True):
                        tmp = []
                        for w in wList:
                            tmp.append(str(w))
                        val = ' '.join(tmp)
                        cmd = "setAttr "+'%s[0:%d] ' % (mp, len(wList)-1)+val
                        #print 'setting',name,attr
                        mm.eval(cmd)

                else:
                    try:
                        #print 'here we go',name,attr,wList
                        mc.setAttr(mp,wList,type='doubleArray')
                    except:
                        pass
                if interp_maps == True:
                    mc.delete(origMesh)


def get_weights(map_name, mesh_name):
    """

    Args:
        map_name:
        mesh_name:

    Returns:

    """
    vert_count = mc.polyEvaluate(mesh_name, v=True)
    try:
        value = mc.getAttr('{}[0:{}]'.format(map_name, vert_count - 1))
    except ValueError:
        value = mc.getAttr(map_name)
    return value

