import re

from maya import cmds
from zBuilder.utils.mayaUtils import get_short_name, build_attr_key_values, construct_map_names
from zBuilder.nodes.deformer import Deformer
import logging

logger = logging.getLogger(__name__)


class BlendShape(Deformer):
    type = 'blendShape'
    MAP_LIST = ['inputTarget[0].inputTargetGroup[*].targetWeights', 'inputTarget[0].baseWeights']
    EXTEND_ATTR_LIST = ['origin', 'supportNegativeWeights']

    def __init__(self, parent=None, builder=None):
        super(BlendShape, self).__init__(parent=parent, builder=builder)
        self._target = None

    def spawn_parameters(self):
        """
        This outputs a dictionary formatted to feed to the parameter factory so
        the parameter factory knows what parameters to build.  The third value in maps 
        is either 'endPoints' or 'barycentric'.  endPoints is an interpolation method 
        exclusive for endPoint fiber maps.
        dict['map'] = [node_name_dot_attr, mesh_name, 'barycentric']
        dict['mesh'] = [mesh_name]
        """
        objs = {}
        if self.nice_association:
            objs['mesh'] = self.nice_association

        # The amount of maps for a blendShape depends on how many targets the blendshape has.
        # So we need to resolve the maps in MAP_LIST by adding node name and replace any * with
        # proper number.
        objs['map'] = []
        num_targets = len(cmds.blendShape(self.name, q=True, target=True))
        mesh_name = self.association[0]
        # append target weights
        for i in range(0, num_targets):
            map_name = '{}.inputTarget[0].inputTargetGroup[{}].targetWeights'.format(self.name, i)
            objs['map'].append([map_name, mesh_name, "barycentric"])
        # append base weights
        objs['map'].append(
            ["{}.inputTarget[0].baseWeights".format(self.name), mesh_name, "barycentric"])
        return objs

    def get_map_meshes(self):
        """
        This is the mesh associated with each map in obj.MAP_LIST.
        Typically it seems to coincide with mesh store in get_association.
        Sometimes it deviates, so you can override this method to define your own
        list of meshes against the map list.
        For blendShapes we don't know how many maps so we are generating this
        list based on length of maps.
        Returns:
            list(): of long mesh names.
        """
        return [self.association[0]] * (len(cmds.blendShape(self.name, q=True, target=True)) + 1)

    def do_build(self, *args, **kwargs):
        interp_maps = kwargs.get('interp_maps', 'auto')

        meshes = self.target
        meshes.append(self.association[0])

        if all([cmds.objExists(x) for x in meshes]):
            if not cmds.objExists(self.name):
                cmds.select(self.target, r=True)
                cmds.select(self.association, add=True)
                cmds.blendShape(name=self.name)

            self.set_maya_attrs()
            self.set_maya_weights(interp_maps=interp_maps)
        else:
            for mesh in meshes:
                if not cmds.objExists(mesh):
                    logger.warning(
                        'Missing items from scene: check for existence of {}'.format(mesh))

    def populate(self, maya_node=None):
        super(BlendShape, self).populate(maya_node=maya_node)
        self.target = get_target(self.name)

        # we need to add the blendShape targets to the attr_list.
        # These are the aliased attrs in channel box for zBuilder to store.
        # We need to remove any namespace here
        attr_list = [x.split(':')[-1] for x in self.target]

        attrs = build_attr_key_values(self.name, attr_list)
        self.attrs.update(attrs)

    @property
    def target(self):
        return [get_short_name(item) for item in self._target]

    @target.setter
    def target(self, target_mesh):
        self._target = cmds.ls(target_mesh, long=True)

    @property
    def long_target(self):
        return self._target

    def string_replace(self, search, replace):
        """ Here we are searching through the stored attributes with the intent of performing a string replace
        on attribute names if it is an aliased attribute.  Aliased attributes are used in blendShape's and our own 
        zRestShape.

        This implementation is the same as the one used in zRestShape.  When updating this, please update the that 
        one as well.
        """
        super(BlendShape, self).string_replace(search=search, replace=replace)

        # to find what attributes are aliased we check the attrs dictionary and see if the 'alias'
        # key is not an empty string.  Furthermore the value of this key will need a string replace on it as well
        tmp_dict = {}
        for item in self.attrs.keys():
            if self.attrs[item]['alias']:
                tmp_dict[item] = re.sub(search, replace, item)

        for item in tmp_dict.keys():
            new_item = tmp_dict[item]
            self.attrs[new_item] = self.attrs.pop(item)
            self.attrs[new_item]['alias'] = re.sub(search, replace, self.attrs[new_item]['alias'])


def get_target(blend_shape):
    target = cmds.blendShape(blend_shape, q=True, t=True)
    return target