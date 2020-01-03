import maya.cmds as mc
import maya.mel as mm
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

        name = self.name
        source_mesh = self.association[0]
        target_mesh = self.association[1]

        # check if both meshes exist
        if mz.check_body_type([source_mesh, target_mesh]):
            # check existing attachments in scene
            cmd = 'zQuery -t zAttachment {}'.format(source_mesh)
            existing_attachments = mm.eval(cmd)
            existing = []
            if existing_attachments:
                for existing_attachment in existing_attachments:
                    att_s = mm.eval('zQuery -as ' + existing_attachment)[0]
                    att_t = mm.eval('zQuery -at ' + existing_attachment)[0]
                    if att_s == source_mesh and att_t == target_mesh:
                        existing.append(existing_attachment)

            data_attachments = self.builder.bundle.get_scene_items(type_filter='zAttachment',
                                                                   association_filter=source_mesh)
            data = []
            for data_attachment in data_attachments:
                data_s = data_attachment.association[0]
                data_t = data_attachment.association[1]
                if data_s == source_mesh and data_t == target_mesh:
                    data.append(data_attachment)

            d_index = data.index(self)

            if existing:
                if d_index < len(existing):
                    self.mobject = existing[d_index]
                    mc.rename(existing[d_index], name)
                else:
                    mc.select(source_mesh, r=True)
                    mc.select(target_mesh, add=True)
                    new_att = mm.eval('ziva -a')
                    self.mobject = new_att[0]
                    mc.rename(new_att[0], name)
            else:
                mc.select(source_mesh, r=True)
                mc.select(target_mesh, add=True)
                new_att = mm.eval('ziva -a')
                self.mobject = new_att[0]
                mc.rename(new_att[0], name)

            # set the attributes
            self.set_maya_attrs(attr_filter=attr_filter)
            self.set_maya_weights(interp_maps=interp_maps)

        else:
            if permissive:
                logger.info('skipping attachment creation...' + name)
            else:
                raise Exception('Cannot create attachment between {} and {}.  Check meshes.'.format(
                    source_mesh, target_mesh))
