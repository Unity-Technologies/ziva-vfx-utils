import logging

from maya import cmds
from zBuilder.utils.commonUtils import time_this
from .builder import Builder

logger = logging.getLogger(__name__)


class Deformers(Builder):
    """ Builder to help serialize and manipulate Maya deformers.
    """

    def __init__(self, *args, **kwargs):
        super(Deformers, self).__init__(*args, **kwargs)

        # Deformers that this builder supports.
        self.deformers = ['deltaMush', 'blendShape', 'wrap', 'skinCluster']

    @time_this
    def retrieve_from_scene(self, deformers=None):
        """
        This retrieves the deformers from the selected meshes.  Supported types are skinCluster,
        deltaMush, wrap and blendShape.  By default it will retrieve all of them.

        Args:
            deformers (list): List of supported deformers to retrieve from scene. 
                    Defaults to `None` which in turn gets all supported deformers.
        """

        if deformers:
            self.deformers = list(set(self.deformers).intersection(deformers))
        else:
            deformers = self.deformers
        logger.info('getting deformers.....' + str(self.deformers))

        not_supported = list(set(deformers).difference(set(self.deformers)))
        if not_supported:
            for x in not_supported:
                logger.info('node type not supported: ' + str(x))

        # I have tried many variation of listHistory command and the way I found works is to
        # get the list with default arguments and reverse it.  Setting future to true will
        # return list in proper order but will end up analysing almost everything and hang maya
        # on large scenes.  Slicing the output of the listHistory seems to be fastest way.
        selection = cmds.ls(sl=True, l=True)
        for hist in cmds.listHistory(selection)[::-1]:
            if cmds.objectType(hist) in self.deformers:
                parameter = self.node_factory(hist)
                self._extend_scene_items(parameter)
                for parm in parameter:
                    if parm.type in ['mesh', 'map']:
                        parm.retrieve_values()
        self.stats()

    @time_this
    def build(self, interp_maps='auto'):
        """
        This builds the deformers into the scene.

        Args:
            interp_maps (str): Option to interpolate maps.
                True: Yes interpolate
                False: No
                auto: Interpolate if it needs it (vert check)
        """

        for scene_item in self.get_scene_items(type_filter=self.deformers):
            logger.info('Building: {}'.format(scene_item.name))
            scene_item.do_build(interp_maps=interp_maps)
