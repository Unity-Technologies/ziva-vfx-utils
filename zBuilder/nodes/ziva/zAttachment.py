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
        permissive = kwargs.get('permissive', True)

        name = self.get_scene_name()
        source_mesh = self.get_association()[0]
        target_mesh = self.get_association()[1]

        self.are_maps_valid()

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

            data_attachments = self._setup.get_nodes(type_filter='zAttachment',
                                                     name_filter=source_mesh)
            data = []
            for data_attachment in data_attachments:
                data_s = data_attachment.get_association()[0]
                data_t = data_attachment.get_association()[1]
                if data_s == source_mesh and data_t == target_mesh:
                    data.append(data_attachment)

            d_index = data.index(self)
            self.interpolate_maps(interp_maps)

            if existing:
                if d_index < len(existing):
                    self.set_mobject(existing[d_index])
                    mc.rename(existing[d_index], name)
                else:
                    mc.select(source_mesh, r=True)
                    mc.select(target_mesh, add=True)
                    new_att = mm.eval('ziva -a')
                    self.set_mobject(new_att[0])
                    mc.rename(new_att[0], name)
            else:
                mc.select(source_mesh, r=True)
                mc.select(target_mesh, add=True)
                new_att = mm.eval('ziva -a')
                self.set_mobject(new_att[0])
                mc.rename(new_att[0], name)

        else:
            if permissive:
                logger.info('skipping attachment creation...' + name)
            else:
                raise StandardError('Cannot create attachment between {} and {}.  Check meshes.'.format(source_mesh,target_mesh))

        # set the attributes
        self.set_maya_attrs(attr_filter=attr_filter)
        self.set_maya_weights(interp_maps=False)

    # TODO need to interp maps before this check happens.
    def are_maps_valid(self):
        """
        Checking maps to see if they are all zeros.  An attachment map with
        only zero's fail.

        Raises:
            ValueError: If map doesn't pass check.
        """
        for map_name in self.get_map_names():
            map_object = self._setup.get_data_by_key_name('map', map_name)
            values = map_object.get_value()

            if all(v == 0 for v in values):
                raise ValueError('{} all 0s.  Check map.'.format(map_name))
