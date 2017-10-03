import zBuilder.zMaya as mz
import maya.cmds as mc
import maya.mel as mm

from zBuilder.nodes.base import BaseNode
import logging

logger = logging.getLogger(__name__)


class ZivaBaseNode(BaseNode):
    EXTEND_ATTR_LIST = list()

    def __init__(self, *args, **kwargs):
        self._solver = None

        BaseNode.__init__(self, *args, **kwargs)

    def apply(self, *args, **kwargs):
        pass

    def populate(self, *args, **kwargs):
        super(ZivaBaseNode, self).populate(*args, **kwargs)
        """

        Returns:
            object:
        """
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
                self._setup.add_data(map_data_object)

                if not self._setup.get_data(type_filter='mesh',
                                            name_filter=mesh_name):
                    mesh_data_object = self._setup.component_factory(mesh_name,
                                                                     type='mesh'
                                                                    )
                    self._setup.add_data(mesh_data_object)

    @property
    def solver(self):
        return self._solver

    @solver.setter
    def solver(self, value):
        self._solver = value
