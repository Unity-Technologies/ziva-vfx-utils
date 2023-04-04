import logging
import re

from maya import cmds
from zBuilder.utils.mayaUtils import safe_rename, get_short_name, build_attr_key_values
from .zivaBase import Ziva

logger = logging.getLogger(__name__)


class RestShapeNode(Ziva):
    """ This node for storing information related to zRestShape.
    """
    type = 'zRestShape'

    def __init__(self, parent=None, builder=None):
        super(RestShapeNode, self).__init__(parent=parent, builder=builder)
        self.targets = []
        self.tissue_item = None

    def populate(self, maya_node=None):
        """ This populates the node given a selection.
        """
        super(RestShapeNode, self).populate(maya_node=maya_node)

        self.targets = cmds.listConnections(self.name + '.target')
        self.targets = cmds.ls(self.targets, long=True)  # find long names
        tissue_name = cmds.zQuery(self.name, type="zTissue")[0]
        self.tissue_item = self.builder.get_scene_items(name_filter=tissue_name)[0]

        # we need to add the zRestShape targets to the attr_list.
        # These are the aliased attrs in channel box for zBuilder to store.
        # We need to get short name
        attr_list = [x.split('|')[-1] for x in self.targets]
        attrs = build_attr_key_values(self.name, attr_list)
        self.attrs.update(attrs)

    def do_build(self, *args, **kwargs):
        """ Builds the node in maya.
        """

        # this is the mesh with zTissue that will have the zRestShape node
        mesh = self.nice_association[0]

        # Checking if the mesh is in scene
        if cmds.objExists(mesh):
            # We know what mesh should have the zRestShape at this point so lets check if
            # there is an existing zRestShape on it.

            existing_restshape_node = cmds.zQuery(mesh, type='zRestShape')

            targets = []
            for target in self.targets:
                if cmds.objExists(target):
                    targets.append(target)
                elif cmds.objExists(get_short_name(target)):
                    targets.append(get_short_name(target))

            if not existing_restshape_node:
                # there is not a zRestShape so we need to create one
                cmds.select(mesh)
                cmds.select(targets, add=True)
                results = cmds.zRestShape(a=True)[0]
                # Rename the zRestShape node based on the name of scene_item.
                # If this name is elsewhere in scene (on another mesh) it will not
                # be able to name it so we capture return and rename scene_item
                # so setAttrs work
                self.name = safe_rename(results, self.name)
            else:
                # The rest shape node exists on mesh so now lets update it.
                # First lets remove existing targets
                for target in targets:
                    cmds.zRestShape(mesh, target, r=True)
                # now lets add back what is in self
                for target in self.targets:
                    cmds.zRestShape(mesh, target, a=True)
                # update name of node to that which is on mesh.
                self.name = existing_restshape_node[0]
        else:
            logger.warning(mesh + ' does not exist in scene, skipping zRestShape creation')

        self.set_maya_attrs()

    def string_replace(self, search, replace):
        """ Here we are searching through the stored attributes with the intent of performing a string replace
        on attribute names if it is an aliased attribute.  Aliased attributes are used in blendShape's and our own 
        zRestShape.

        This implementation is the same as the one used in blendShape.  When updating this, please update the that 
        one as well.
        """
        super(RestShapeNode, self).string_replace(search=search, replace=replace)

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
