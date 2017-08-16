import logging

import maya.cmds as mc
import maya.mel as mm

import zBuilder.data as dta
import zBuilder.data.mesh as msh
import zBuilder.nodes as nds
from zBuilder.main import Builder

logger = logging.getLogger(__name__)


class ZivaSetup(Builder):
    """
    To capture a ziva setup
    """

    def __init__(self):
        Builder.__init__(self)

        for plugin in mc.pluginInfo(query=True, listPluginsPath=True):
            cmds = mc.pluginInfo(plugin, q=True, c=True)
            if cmds and 'ziva' in cmds:
                # self.info['plugin_name'] = plug
                # self.info['plugin_version'] = mc.pluginInfo(plug,
                #   q=True,v=True)
                plug = plugin.split('/')[-1]
                continue

    @Builder.time_this
    def retrieve_from_scene(self, *args, **kwargs):
        # ----------------------------------------------------------------------
        # KWARG PARSING---------------------------------------------------------
        # ----------------------------------------------------------------------
        get_mesh = kwargs.get('get_mesh', True)
        get_maps = kwargs.get('get_maps', True)

        map_names = []
        mesh_names = []

        # ----------------------------------------------------------------------
        # NODE STORING----------------------------------------------------------
        # ----------------------------------------------------------------------
        solver = mm.eval('zQuery -t "zSolver" {}'.format(args[0]))[0]

        b_solver = self.node_factory(solver)
        self.add_node(b_solver)

        node_types = ['zSolverTransform',
                      'zBone',
                      'zTet',
                      'zTissue',
                      'zCloth',
                      'zMaterial',
                      'zAttachment',
                      'zFiber',
                      'zEmbedder',
                      ]

        for node_type in node_types:
            nodes = mm.eval('zQuery -t "{}" {}'.format(node_type, solver))
            if nodes:
                for node in nodes:
                    b_node = self.node_factory(node)
                    #print b_node
                    self.add_node(b_node)

        if get_maps:
            self.store_maps()
            # self.component_factory('map')
        if get_mesh:
            self.store_mesh()



        self.stats()

    @Builder.time_this
    def apply(self, name_filter=None, attr_filter=None, interp_maps='auto',
              solver=True, bones=True, tissues=True, attachments=True,
              materials=True, fibers=True, embedder=True, cloth=True,
              lineOfActions=True, mirror=False, permisive=True):

        """
        Args:
            attr_filter (dict):  Attribute filter on what attributes to get. 
                dictionary is key value where key is node type and value is 
                list of attributes to use.

                tmp = {'zSolver':['substeps']}
            name_filter (str): filter by node name.  Defaults to **None**
        """

        sel = mc.ls(sl=True)
        if solver:
            self.__apply_solver(attr_filter=attr_filter)
        if bones:
            self.__apply_bones(attr_filter=attr_filter)

        mc.select(sel)

    def __apply_solver(self, attr_filter=None):
        """

        Args:
            attr_filter:

        Returns:

        """
        node_types = ['zSolverTransform', 'zSolver']
        for node_type in node_types:
            b_nodes = self.get_nodes(type_filter=node_type)
            for b_node in b_nodes:
                b_node.apply(attr_filter=attr_filter)

    def __apply_bones(self, name_filter=None, attr_filter=None):
        """

        Args:
            attr_filter:

        Returns:

        """
        from zBuilder.nodes.ziva.zBone import apply_multiple

        b_nodes = self.get_nodes(type_filter='zBone', name_filter=name_filter)
        apply_multiple(b_nodes, attr_filter=attr_filter)
