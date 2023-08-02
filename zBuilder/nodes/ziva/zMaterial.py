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

    def do_build(self, *args, **kwargs):
        """ Builds the zMaterial in maya scene.

        Args:
            interp_maps (str): Interpolating maps.  Defaults to ``auto``
            target_prefix (str): Target prefix used for mirroring. Defaults to None
            center_prefix (str): Center prefix used for mirroring. Defaults to None
        """
        interp_maps = kwargs.get('interp_maps', 'auto')
        target_prefix = kwargs.get('target_prefix', None)
        center_prefix = kwargs.get('center_prefix', None)

        # When building a zMaterial node it is complicated by the fact that when tissues are created
        # a zMaterial node is created as well.  For something like a zTet it isnt a big deal because there is always only 1.
        # The user can add zMaterials so we need to make sure that we actually need to create the node.

        # Normal workflow if self.name is not in scene already we create it

        # get mesh name from data
        mesh = self.nice_association[0]
        if cmds.objExists(mesh):
            # get exsisting node names in scene on specific mesh and in data
            existing_materials = cmds.zQuery(mesh, t='zMaterial')
            data_materials = self.builder.get_scene_items(type_filter='zMaterial',
                                                          association_filter=mesh)

            # case 1: normal workflow.
            is_normal_workflow = (center_prefix is None)
            is_new_material = (self.name not in existing_materials)
            build_material_case1 = is_normal_workflow and is_new_material

            # case 2: mirrow workflow, not center mesh, new material and material name is not in scene
            is_mirror_workflow = not is_normal_workflow
            is_center_mesh = bool(center_prefix) and mesh.split('|')[-1].startswith(center_prefix)
            is_new_material_for_non_center_mesh = (len(existing_materials) < len(data_materials))
            build_material_case2 = is_mirror_workflow and (
                not is_center_mesh) and is_new_material_for_non_center_mesh and is_new_material

            # case 3: mirrow workflow, center mesh, new side material
            sided_materials = [x for x in data_materials
                               if x.name.startswith(target_prefix)] if target_prefix else []
            has_side_material_prefix = bool(target_prefix) and self.name.startswith(target_prefix)
            is_new_side_material = len(existing_materials) < (len(data_materials) +
                                                              len(sided_materials))
            build_material_case3 = is_mirror_workflow and is_center_mesh and has_side_material_prefix and is_new_side_material

            # Build material instance
            if any((build_material_case1, build_material_case2, build_material_case3)):
                cmds.select(mesh, r=True)
                results = cmds.ziva(m=True)
                self.name = safe_rename(results[0], self.name)
        else:
            logger.warning(mesh + ' does not exist in scene, skipping zMaterial creation')

        # Set/Update newly created or existing node attributes
        self.check_parameter_name()
        # set the attributes
        self.set_maya_attrs()
        # NOTE: On base material node weight attribute 'MATERIAL_NODE.weightList' is locked by zivaVFX.
        # Though it is locked, before Maya 2022.5, we could apply setAttr() on 'MATERIAL_NODE.weightList[0].weight'.
        # Since that behaviour changed, we need to explicitly check if parent is locked before calling setAttr().
        parent_weight_node = self.name + ".weightList"
        if not cmds.getAttr(parent_weight_node, l=True):
            self.set_maya_weights(interp_maps=interp_maps)
