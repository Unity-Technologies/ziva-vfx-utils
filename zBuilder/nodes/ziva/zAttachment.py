from maya import cmds
from maya import mel
import zBuilder.zMaya as mz

from zBuilder.nodes import Ziva
import logging

logger = logging.getLogger(__name__)


class AttachmentNode(Ziva):
    """ This node for storing information related to zAttachments.
    """
    type = 'zAttachment'
    """ The type of node. """
    MAP_LIST = ['weightList[0].weights', 'weightList[1].weights']
    """ List of maps to store. """

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
        if mz.check_body_type([source_mesh, target_mesh]):
            # check existing attachments in scene
            cmd = 'zQuery -t zAttachment {}'.format(source_mesh)
            existing_attachments = mel.eval(cmd)
            existing = []
            if existing_attachments:
                for existing_attachment in existing_attachments:
                    att_s = mel.eval('zQuery -as ' + existing_attachment)[0]
                    att_t = mel.eval('zQuery -at ' + existing_attachment)[0]
                    if att_s == source_mesh and att_t == target_mesh:
                        existing.append(existing_attachment)

            data_attachments = self.builder.bundle.get_scene_items(type_filter='zAttachment',
                                                                   association_filter=source_mesh)
            data = []
            for data_attachment in data_attachments:
                data_s = data_attachment.nice_association[0]
                data_t = data_attachment.nice_association[1]
                if data_s == source_mesh and data_t == target_mesh:
                    data.append(data_attachment)

            d_index = data.index(self)

            if existing:
                if d_index < len(existing):
                    self.name = mz.safe_rename(existing[d_index], self.name)
                else:
                    cmds.select(source_mesh, r=True)
                    cmds.select(target_mesh, add=True)
                    new_att = mel.eval('ziva -a')
                    self.name = mz.safe_rename(new_att[0], self.name)
            else:
                cmds.select(source_mesh, r=True)
                cmds.select(target_mesh, add=True)
                new_att = mel.eval('ziva -a')
                self.name = mz.safe_rename(new_att[0], self.name)

            # set the attributes
            self.set_maya_attrs(attr_filter=attr_filter)
            self.set_maya_weights(interp_maps=interp_maps)

        else:
            if permissive:
                logger.info('skipping attachment creation...' + self.name)
            else:
                raise Exception('Cannot create attachment between {} and {}.  Check meshes.'.format(
                    source_mesh, target_mesh))
