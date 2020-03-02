from maya import cmds
from maya import mel
import zBuilder.zMaya as mz

from zBuilder.nodes import Ziva
import logging

logger = logging.getLogger(__name__)


class MaterialNode(Ziva):
    """ This node for storing information related to zMaterials.
    """
    type = 'zMaterial'
    """ The type of node. """

    MAP_LIST = ['weightList[0].weights']
    """ List of maps to store. """

    def build(self, *args, **kwargs):
        """ Builds the zMaterial in maya scene.

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

        # - check for existing materials on associated mesh for each material
        # - check amount of materials on mesh in zBuilder data
        # - name existing ones same as in data
        # - build remaining
        # - set attrs and weights

        # get mesh name from data
        mesh = self.nice_association[0]

        if cmds.objExists(mesh):
            # get exsisting node names in scene on specific mesh and in data
            existing_materials = mel.eval('zQuery -t zMaterial {}'.format(mesh))
            if not existing_materials:
                existing_materials = []
            data_materials = self.builder.bundle.get_scene_items(type_filter='zMaterial',
                                                                 association_filter=mesh)

            try:
                d_index = data_materials.index(self)
            except ValueError:
                d_index = 0

            # if there are enough existing materials use those
            # or else create a new material
            if d_index < len(existing_materials):
                self.name = mz.safe_rename(existing_materials[d_index], self.name)
            else:
                cmds.select(mesh, r=True)
                results = mel.eval('ziva -m')
                self.name = mz.safe_rename(results[0], self.name)
        else:
            logger.warning(mesh + ' does not exist in scene, skipping zMaterial creation')

        # set the attributes
        self.set_maya_attrs(attr_filter=attr_filter)
        self.set_maya_weights(interp_maps=interp_maps)
