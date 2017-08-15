from zBuilder.nodes import ZivaBaseNode
import zBuilder.zMaya as mz
import logging

logger = logging.getLogger(__name__)


class TetNode(ZivaBaseNode):
    TYPE = 'zTet'
    MAP_LIST = ['weightList[0].weights']

    def __init__(self, *args, **kwargs):
        ZivaBaseNode.__init__(self, *args, **kwargs)

        self._user_tet_mesh = None

    def set_user_tet_mesh(self, mesh):
        self._user_tet_mesh = mesh

    def get_user_tet_mesh(self, long_name=False):
        if self._user_tet_mesh:
            if long_name:
                return self._user_tet_mesh
            else:
                return self._user_tet_mesh.split('|')[-1]
        else:
            return None

    def string_replace(self, search, replace):
        # TODO a way to manage string_replace without having to override.
        # TODO define attrs that need to be searched?
        super(TetNode, self).string_replace(search, replace)

        # name replace----------------------------------------------------------
        name = self.get_user_tet_mesh(long_name=True)
        if name:
            new_name = mz.replace_long_name(search, replace, name)
            self.set_user_tet_mesh(new_name)

