from zBuilder.nodes import Ziva
import zBuilder.zMaya as mz
import logging
import maya.cmds as mc
import maya.mel as mm

logger = logging.getLogger(__name__)


class TetNode(Ziva):
    """ This node for storing information related to zTets.
    """
    type = 'zTet'
    """ The type of node. """

    MAP_LIST = ['weightList[0].weights']
    """ List of maps to store. """

    def __init__(self, *args, **kwargs):
        self._user_tet_mesh = None

        Ziva.__init__(self, *args, **kwargs)

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
            try:
                mc.connectAttr(str(self.get_user_tet_mesh()) + '.worldMesh',
                               self.get_scene_name() + '.iTet', f=True)
            except:
                user_mesh = str(self.get_user_tet_mesh())
                name = self.get_scene_name()
                # TODO permissive check
                print 'could not connect {}.worldMesh to {}.iTet'.format(
                    user_mesh, name)

    def build(self, *args, **kwargs):
        """ Builds the zTets in maya scene.

        These get built after the tissues so it is assumed they are in scene.
        This just checks what tet is associated with mesh and uses that one,
        renames it and stores mObject then changes attributes.
        There is only ever 1 per mesh so no need to worry about multiple tets

        Args:
            attr_filter (dict):  Attribute filter on what attributes to get.
                dictionary is key value where key is node type and value is
                list of attributes to use.

                tmp = {'zSolver':['substeps']}
            interp_maps (str): Interpolating maps.  Defaults to ``auto``
            permissive (bool): Pass on errors. Defaults to ``True``
        """

        attr_filter = kwargs.get('attr_filter', list())
        permissive = kwargs.get('permissive', True)
        interp_maps = kwargs.get('interp_maps', 'auto')

        #name = self.get_scene_name()
        name = self.name
        if not mc.objExists(name):
            mesh = self.association[0]
            if mc.objExists(mesh):
                if permissive:
                    name = mm.eval('zQuery -t zTet ' + mesh)[0]
                else:
                    raise StandardError('{} does not exist in scene.  Check meshes.'.format(mesh))

        if name:
            if not mc.objExists(name):
                if permissive:
                    logger.info('{} doesnt exist in scene.  Permissive set to True, skipping tet creation'.format(mesh))
            else:
                new_name = mc.rename(name, self.name)
                self.mobject = new_name

        self.apply_user_tet_mesh()
        self.set_maya_attrs(attr_filter=attr_filter)
        self.set_maya_weights(interp_maps=interp_maps)

