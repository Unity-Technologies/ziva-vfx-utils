
from base import BaseNode

import re

class TetNode(BaseNode):
    def __init__(self):
        BaseNode.__init__(self)
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
            newName = replace_longname(search,replace,name)
            self.set_user_tet_mesh(newName)





def replace_longname(search,replace,longName):
    items = longName.split('|')
    newName = ''
    for i in items:
        if i:
            i = re.sub(search, replace,i)
            newName+='|'+i

    return newName