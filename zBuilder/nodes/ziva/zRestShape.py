from zBuilder.nodes import Ziva
from maya import cmds
from maya import mel
import zBuilder.zMaya as mz
import logging

logger = logging.getLogger(__name__)


class RestShapeNode(Ziva):
    """ This node for storing information related to zRestShape.
    """
    type = 'zRestShape'
    """ The type of node. """

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
        tissue_name = get_rest_shape_tissue(self.name)
        self.tissue_item = self.builder.get_scene_items(name_filter=tissue_name)[0]

    def build(self, *args, **kwargs):
        """ Builds the node in maya.
        """
        attr_filter = kwargs.get('attr_filter', list())

        # this is the mesh with zTissue that will have the zRestShape node
        mesh = self.nice_association[0]

        # Checking if the mesh is in scene
        if cmds.objExists(mesh):
            # We know what mesh should have the zRestShape at this point so lets check if
            # there is an existing zRestShape on it.

            existing_restshape_node = mel.eval('zQuery -type zRestShape {}'.format(mesh))

            targets = []
            for target in self.targets:
                if cmds.objExists(target):
                    targets.append(target)
                elif cmds.objExists(target.split("|")[-1]):
                    targets.append(target.split("|")[-1])

            if not existing_restshape_node:
                # there is not a zRestShape so we need to create one
                cmds.select(mesh)
                cmds.select(targets, add=True)
                results = mel.eval('zRestShape -a')[0]

                # Rename the zRestShape node based on the name of scene_item.
                # If this name is elsewhere in scene (on another mesh) it will not
                # be able to name it so we capture return and rename scene_item
                # so setAttrs work
                self.name = mz.safe_rename(results, self.name)

            else:
                # The rest shape node exists on mesh so now lets update it.
                # First lets remove existing targets
                for target in targets:
                    mel.eval('zRestShape -r {} {};'.format(mesh, target))

                for target in self.targets:
                    # now lets add back what is in self
                    mel.eval('zRestShape -a {} {};'.format(mesh, target))

                # update name of node to that which is on mesh.
                self.name = existing_restshape_node[0]

        else:
            logger.warning(mesh + ' does not exist in scene, skipping zRestShape creation')

        self.set_maya_attrs(attr_filter=attr_filter)


def get_rest_shape_tissue(rest_shape):
    tissue = mel.eval('zQuery -type "zTissue" {}'.format(rest_shape))
    return tissue[0]
