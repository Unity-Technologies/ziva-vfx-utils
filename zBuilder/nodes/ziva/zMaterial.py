import logging

from maya import cmds
from zBuilder.utils.mayaUtils import safe_rename
from .zivaBase import Ziva

logger = logging.getLogger(__name__)


class MaterialNode(Ziva):
    """ This node for storing information related to zMaterials.
    """
    type = 'zMaterial'

    # List of maps to store
    MAP_LIST = ['weightList[0].weights']

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
            existing_materials = cmds.zQuery(mesh, t='zMaterial')

            # Check if material already exists on mesh
            if self.name not in existing_materials:
                cmds.select(mesh, r=True)
                results = cmds.ziva(m=True)
                self.name = safe_rename(results[0], self.name)
        else:
            logger.warning(mesh + ' does not exist in scene, skipping zMaterial creation')

        self.check_parameter_name()

        # set the attributes
        self.set_maya_attrs(attr_filter=attr_filter)
        self.set_maya_weights(interp_maps=interp_maps)
