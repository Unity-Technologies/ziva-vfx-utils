import logging
from maya import cmds
from maya import mel

from zBuilder.nodes.deformer import Deformer

logger = logging.getLogger(__name__)


class Wrap(Deformer):
    type = 'wrap'

    # MAP_LIST = ['weightList[0].weights']

    def build(self, *args, **kwargs):
        # interp_maps = kwargs.get('interp_maps', 'auto')
        attr_filter = kwargs.get('attr_filter', None)

        name = self.get_scene_name()
        if not cmds.objExists(name):
            cmds.select(self.nice_association, r=True)
            version = 7
            operation = 1  # create
            threshold = 0
            maxDist = 1
            inflType = 2  # 1, poitn 2 face
            exclusiveBind = 1  # bind algorythem(1-smooth,2-exclusive)
            autoWeightThreshold = 1
            renderInfl = 0  # render influence objects
            fallOffMode = 0  # distanceFalloff alg

            cmd = ('doWrapArgList "{}" {}"{}", "{}", "{}", "{}", "{}", "{}", "{}", "{}"{}').format(
                version, '{', operation, threshold, maxDist, inflType, exclusiveBind,
                autoWeightThreshold, renderInfl, fallOffMode, '}')

            results = mel.eval(cmd)
            cmds.rename(results[0], self.name)

        self.set_maya_attrs(attr_filter=attr_filter)
        # self.set_maya_weights(interp_maps=interp_maps)

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
        #output_geometry = cmds.listConnections('{}.outputGeometry'.format(node))

        out = list()
        out.extend(output_geometry)
        out.extend(driver_points)
        print('FYUFSF', node, out)
        return out
