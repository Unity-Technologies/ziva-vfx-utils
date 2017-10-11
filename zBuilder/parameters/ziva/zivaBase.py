import zBuilder.zMaya as mz
import maya.cmds as mc
import maya.mel as mm

from zBuilder.parameters.base import BaseParameter
import logging

logger = logging.getLogger(__name__)


class ZivaBaseParameter(BaseParameter):
    """Base node for Ziva type nodes.

    extended from base to deal with maps and meshes and storing the solver.
    """
    EXTEND_ATTR_LIST = list()

    def __init__(self, *args, **kwargs):
        self.solver = None

        BaseParameter.__init__(self, *args, **kwargs)

    def build(self, *args, **kwargs):
        """

        Args:
            *args:
            **kwargs:

        Raises:
            NotImplementedError: if not implemented

        """
        raise NotImplementedError

    def populate(self, *args, **kwargs):
        """ This populates the node given a selection.

        Args:
            *args: Maya node to populate with.
        """
        super(ZivaBaseParameter, self).populate(*args, **kwargs)

        selection = mz.parse_args_for_selection(args)

        mesh = mz.get_association(selection[0])
        self.association = mesh

        solver = mm.eval('zQuery -t zSolver {}'.format(self.name))
        if solver:
            self.solver = solver[0]

        # get map component data------------------------------------------------
        mesh_names = self.get_map_meshes()
        map_names = self.get_map_names()

        if map_names and mesh_names:
            for map_name, mesh_name in zip(map_names, mesh_names):
                map_data_object = self._setup.component_factory(map_name,
                                                                mesh_name,
                                                                type='map')
                self._setup.add_component(map_data_object)

                if not self._setup.get_components(type_filter='mesh',
                                                 name_filter=mesh_name):
                    mesh_data_object = self._setup.component_factory(mesh_name,
                                                                     type='mesh'
                                                                    )
                    self._setup.add_component(mesh_data_object)

    # @property
    # def solver(self):
    #     """ :obj:`str`: The solver name this node used.
    #
    #     Used for allowing multiple solvers in scene and building a setup on one
    #     of them.
    #     """
    #     return self._solver
    #
    # @solver.setter
    # def solver(self, value):
    #     self._solver = value
