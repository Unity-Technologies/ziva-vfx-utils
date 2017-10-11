from zBuilder.parameters import ZivaBaseParameter
import maya.cmds as mc
import maya.mel as mm
import zBuilder.zMaya as mz
import logging

logger = logging.getLogger(__name__)


class EmbedderNode(ZivaBaseParameter):
    """ This node for storing information related to zEmebedder.
    """
    type = 'zEmbedder'
    """ The type of node. """

    def __init__(self, *args, **kwargs):
        self.__embedded_meshes = None
        self.__collision_meshes = None

        ZivaBaseParameter.__init__(self, *args, **kwargs)

    def populate(self, *args, **kwargs):
        """ This extends ZivaBase.populate()

        Adds collision mesh and embedded mesh storage.

        Args:
            *args: Maya node to populate with.
        """
        super(EmbedderNode, self).populate(*args, **kwargs)

        embedded_meshes = get_embedded_meshes([self.get_scene_name()])
        self.set_embedded_meshes(embedded_meshes[0])
        self.set_collision_meshes(embedded_meshes[1])

    def set_collision_meshes(self, meshes):
        """ Sets the collision meshes.

        Args:
            meshes (list): The meshes to set.
        """
        self.__collision_meshes = meshes

    def set_embedded_meshes(self, meshes):
        """ Sets the embedded meshes.

        Args:
            meshes (list): The meshes to set.
        """
        self.__embedded_meshes = meshes

    def get_collision_meshes(self, long_name=False):
        """ Gets the collision meshes stored.
        Args:
            long_name (bool): Returns long name or short.  Default ``False``

        Returns:
            str: String of collision mesh name.
        """
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
        """ Gets the embedded meshes stored.
        Args:
            long_name (bool): Returns long name or short.  Default ``False``

        Returns:
            str: String of embedded mesh name.
        """
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
        """ Builds the zEmbedder in maya scene.

        Args:
            attr_filter (dict):  Attribute filter on what attributes to get.
                dictionary is key value where key is node type and value is
                list of attributes to use.

                tmp = {'zSolver':['substeps']}
            permissive (bool): Pass on errors. Defaults to ``True``
        """

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
    """ Returns embedded meshes for given body.
    Args:
        bodies: Maya mesh to find embedded meshes with.

    Returns:
        2 dict: of embedded meshes and collision meshes.
    """
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
