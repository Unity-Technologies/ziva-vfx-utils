import maya.cmds as mc
import maya.mel as mm
import zBuilder.zMaya as mz

from zBuilder.nodes.base import BaseNode
import logging

logger = logging.getLogger(__name__)


# TODO zivabase????  change name???
class ZivaBaseNode(BaseNode):
    MAP_LIST = []

    def __init__(self, *args, **kwargs):
        BaseNode.__init__(self, *args, **kwargs)

    def create(self, *args, **kwargs):
        """

        Returns:
            object:
        """

        #logger.info('retrieving {}'.format(args))
        selection = mz.parse_args_for_selection(args)

        self.set_name(selection[0])
        self.set_type(mz.get_type(selection[0]))
        self.set_attr_list(mz.build_attr_list(selection[0]))
        self.populate_attrs(selection[0])
        self.set_mobject(selection[0])

        mesh = mz.get_association(selection[0])
        self.set_association(mesh)

        # print 'getting maps', self._map_list

        # tmp = []
        # if self.get_map_list():
        #     for map_ in self.get_map_list():
        #         map_name = '{}.{}'.format(selection[0], map_)
        #         tmp.append(map_name)
        #     self.set_maps(tmp)
