from zBuilder.nodes import ZivaBaseNode
import zBuilder.zMaya as mz
import logging
import maya.cmds as mc
import maya.mel as mm

logger = logging.getLogger(__name__)


class TetNode(ZivaBaseNode):
    TYPE = 'zTet'
    MAP_LIST = ['weightList[0].weights']

    def __init__(self, *args, **kwargs):
        self._user_tet_mesh = None

        ZivaBaseNode.__init__(self, *args, **kwargs)

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

    def apply_user_tet_mesh(self):
        """
        Applies the user tet mesh if any.
        """
        if self.get_user_tet_mesh():
            try:
                mc.connectAttr(str(self.get_user_tet_mesh()) + '.worldMesh',
                               self.get_scene_name() + '.iTet', f=True)
            except:
                user_mesh = str(self.get_user_tet_mesh())
                name = self.get_scene_name()

                print 'could not connect {}.worldMesh to {}.iTet'.format(
                    user_mesh, name)

    def apply(self, *args, **kwargs):
        """
        These get built after the tissues so it is assumed they are in scene.
        This just checks what tet is associated with mesh and uses that one,
        renames it and stores mObject then changes attributes.
        There is only ever 1 per mesh so no need to worry about multiple tets

        Args:
            *args:
            **kwargs:

        Returns:

        """
        permissive = kwargs.get('permissive', True)
        interp_maps = kwargs.get('interp_maps', 'auto')
        attr_filter = kwargs.get('attr_filter', None)

        name = self.get_scene_name()
        if not mc.objExists(name):
            mesh = self.get_association()[0]
            if mc.objExists(mesh):
                if permissive:
                    name = mm.eval('zQuery -t zTet ' + mesh)[0]
                else:
                    raise StandardError('{} does not exist in scene.  Check meshes.'.format(mesh))
        if name:
            new_name = mc.rename(name, self.get_name())
            self.set_mobject(new_name)

        self.apply_user_tet_mesh()
        self.set_maya_attrs(attr_filter=attr_filter)
        self.set_maya_weights(interp_maps=interp_maps)

