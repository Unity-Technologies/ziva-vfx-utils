from zBuilder.nodes import Ziva
import maya.cmds as mc
import maya.mel as mm
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
        self.tissue_name = None

    def populate(self, maya_node=None):
        """ This populates the node given a selection.
        """
        super(RestShapeNode, self).populate(maya_node=maya_node)

        self.targets = mc.listConnections(self.name + '.target')
        self.targets = mc.ls(self.targets, long=True)  # find long names
        self.tissue_name = get_rest_shape_tissue(self.name)

    def build(self, *args, **kwargs):
        """ Builds the node in maya.
        """
        attr_filter = kwargs.get('attr_filter', list())

        # this is the mesh with zTissue that will have the zRestShape node
        mesh = self.association[0]

        # get a list of the short names of all the targets
        targets = [x.split('|')[-1] for x in self.targets]

        # Checking if the mesh is in scene
        if mc.objExists(mesh):
            # We know what mesh should have the zRestShape at this point so lets check if
            # there is an existing zRestShape on it.

            existing_restshape = mm.eval('zQuery -type zRestShape {}'.format(mesh))

            if not existing_restshape:
                # there is not a zRestShape so we need to create one
                mc.select(mesh)
                mc.select(targets, add=True)
                results = mm.eval('zRestShape -a')[0]
                self.mobject = results

                # Rename the zRestShape node based on the name of scene_item.
                # If this name is elsewhere in scene (on another mesh) it will not
                # be able to name it so we capture return and rename scene_item
                # so setAttrs work
                self.name = mc.rename(results, self.name)

                # Update name of tissue.  If a 'string_replace' was applied to scene_items
                # this could get out of sync so lets double check it.
                self.tissue_name = get_rest_shape_tissue(self.name)

        else:
            logger.warning(mesh + ' does not exist in scene, skipping zRestShape creation')

        self.set_maya_attrs(attr_filter=attr_filter)


def get_rest_shape_tissue(rest_shape):
    tissue = mm.eval('zQuery -type "zTissue" {}'.format(rest_shape))
    return tissue[0]
