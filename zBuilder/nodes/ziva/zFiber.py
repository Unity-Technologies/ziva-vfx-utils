from zBuilder.nodes import Ziva
from maya import cmds
from maya import mel
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

    def spawn_parameters(self):
        """

        Returns:

        """
        objs = {}
        if self.nice_association:
            objs['mesh'] = self.nice_association

        mesh_names = self.get_map_meshes()
        map_names = self.get_map_names()
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

        mesh = self.nice_association[0]

        if cmds.objExists(mesh):
            # get exsisting node names in scene on specific mesh and in data
            existing_fibers = mel.eval('zQuery -t zFiber {}'.format(mesh))
            data_fibers = self.builder.bundle.get_scene_items(type_filter='zFiber',
                                                              association_filter=mesh)

            try:
                d_index = data_fibers.index(self)
            except ValueError:
                d_index = 0

            if existing_fibers:
                if d_index < len(existing_fibers):
                    self.name = mz.safe_rename(existing_fibers[d_index], self.name)
                else:
                    cmds.select(mesh, r=True)
                    results = mel.eval('ziva -f')
                    self.name = mz.safe_rename(results[0], self.name)
            else:
                cmds.select(mesh, r=True)
                results = mel.eval('ziva -f')
                self.name = mz.safe_rename(results[0], self.name)
        else:
            logger.warning(mesh + ' does not exist in scene, skipping zFiber creation')

        # set the attributes
        self.set_maya_attrs(attr_filter=attr_filter)
        self.set_maya_weights(interp_maps=interp_maps)
