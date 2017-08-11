import maya.cmds as mc
import maya.mel as mm
import zBuilder.zMaya as mz

from zBuilder.nodes.base import BaseNode
import logging

logger = logging.getLogger(__name__)


class ZivaBaseNode(BaseNode):
    def __init__(self, *args, **kwargs):
        BaseNode.__init__(self, *args, **kwargs)

        self._map_list = list()

    # def set_map_list(self, map_list):
    #     self._map_list = map_list
    #
    # def get_map_list(self):
    #     return self._map_list

    def create(self, *args, **kwargs):
        """

        Returns:
            object:
        """

        logger.info('retrieving {}'.format(args))
        selection = mz.parse_args_for_selection(args)

        self.set_name(selection[0])
        self.set_type(mz.get_type(selection[0]))
        self.set_attr_list(mz.build_attr_list(selection[0]))
        self.populate_attrs(selection[0])
        self.set_mobject(selection[0])

        mesh = mz.get_association(selection[0])
        self.set_association(mesh)

        print 'getting maps', self._map_list

        for map_ in self._map_list:
            map_name = '{}.{}'.format(selection[0], map_)
            self.set_maps([map_name])

        # TODO  seriously?  Is returning self a good idea?  Probably not.
        return self
