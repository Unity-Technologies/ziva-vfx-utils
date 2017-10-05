import maya.cmds as mc
import maya.mel as mm
import zBuilder.zMaya as mz

from zBuilder.nodes import ZivaBaseNode
import logging

logger = logging.getLogger(__name__)


class MaterialNode(ZivaBaseNode):
    """ This node for storing information related to zMaterials.
    """
    type = 'zMaterial'
    """ The type of node. """

    MAP_LIST = ['weightList[0].weights']
    """ List of maps to store. """

    def __init__(self, *args, **kwargs):
        ZivaBaseNode.__init__(self, *args, **kwargs)

    def apply(self, *args, **kwargs):
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

        # get mesh name and node name from data
        name = self.get_scene_name()
        mesh = self.association[0]

        # logger.info('creating material {}'.format(name))

        if mc.objExists(mesh):
            # get exsisting node names in scene on specific mesh and in data
            existing_materials = mm.eval(
                'zQuery -t zMaterial {}'.format(mesh))
            data_materials = self._setup.get_nodes(type_filter='zMaterial',
                                                   association_filter=mesh)

            d_index = data_materials.index(self)

            # if there are enough existing materials use those
            # or else create a new material
            if d_index < len(existing_materials):
                self.mobject = existing_materials[d_index]
                mc.rename(existing_materials[d_index], name)
            else:
                mc.select(mesh, r=True)
                results = mm.eval('ziva -m')
                self.mobject = results[0]
                mc.rename(results[0], name)
        else:
            logger.warning(
                mesh + ' does not exist in scene, skipping zMaterial creation')

        # set the attributes
        self.set_maya_attrs(attr_filter=attr_filter)
        self.set_maya_weights(interp_maps=interp_maps)
