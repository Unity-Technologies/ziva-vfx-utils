import logging

from maya import cmds
from zBuilder.vfxUtils import check_body_type
from zBuilder.mayaUtils import safe_rename
from .zivaBase import Ziva

logger = logging.getLogger(__name__)


class AttachmentNode(Ziva):
    """ This node for storing information related to zAttachments.
    """
    type = 'zAttachment'

    # List of maps to store
    MAP_LIST = ['weightList[0].weights', 'weightList[1].weights']

    def build(self, *args, **kwargs):
        """ Builds the zAttachment in maya scene.

        Args:
            attr_filter (dict):  Attribute filter on what attributes to get.
                dictionary is key value where key is node type and value is
                list of attributes to use.

                tmp = {'zSolver':['substeps']}
            interp_maps (str): Interpolating maps.  Defaults to ``auto``
            permissive (bool): Pass on errors. Defaults to ``True``
        """
        attr_filter = kwargs.get('attr_filter', None)
        interp_maps = kwargs.get('interp_maps', 'auto')
        permissive = kwargs.get('permissive', True)

        source_mesh = self.nice_association[0]
        target_mesh = self.nice_association[1]
        # check if both meshes exist
        if check_body_type([source_mesh, target_mesh]):
            # check existing attachments in scene
            existing_attachments = cmds.zQuery(source_mesh, t='zAttachment')
            existing = []
            if existing_attachments:
                for existing_attachment in existing_attachments:
                    att_s = cmds.zQuery(existing_attachment, attachmentSource=True, l=True)[0]
                    att_t = cmds.zQuery(existing_attachment, attachmentTarget=True, l=True)[0]
                    if att_s == source_mesh and att_t == target_mesh:
                        existing.append(existing_attachment)

            data_attachments = self.builder.get_scene_items(type_filter='zAttachment',
                                                            association_filter=source_mesh)
            data = []
            for data_attachment in data_attachments:
                data_s = data_attachment.nice_association[0]
                data_t = data_attachment.nice_association[1]
                if data_s == source_mesh and data_t == target_mesh:
                    data.append(data_attachment)

            d_index = data.index(self)

            if existing:
                # TODO: Update following logic. Check JIRA issue VFXACT-1110
                if d_index < len(existing):
                    self.name = safe_rename(existing[d_index], self.name)
                else:
                    cmds.select(source_mesh, r=True)
                    cmds.select(target_mesh, add=True)
                    new_att = cmds.ziva(a=True)
                    self.name = safe_rename(new_att[0], self.name)
            else:
                cmds.select(source_mesh, r=True)
                cmds.select(target_mesh, add=True)
                new_att = cmds.ziva(a=True)
                self.name = safe_rename(new_att[0], self.name)

            self.check_parameter_name()

            # set the attributes
            self.set_maya_attrs(attr_filter=attr_filter)
            self.set_maya_weights(interp_maps=interp_maps)

        else:
            if permissive:
                logger.info('skipping attachment creation...' + self.name)
            else:
                raise Exception('Cannot create attachment between {} and {}.  Check meshes.'.format(
                    source_mesh, target_mesh))
