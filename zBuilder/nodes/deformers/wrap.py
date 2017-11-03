import logging
import maya.cmds as mc
import maya.mel as mm

from zBuilder.nodes.deformer import Deformer

logger = logging.getLogger(__name__)


class Wrap(Deformer):
    type = 'wrap'
    # MAP_LIST = ['weightList[0].weights']

    def build(self, *args, **kwargs):
        # interp_maps = kwargs.get('interp_maps', 'auto')
        attr_filter = kwargs.get('attr_filter', None)

        name = self.get_scene_name()
        if not mc.objExists(name):
            mc.select(self.association, r=True)
            version = 7
            operation = 1 # create
            threshold = 0
            maxDist = 1
            inflType = 2 # 1, poitn 2 face
            exclusiveBind = 1 # bind algorythem(1-smooth,2-exclusive)
            autoWeightThreshold = 1
            renderInfl = 0 # render influence objects
            fallOffMode = 0 # distanceFalloff alg

            cmd = ('doWrapArgList "{}" {}"{}", "{}", "{}", "{}", "{}", "{}", "{}", "{}"{}').format(version, '{',operation, threshold, maxDist, inflType, exclusiveBind, autoWeightThreshold, renderInfl, fallOffMode,'}')

            results = mm.eval(cmd)
            print results

            # print cmd
            #self.mobject = delta_mush
        else:
            self.mobject = name

        self.set_maya_attrs(attr_filter=attr_filter)
        # self.set_maya_weights(interp_maps=interp_maps)

    # proc
    # string[]
    # createWrap(
    #     float $threshold, float $maxDistance, int $inflType, int $exclusiveBind, int $autoWeightThreshold, int $renderInfl, int $falloffMode)
    # //
    # doWrapArgList
    # "7"
    # {"1", "0", "1", "2", "0", "1", "0", "0"} //

    # def populate(self, *args, **kwargs):
    #     super(WrapNode, self).populate(*args, **kwargs)
    #
    #     # self.target = get_target(self.name)
    #     self.association = self.get_meshes(self.get_scene_name())
    #     print 'ddd'
    @staticmethod
    def get_meshes(node):
        """ Queries the deformer and returns the meshes associated with it.

        Args:
            node: Maya node to query.

        Returns:
            list od strings: list of strings of mesh names.
        """
        driver_points = mc.listConnections('{}.driverPoints'.format(node))
        output_geometry = mc.listConnections('{}.outputGeometry'.format(node))

        out = list()
        out.extend(output_geometry)
        out.extend(driver_points)
        return out
