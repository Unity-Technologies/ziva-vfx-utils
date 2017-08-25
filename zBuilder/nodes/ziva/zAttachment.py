import maya.cmds as mc
import maya.mel as mm
import zBuilder.zMaya as mz

from zBuilder.nodes import ZivaBaseNode
import logging

logger = logging.getLogger(__name__)


class AttachmentNode(ZivaBaseNode):
    TYPE = 'zAttachment'
    MAP_LIST = ['weightList[0].weights', 'weightList[1].weights']

    def __init__(self, *args, **kwargs):
        ZivaBaseNode.__init__(self, *args, **kwargs)

    def apply(self, *args, **kwargs):
        attr_filter = kwargs.get('attr_filter', None)
        interp_maps = kwargs.get('interp_maps', 'auto')

        name = self.get_scene_name()
        source_mesh = self.get_association()[0]
        t_mesh = self.get_association()[1]

        # check if both meshes exist
        if mz.check_body_type([source_mesh, t_mesh]):
            # check existing attachments in scene
            cmd = 'zQuery -t zAttachment {}'.format(source_mesh)
            existing_attachments = mm.eval(cmd)
            existing = []
            if existing_attachments:
                for existing_attachment in existing_attachments:
                    att_s = mm.eval('zQuery -as ' + existing_attachment)[0]
                    att_t = mm.eval('zQuery -at ' + existing_attachment)[0]
                    if att_s == source_mesh and att_t == t_mesh:
                        existing.append(existing_attachment)

            data_attachments = self._parent.get_nodes(type_filter='zAttachment',
                                              name_filter=source_mesh)
            data = []
            for data_attachment in data_attachments:
                data_s = data_attachment.get_association()[0]
                data_t = data_attachment.get_association()[1]
                if data_s == source_mesh and data_t == t_mesh:
                    data.append(data_attachment)

            d_index = data.index(self)

            if existing:
                if d_index < len(existing):
                    self.set_mobject(existing[d_index])
                    mc.rename(existing[d_index], name)
                else:
                    mc.select(source_mesh, r=True)
                    mc.select(t_mesh, add=True)
                    new_att = mm.eval('ziva -a')
                    self.set_mobject(new_att[0])
                    mc.rename(new_att[0], name)
            else:
                mc.select(source_mesh, r=True)
                mc.select(t_mesh, add=True)
                new_att = mm.eval('ziva -a')
                self.set_mobject(new_att[0])
                mc.rename(new_att[0], name)

        else:
            print mc.warning('skipping attachment creation...' + name)

        # set the attributes
        self.set_maya_attrs(attr_filter=attr_filter)
        self.set_maya_weights(interp_maps=interp_maps)

