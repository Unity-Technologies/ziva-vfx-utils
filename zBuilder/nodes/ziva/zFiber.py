import logging

from maya import cmds
from zBuilder.utils.mayaUtils import safe_rename, construct_map_names
from zBuilder.utils.commonUtils import none_to_empty
from .zivaBase import Ziva

logger = logging.getLogger(__name__)


class FiberNode(Ziva):
    """ This node for storing information related to zFibers.
    """
    type = 'zFiber'

    # List of maps to store
    MAP_LIST = ['weightList[0].weights', 'endPoints']

    def spawn_parameters(self):
        objs = {}
        if self.nice_association:
            objs['mesh'] = self.nice_association

        mesh_names = self.get_map_meshes()
        map_names = construct_map_names(self.name, self.MAP_LIST)
        if map_names and mesh_names:
            objs['map'] = []
            for map_name, mesh_name in zip(map_names, mesh_names):
                if '.endPoints' in map_name:
                    objs['map'].append([map_name, mesh_name, "endPoints"])
                else:
                    objs['map'].append([map_name, mesh_name, "barycentric"])
        return objs

    def get_map_meshes(self):
        """
        This is the mesh associated with each map in obj.MAP_LIST.  Typically
        it seems to coincide with mesh store in get_association.  Sometimes
        it deviates, so you can override this method to define your own
        list of meshes against the map list.

        Returns:
            list(): of long mesh names.
        """
        return [self.nice_association[0], self.nice_association[0]]

    def do_build(self, *args, **kwargs):
        """ Builds the zFiber in maya scene.

        Args:
            interp_maps (str): Interpolating maps.  Defaults to ``auto``
        """
        interp_maps = kwargs.get('interp_maps', 'auto')

        mesh = self.nice_association[0]

        if cmds.objExists(mesh):
            # get exsisting node names in scene on specific mesh and in data
            existing_fibers = none_to_empty(cmds.zQuery(mesh, t='zFiber'))

            if self.name not in existing_fibers:
                cmds.select(mesh, r=True)
                results = cmds.ziva(f=True)
                self.name = safe_rename(results[0], self.name)
        else:
            logger.warning(mesh + ' does not exist in scene, skipping zFiber creation')

        self.check_parameter_name()

        # set the attributes
        self.set_maya_attrs()
        self.set_maya_weights(interp_maps=interp_maps)
