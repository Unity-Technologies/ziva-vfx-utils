from zBuilder.nodes import Ziva
import maya.cmds as mc
import maya.mel as mm
import zBuilder.zMaya as mz
import logging

logger = logging.getLogger(__name__)


class FiberNode(Ziva):
    """ This node for storing information related to zFibers.
    """
    type = 'zFiber'
    """ The type of node. """
    MAP_LIST = ['weightList[0].weights', 'endPoints']
    """ List of maps to store. """

    def __init__(self, *args, **kwargs):
        Ziva.__init__(self, *args, **kwargs)

    def get_map_meshes(self):
        """
        This is the mesh associated with each map in obj.MAP_LIST.  Typically
        it seems to coincide with mesh store in get_association.  Sometimes
        it deviates, so you can override this method to define your own
        list of meshes against the map list.

        Returns:
            list(): of long mesh names.
        """
        return [self.association[0],
                self.association[0]]

    def build(self, *args, **kwargs):
        """ Builds the zFiber in maya scene.

        Args:
            attr_filter (dict):  Attribute filter on what attributes to get.
                dictionary is key value where key is node type and value is
                list of attributes to use.

                tmp = {'zSolver':['substeps']}
            interp_maps (str): Interpolating maps.  Defaults to ``auto``
            permissive (bool): Pass on errors. Defaults to ``True``
        """
        attr_filter = kwargs.get('attr_filter', list())
        permissive = kwargs.get('permissive', True)
        interp_maps = kwargs.get('interp_maps', 'auto')

        name = self.name
        mesh = self.association[0]

        if mc.objExists(mesh):
            # get exsisting node names in scene on specific mesh and in data
            existing_fibers = mm.eval('zQuery -t zFiber {}'.format(mesh))
            data_fibers = self.builder.bundle.get_scene_items(type_filter='zFiber',
                                                              association_filter=mesh)

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
        self.set_maya_weights(interp_maps=interp_maps)

    # def are_maps_valid(self):
    #     """
    #     Checking just fiber .endPoint maps.  These maps are mostly .5 and at
    #     at least one vert needs to be between .9 and 1 and another needs to
    #     be between 0 and .1.  This is defining the direction of the fibers
    #     so things do not work if these requirements are not met.
    #
    #     This checks for that case.
    #
    #     Raises:
    #         ValueError: If map fails test.
    #
    #     """
    #     map_name = self.get_map_names()[1]
    #     map_object = self.builder.bundle.get_scene_items(type_filter='map',
    #                                                     name_filter=map_name)
    #     values = map_object.values
    #
    #     upper = False
    #     lower = False
    #     if any(0 <= v <= .1 for v in values):
    #         lower = True
    #     if any(.9 <= v <= 1 for v in values):
    #         upper = True
    #
    #     if not upper and not lower:
    #         raise ValueError('{} map does not have a 1 or 0.  Please check map.'.format(map_name))
    #     if not upper:
    #         raise ValueError('{} map does not have a 1.  Please check map.'.format(map_name))
    #     if not lower:
    #         raise ValueError('{} map does not have a 0.  Please check map.'.format(map_name))
