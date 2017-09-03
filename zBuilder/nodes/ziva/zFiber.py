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
        return [self.get_association(long_name=True)[0],
                self.get_association(long_name=True)[0]]

    def apply(self, *args, **kwargs):

        attr_filter = kwargs.get('attr_filter', None)
        interp_maps = kwargs.get('interp_maps', 'auto')

        name = self.get_scene_name()
        mesh = self.get_association()[0]

        if mc.objExists(mesh):
            # get exsisting node names in scene on specific mesh and in data
            existing_fibers = mm.eval('zQuery -t zFiber {}'.format(mesh))
            data_fibers = self._parent.get_nodes(type_filter='zFiber',
                                         name_filter=mesh)

            # self.are_maps_valid()

            d_index = data_fibers.index(self)

            if existing_fibers:
                if d_index < len(existing_fibers):
                    self.set_mobject(existing_fibers[d_index])
                    mc.rename(existing_fibers[d_index], name)
                else:
                    mc.select(mesh, r=True)
                    results = mm.eval('ziva -f')
                    self.set_mobject(results[0])
                    mc.rename(results[0], name)
            else:
                mc.select(mesh, r=True)
                results = mm.eval('ziva -f')
                self.set_mobject(results[0])
                mc.rename(results[0], name)

        else:
            logger.warning(
                mesh + ' does not exist in scene, skipping zFiber creation')

        # set the attributes
        self.set_maya_attrs(attr_filter=attr_filter)
        self.set_maya_weights(interp_maps=interp_maps)

    # TODO need to interp maps before this check happens.
    def are_maps_valid(self):
        """
        Checking maps to see if they are all zeros.  An attachment map with
        only zero's fail.

        Returns:

        """
        map_name = self.get_maps()[1]
        map_object = self._parent.get_data_by_key_name('map', map_name)
        values = map_object.get_value()
        print self.get_name(), values
        if 0 not in values or 1 not in values:
            raise ValueError('{} bad map'.format(map_name))
