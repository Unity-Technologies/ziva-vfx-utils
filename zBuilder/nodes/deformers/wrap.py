import logging

from maya import cmds
from maya import mel
from zBuilder.nodes.deformer import Deformer

logger = logging.getLogger(__name__)


class Wrap(Deformer):
    type = 'wrap'

    def populate(self, maya_node=None):
        """ This extends Deformer.populate().
        Args:
            maya_node: Maya node to populate with.
        """
        super(Wrap, self).populate(maya_node=maya_node)
        self.association = self.get_meshes(self.name)

    def do_build(self, *args, **kwargs):

        if all([cmds.objExists(x) for x in self.association]):
            if not cmds.objExists(self.name):
                cmds.select(self.nice_association, replace=True)

                version = 7  # internal maya
                operation = 1  # create mode
                threshold = self.attrs['weightThreshold']['value']
                maxDist = self.attrs['maxDistance']['value']
                inflType = 2  # 1, point 2 face
                exclusiveBind = self.attrs['exclusiveBind']['value']
                autoWeightThreshold = self.attrs['autoWeightThreshold']['value']
                renderInfl = 0  # render influence objects
                fallOffMode = self.attrs['falloffMode']['value']

                cmd = (
                    'doWrapArgList "{}" {}"{}", "{}", "{}", "{}", "{}", "{}", "{}", "{}"{}').format(
                        version, '{', operation, threshold, maxDist, inflType, exclusiveBind,
                        autoWeightThreshold, renderInfl, fallOffMode, '}')

                results = mel.eval(cmd)
                cmds.rename(results[0], self.name)

            self.set_maya_attrs()
        else:
            for item in self.association:
                if not cmds.objExists(item):
                    logger.warning(
                        'Missing items from scene: check for existence of {}'.format(item))

    @staticmethod
    def get_meshes(node):
        """ Queries the deformer and returns the meshes associated with it.
        Args:
            node: Maya node to query.
        Returns:
            list od strings: list of strings of mesh names.
        """
        driver_points = cmds.listConnections('{}.driverPoints'.format(node))
        output_geometry = cmds.listConnections('{}.geomMatrix'.format(node))

        out = list()
        out.extend(output_geometry)
        out.extend(driver_points)
        return out