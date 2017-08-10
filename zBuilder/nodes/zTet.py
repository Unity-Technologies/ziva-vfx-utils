from zBuilder.nodes.base import BaseNode
import zBuilder.zMaya as mz
import logging

logger = logging.getLogger(__name__)


class TetNode(BaseNode):
    def __init__(self, *args, **kwargs):
        BaseNode.__init__(self, *args, **kwargs)

        self._user_tet_mesh = None
        self._map_list = ['weightList[0].weights']

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

    # TODO a way to print everything without having to override
    # TODO print __dict__ or some variation
    # def print_(self):
    #     super(TetNode, self).print_()
    #     if self.get_user_tet_mesh(long_name=True):
    #         print 'User_Tet_Mesh: ', self.get_user_tet_mesh(long_name=True)

    def string_replace(self, search, replace):
        # TODO a way to manage string_replace without having to override.
        # TODO define attrs that need to be searched?
        super(TetNode, self).string_replace(search, replace)

        # name replace----------------------------------------------------------
        name = self.get_user_tet_mesh(long_name=True)
        if name:
            new_name = mz.replace_long_name(search, replace, name)
            self.set_user_tet_mesh(new_name)

    # TODO consistency with data classes.  use create() instead of retrieve()??
    def retrieve_from_scene(self, *args, **kwargs):
        """

        Returns:
            object:
        """
        # TODO better place to put _map_list
        self._map_list = ['weightList[0].weights']

        logger.info('retrieving {}'.format(args))
        selection = mz.parse_args_for_selection(args)

        self.set_name(selection[0])
        self.set_type(mz.get_type(selection[0]))
        self.set_attr_list(mz.build_attr_list(selection[0]))
        self.populate_attrs(selection[0])
        self.set_mobject(selection[0])

        # TODO user tet mesh
        mesh = mz.get_association(selection[0])
        self.set_association(mesh)

        # if get_maps:
        map_name = '{}.{}'.format(selection[0], self._map_list[0])
        self.set_maps([map_name])

