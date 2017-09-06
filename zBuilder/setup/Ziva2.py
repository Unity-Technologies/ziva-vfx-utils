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
        """

        Args:
            *args:
            **kwargs:

        Returns:

        """
        # ----------------------------------------------------------------------
        # KWARG PARSING---------------------------------------------------------
        # ----------------------------------------------------------------------
        get_mesh = kwargs.get('get_mesh', True)
        get_maps = kwargs.get('get_map_names', True)

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
                      'zLineOfAction'
                      ]

        for node_type in node_types:
            if node_type == 'zLineOfAction':
                fibers = mm.eval('zQuery -t "{}" {}'.format('zFiber', solver))
                fiber_history = mc.listHistory(fibers)
                nodes = mc.ls(fiber_history, type='zLineOfAction')
            else:
                nodes = mm.eval('zQuery -t "{}" {}'.format(node_type, solver))
            if nodes:
                for node in nodes:
                    b_node = self.node_factory(node)
                    self.add_node(b_node)

        self.stats()

    @Builder.time_this
    def apply(self, name_filter=None, attr_filter=None, interp_maps='auto',
              solver=True, bones=True, tissues=True, attachments=True,
              materials=True, fibers=True, embedder=True, cloth=True,
              lineOfActions=True, mirror=False, permissive=True):

        """
        Args:
            permissive (bool): False raises errors if something is wrong.  Defaults to True
            attr_filter (dict):  Attribute filter on what attributes to get.
                dictionary is key value where key is node type and value is 
                list of attributes to use.

                tmp = {'zSolver':['substeps']}
            name_filter (str): filter by node name.  Defaults to **None**
        """
        logger.info('applying setup....')
        sel = mc.ls(sl=True)

        node_types_to_apply = list()
        if solver:
            node_types_to_apply.append('zSolver')
            node_types_to_apply.append('zSolverTransform')
        if bones:
            node_types_to_apply.append('zBone')
        if tissues:
            node_types_to_apply.append('zTissue')
            node_types_to_apply.append('zTet')
        if cloth:
            node_types_to_apply.append('zCloth')
        if materials:
            node_types_to_apply.append('zMaterial')
        if attachments:
            node_types_to_apply.append('zAttachment')
        if fibers:
            node_types_to_apply.append('zFiber')
        if lineOfActions:
            node_types_to_apply.append('zLineOfAction')
        if embedder:
            node_types_to_apply.append('zEmbedder')

        for node_type in node_types_to_apply:
            for b_node in self.get_nodes(type_filter=node_type):
                b_node.apply(attr_filter=attr_filter, permissive=permissive)
        try:
            mc.select(sel)
        except ValueError:
            pass
