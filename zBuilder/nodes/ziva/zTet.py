from zBuilder.nodes import Ziva
import zBuilder.zMaya as mz
import logging
from maya import cmds
from maya import mel

logger = logging.getLogger(__name__)


class TetNode(Ziva):
    """ This node for storing information related to zTets.
    """
    type = 'zTet'
    """ The type of node. """

    MAP_LIST = ['weightList[0].weights']
    """ List of maps to store. """

    def __init__(self, parent=None, builder=None):
        super(TetNode, self).__init__(parent=parent, builder=builder)
        self._user_tet_mesh = None

    def set_user_tet_mesh(self, mesh):
        """ Setting of the user tet mesh.
        Args:
            mesh (str): A maya mesh.
        """
        self._user_tet_mesh = mesh

    def get_user_tet_mesh(self, long_name=False):
        """ Get user tet mesh.
        Args:
            long_name: return long name or not.  Defaults to ``False``

        Returns:
            str: String of user tet mesh name.

        """
        if self._user_tet_mesh:
            if long_name:
                return self._user_tet_mesh
            else:
                return self._user_tet_mesh.split('|')[-1]
        else:
            return None

    def apply_user_tet_mesh(self):
        """ Applies the user tet mesh if any.
        """
        if self.get_user_tet_mesh():
            name = self.get_scene_name()
            try:
                cmds.connectAttr(str(self.get_user_tet_mesh()) + '.worldMesh',
                                 name + '.iTet',
                                 f=True)
            except:
                user_mesh = str(self.get_user_tet_mesh())
                # TODO permissive check
                print('could not connect {}.worldMesh to {}.iTet'.format(user_mesh, name))

    def build(self, *args, **kwargs):
        """ Builds the zTets in maya scene.

        These get built after the tissues so it is assumed they are in scene.
        This just checks what tet is associated with mesh and uses that one,
        renames it and then changes attributes.
        There is only ever 1 per mesh so no need to worry about multiple tets

        Args:
            permissive (bool): Pass on errors. Defaults to ``True``
        """

        permissive = kwargs.get('permissive', True)

        name = self.name
        if not cmds.objExists(name):
            mesh = self.nice_association[0]
            if cmds.objExists(mesh):
                if permissive:
                    name = mel.eval('zQuery -t zTet ' + mesh)
                    if name:
                        name = name[0]
                else:
                    raise Exception('{} does not exist in scene. Check mesh {}.'.format(name, mesh))

        if name:
            if not cmds.objExists(name):
                if permissive:
                    logger.info(
                        '{} doesnt exist in scene.  Permissive set to True, skipping tet creation'.
                        format(mesh))
            else:
                self.name = mz.safe_rename(name, self.name)

        self.apply_user_tet_mesh()
        # zTet does not need to build maps and attributes here because it's done by zTissue
