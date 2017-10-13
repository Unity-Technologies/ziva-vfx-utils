import zBuilder.zMaya as mz
import maya.cmds as mc
import maya.mel as mm

from zBuilder.parameters.deformerBase import DeformerBaseParameter
import logging

logger = logging.getLogger(__name__)


class ZivaBaseParameter(DeformerBaseParameter):
    """Base node for Ziva type nodes.

    extended from base to deal with maps and meshes and storing the solver.
    """
    EXTEND_ATTR_LIST = list()

    def __init__(self, *args, **kwargs):
        self.solver = None

        DeformerBaseParameter.__init__(self, *args, **kwargs)

        if args:
            self.populate(args[0])

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

        selection = mz.parse_args_for_selection(args)

        self.name = selection[0]
        self.type = mc.objectType(selection[0])
        attr_list = mz.build_attr_list(selection[0])
        if self.EXTEND_ATTR_LIST:
            attr_list.extend(self.EXTEND_ATTR_LIST)
        attrs = mz.build_attr_key_values(selection[0], attr_list)
        self.attrs = attrs
        self.mobject = selection[0]

        mesh = mz.get_association(selection[0])
        self.association = mesh

        solver = mm.eval('zQuery -t zSolver {}'.format(self.name))
        if solver:
            self.solver = solver[0]

        mesh_names = self.get_map_meshes()
        map_names = self.get_map_names()

        # if map_names and mesh_names:
        #     for map_name, mesh_name in zip(map_names, mesh_names):
        #         # map_data_object = self._setup.component_factory(map_name,
        #         #                                                mesh_name,
        #         #                                                type='map')
        #         map_data_object = self._setup.parameter_factory([map_name,mesh_name],
        #                                             type_='map')
        #         # print map_name, mesh_name
        #         self._setup.bundle.add_parameter(map_data_object)

        # # get map component data------------------------------------------------
        # mesh_names = self.get_map_meshes()
        # map_names = self.get_map_names()
        #
        # if map_names and mesh_names:
        #     for map_name, mesh_name in zip(map_names, mesh_names):
        #         map_data_object = self._setup.component_factory(map_name,
        #                                                         mesh_name,
        #                                                         type='map')
        #         self._setup.bundle.add_component(map_data_object)
        #
        #         if not self._setup.bundle.get_components(type_filter='mesh',
        #                                          name_filter=mesh_name):
        #             mesh_data_object = self._setup.component_factory(mesh_name,
        #                                                              type='mesh'
        #                                                             )
        #             self._setup.bundle.add_component(mesh_data_object)

    @property
    def solver(self):
        """ :obj:`str`: The solver name this node used.

        Used for allowing multiple solvers in scene and building a setup on one
        of them.
        """
        return self._solver

    @solver.setter
    def solver(self, value):
        self._solver = value
