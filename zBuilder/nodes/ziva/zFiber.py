from zBuilder.nodes import ZivaBaseNode
import maya.cmds as mc
import maya.mel as mm
import zBuilder.zMaya as mz
import logging

logger = logging.getLogger(__name__)


class FiberNode(ZivaBaseNode):
    TYPE = 'zFiber'
    MAP_LIST = ['weightList[0].weights', 'endPoints']

    def __init__(self, *args, **kwargs):
        ZivaBaseNode.__init__(self, *args, **kwargs)

    def get_map_meshes(self):
        """
        This is the mesh associated with each map in obj.MAP_LIST.  Typically
        it seems to coincide with mesh store in get_association.  Sometimes
        it deviates, so you can override this method to define your own
        list of meshes against the map list.

        Returns:
            list(): of long mesh names.
        """
        return [self.long_association[0],
                self.long_association[0]]

    def apply(self, *args, **kwargs):

        attr_filter = kwargs.get('attr_filter', list())
        name_filter = kwargs.get('name_filter', list())
        permissive = kwargs.get('permissive', True)
        interp_maps = kwargs.get('interp_maps', 'auto')

        name = self.get_scene_name()
        mesh = self.association[0]

        if mc.objExists(mesh):
            # get exsisting node names in scene on specific mesh and in data
            existing_fibers = mm.eval('zQuery -t zFiber {}'.format(mesh))
            data_fibers = self._setup.get_nodes(type_filter='zFiber',
                                                name_filter=mesh)

            # self.interpolate_maps(interp_maps)
            # self.are_maps_valid()

            d_index = data_fibers.index(self)

            if existing_fibers:
                if d_index < len(existing_fibers):
                    self.mobject = existing_fibers[d_index]
                    mc.rename(existing_fibers[d_index], name)
                else:
                    mc.select(mesh, r=True)
                    results = mm.eval('ziva -f')
                    self.mobject = results[0]
                    mc.rename(results[0], name)
            else:
                mc.select(mesh, r=True)
                results = mm.eval('ziva -f')
                self.mobject = results[0]
                mc.rename(results[0], name)
        else:
            logger.warning(
                mesh + ' does not exist in scene, skipping zFiber creation')

        # set the attributes
        self.set_maya_attrs(attr_filter=attr_filter)
        self.set_maya_weights(interp_maps=False)

    def are_maps_valid(self):
        """
        Checking jsut fiber .endPoint maps.  These maps are mostly .5 and at
        at least one vert needs to be between .9 and 1 and another needs to
        be between 0 and .1.  This is defining the direction of the fibers
        so things do not work if these requirements are not met.

        This checks for that case.

        Raises:
            ValueError: If map fails test.

        """
        map_name = self.get_map_names()[1]
        map_object = self._setup.get_data(type_filter='map',
                                          name_filter=map_name)
        values = map_object.value

        upper = False
        lower = False
        if any(0 <= v <= .1 for v in values):
            lower = True
        if any(.9 <= v <= 1 for v in values):
            upper = True

        if not upper and not lower:
            raise ValueError('{} map does not have a 1 or 0.  Please check map.'.format(map_name))
        if not upper:
            raise ValueError('{} map does not have a 1.  Please check map.'.format(map_name))
        if not lower:
            raise ValueError('{} map does not have a 0.  Please check map.'.format(map_name))
