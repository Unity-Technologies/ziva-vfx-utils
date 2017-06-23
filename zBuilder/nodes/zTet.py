import zBuilder.nodes.base as base

import re
import logging

logger = logging.getLogger(__name__)

class TetNode(base.BaseNode):
    def __init__(self):
        base.BaseNode.__init__(self)
        self._user_tet_mesh = None

    def set_user_tet_mesh(self,mesh):
        self._user_tet_mesh = mesh

    def get_user_tet_mesh(self,longName=False):
        if self._user_tet_mesh:
            if longName:
                return self._user_tet_mesh
            else:
                return self._user_tet_mesh.split('|')[-1]
        else:
            return None

    def print_(self):
        super(TetNode, self).print_()
        if self.get_user_tet_mesh(longName=True):
            print 'User_Tet_Mesh: ',self.get_user_tet_mesh(longName=True)

    def string_replace(self,search,replace):
        super(TetNode, self).string_replace(search,replace)

        # name replace----------------------------------------------------------
        name = self.get_user_tet_mesh(longName=True)
        if name:
            newName = base.replace_longname(search,replace,name)
            self.set_user_tet_mesh(newName)






