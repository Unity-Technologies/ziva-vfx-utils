import maya.cmds as mc
import maya.mel as mm
import zBuilder.zMaya as mz
from zBuilder.data import BaseComponent
import logging

logger = logging.getLogger(__name__)


class Map(BaseComponent):
    TYPE = 'map'

    def __init__(self, *args, **kwargs):
        BaseComponent.__init__(self, *args, **kwargs)
        self._class = (self.__class__.__module__, self.__class__.__name__)

        self._name = None
        self._mesh = None
        self._value = None


        if args:
            map_name = args[0]
            mesh_name = args[1]

            if map_name and mesh_name:
                self.populate(map_name, mesh_name)

    def __str__(self):
        name = self.get_name()
        if self.get_value():
            length = len(self.get_value())
        else:
            length = 'null'
        output = ''
        output += '< MAP: {} -- length: {} >'.format(name, length)
        return output

    def __repr__(self):
        return self.__str__()

    def populate(self, map_name, mesh_name):
        """

        Args:
            map_name:
            mesh_name:

        Returns:

        """
        weight_value = get_weights(map_name, mesh_name)

        self.set_name(map_name)
        self.set_mesh(mesh_name)
        self.set_type('map')
        self.set_value(weight_value)

    def set_mesh(self, mesh):
        self._mesh = mesh   

    def get_mesh(self, long_name=False):

        if self._mesh:
            if long_name:
                return self._mesh
            else:
                return self._mesh.split('|')[-1]
        else:
            return None

    def set_value(self, value):
        self._value = value

    def get_value(self):
        return self._value

    def string_replace(self, search, replace):
        # name replace----------------------------------------------------------
        name = self.get_name(long_name=True)
        newName = mz.replace_long_name(search, replace, name)
        self.set_name(newName)

        mesh = self.get_mesh(long_name=True)
        newMesh = mz.replace_long_name(search, replace, mesh)
        self.set_mesh(newMesh)


def get_weights(map_name, mesh_name):
    """

    Args:
        map_name:
        mesh_name:

    Returns:

    """
    vert_count = mc.polyEvaluate(mesh_name, v=True)
    try:
        value = mc.getAttr('{}[0:{}]'.format(map_name, vert_count - 1))
    except ValueError:
        value = mc.getAttr(map_name)
    return value

