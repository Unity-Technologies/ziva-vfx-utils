from maya import cmds
from maya import mel
from zBuilder.utils.mayaUtils import get_short_name, safe_rename
from .zivaBase import Ziva


class EmbedderNode(Ziva):
    """ This node for storing information related to zEmebedder.
    """
    type = 'zEmbedder'

    def __init__(self, parent=None, builder=None):
        super(EmbedderNode, self).__init__(parent=parent, builder=builder)
        self.__embedded_meshes = None
        self.__collision_meshes = None

    def populate(self, maya_node=None):
        """ This populates the node given a selection.

        Args:
            maya_node: Maya node to populate with.
        """
        super(EmbedderNode, self).populate(maya_node=maya_node)

        tissues = self.builder.get_scene_items(type_filter='zTissue')
        tissue_meshes = [x.nice_association[0] for x in tissues]
        embedded_meshes = get_embedded_meshes(tissue_meshes)

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
                    msh.append(get_short_name(item))
                tmp[get_short_name(name)] = msh
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
                    msh.append(get_short_name(item))
                tmp[get_short_name(name)] = msh
            return tmp

    def do_build(self, *args, **kwargs):
        """ Builds the zEmbedder in maya scene.

        Args:
            permissive (bool): Pass on errors. Defaults to ``True``
        """

        # If the embedder as named, does not exist in scene lets find correct name
        # based on stored solver then rename it to what is in builder.
        if not cmds.objExists(self.name):
            found_name = mel.eval('zQuery -t zEmbedder {}'.format(self.solver.name))
            self.name = safe_rename(found_name[0], self.name)

        collision_meshes = self.get_collision_meshes(long_name=True)
        embedded_meshes = self.get_embedded_meshes(long_name=True)

        if collision_meshes:
            for mesh in collision_meshes:
                for item in collision_meshes[mesh]:
                    if not cmds.objExists(item):
                        item = get_short_name(item)
                    history = cmds.listHistory(item)
                    if not cmds.ls(history, type='zEmbedder'):
                        if not cmds.objExists(mesh):
                            mesh = get_short_name(mesh)
                        cmds.select(mesh, item, r=True)
                        mel.eval('ziva -tcm')

        if embedded_meshes:
            for mesh in embedded_meshes:
                for item in embedded_meshes[mesh]:
                    if not cmds.objExists(item):
                        item = get_short_name(item)
                    history = cmds.listHistory(item)
                    if not cmds.ls(history, type='zEmbedder'):
                        if not cmds.objExists(mesh):
                            mesh = get_short_name(mesh)
                        cmds.select(mesh, item, r=True)
                        mel.eval('ziva -e')


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
        col_mesh = mel.eval('zQuery -cm -l ' + body)
        em_mesh = mel.eval('zQuery -em -l ' + body)
        if em_mesh and col_mesh:
            em_mesh = list(set(set(em_mesh) - set(col_mesh)))
            if em_mesh == []:
                em_mesh = None

        if em_mesh:
            embedded_meshes[body] = em_mesh
        if col_mesh:
            collision_meshes[body] = col_mesh

    return embedded_meshes, collision_meshes
