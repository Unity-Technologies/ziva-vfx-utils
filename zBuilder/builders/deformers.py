from ..builder import Builder
from ..mayaUtils import parse_maya_node_for_selection, get_type
from ..commonUtils import time_this
from maya import cmds
import logging

logger = logging.getLogger(__name__)


class Deformers(Builder):
    """Test setup to play with deformers and how they are ordered on a mesh.
    """
    @time_this
    def retrieve_from_scene(self, *args, **kwargs):
        # parse args-----------------------------------------------------------
        selection = parse_maya_node_for_selection(args)

        acquire = ['deltaMush', 'zRelaxer', 'zWrap', 'zItto', 'zPolyCombine', 'blendShape', 'wrap']
        tmp = list()
        history = cmds.listHistory(selection, f=True)
        history.extend(cmds.listHistory(selection))
        history = list(set(history))[::-1]

        for hist in history:
            if get_type(hist) in acquire:
                tmp.append(hist)

        for item in tmp:
            parameter = self.node_factory(item)
            self.bundle.extend_scene_items(parameter)
        self.stats()

    @time_this
    def build(self, *args, **kwargs):
        logger.info('Applying....')
        attr_filter = kwargs.get('attr_filter', None)
        interp_maps = kwargs.get('interp_maps', 'auto')
        name_filter = kwargs.get('name_filter', list())
        acquire = ['deltaMush', 'zRelaxer', 'zWrap', 'zItto', 'zPolyCombine', 'blendShape', 'wrap']

        for scene_item in self.get_scene_items(name_filter=name_filter, type_filter=acquire):
            scene_item.build(attr_filter=attr_filter, interp_maps=interp_maps)
