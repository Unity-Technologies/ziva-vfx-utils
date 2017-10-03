from zBuilder.nodes import ZivaBaseNode
import maya.cmds as mc
import maya.mel as mm
import zBuilder.zMaya as mz
import logging

logger = logging.getLogger(__name__)


class EmbedderNode(ZivaBaseNode):
    TYPE = 'zEmbedder'

    def __init__(self, *args, **kwargs):
        self.__embedded_meshes = None
        self.__collision_meshes = None

        ZivaBaseNode.__init__(self, *args, **kwargs)

    def populate(self, *args, **kwargs):
        super(EmbedderNode, self).populate(*args, **kwargs)

        embedded_meshes = get_embedded_meshes([self.get_scene_name()])
        self.set_embedded_meshes(embedded_meshes[0])
        self.set_collision_meshes(embedded_meshes[1])

    def set_collision_meshes(self, meshes):
        self.__collision_meshes = meshes

    def set_embedded_meshes(self, meshes):
        self.__embedded_meshes = meshes

    def get_collision_meshes(self, long_name=False):
        if long_name:
            return self.__collision_meshes
        else:
            tmp = {}
            msh = []
            for name in self.__collision_meshes:
                for item in self.__collision_meshes[name]:
                    msh.append(item.split('|')[-1])
                tmp[name.split('|')[-1]] = msh
            return tmp

    def get_embedded_meshes(self, long_name=False):
        if long_name:
            return self.__embedded_meshes
        else:
            tmp = {}
            msh = []
            for name in self.__embedded_meshes:
                for item in self.__embedded_meshes[name]:
                    msh.append(item.split('|')[-1])
                tmp[name.split('|')[-1]] = msh
            return tmp

    def apply(self, *args, **kwargs):
        # logger.info('applying embedder')

        name = self.get_scene_name()
        collision_meshes = self.get_collision_meshes()
        embedded_meshes = self.get_embedded_meshes()

        # if collision_meshes:
        #     for mesh in collision_meshes:
        #         for item in collision_meshes[mesh]:
        #             mc.select(mesh, item, r=True)
        #             mm.eval('ziva -tcm')
        #
        # if embedded_meshes:
        #     for mesh in embedded_meshes:
        #         for item in embedded_meshes[mesh]:
        #             mc.select(mesh, item, r=True)
        #             mm.eval('ziva -e')


def get_embedded_meshes(bodies):
    collision_meshes = {}
    embedded_meshes = {}
    for body in bodies:
        col_mesh = mm.eval('zQuery -cm -l ' + body)
        em_mesh = mm.eval('zQuery -em -l ' + body)
        if em_mesh and col_mesh:
            em_mesh = list(set(set(em_mesh) - set(col_mesh)))
            if em_mesh == []:
                em_mesh = None

        if em_mesh:
            embedded_meshes[body] = em_mesh
        if col_mesh:
            collision_meshes[body] = col_mesh

    return embedded_meshes, collision_meshes
