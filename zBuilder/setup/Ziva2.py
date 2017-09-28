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
        get_maps = kwargs.get('get_maps', True)

        # ----------------------------------------------------------------------
        # NODE STORING----------------------------------------------------------
        # ----------------------------------------------------------------------
        solver = None
        if args:
            solver = mm.eval('zQuery -t "zSolver" {}'.format(args[0]))
        else:
            solver = mm.eval('zQuery -t "zSolver"')

        if solver:
            solver = solver[0]
        else:
            raise StandardError('zSolver not connected to selection.  Please try again.')

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
                if fibers:
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
              lineOfActions=True, mirror=False, permissive=True,
              check_meshes=True):

        """
        Args:
            permissive (bool): False raises errors if something is wrong. Defaults to True
            attr_filter (dict):  Attribute filter on what attributes to get.
                dictionary is key value where key is node type and value is 
                list of attributes to use.

                tmp = {'zSolver':['substeps']}
            name_filter (str): filter by node name.  Defaults to **None**
        """
        if mirror:
            meshes = self.get_data_by_key('mesh')
            for mesh in meshes:
                meshes[mesh].mirror()
                
        logger.info('applying setup....')
        sel = mc.ls(sl=True)

        # get stored solver enable value to apply later. The solver comes in OFF
        solver_transform = self.get_nodes(type_filter='zSolverTransform')[0]
        sn = solver_transform.name
        solver_value = solver_transform.get_attr_value('enable')

        # generate list of node types to build
        node_types_to_apply = list()
        if solver:
            logger.info('Building solver.')
            for node_type in ['zSolver', 'zSolverTransform']:
                for b_node in self.get_nodes(type_filter=node_type):
                    b_node.apply(attr_filter=attr_filter, permissive=permissive,
                                 check_meshes=check_meshes, interp_maps=interp_maps)
            # node_types_to_apply.append('zSolver')
            # node_types_to_apply.append('zSolverTransform')
        if bones:
            logger.info('Building bones.')
            for b_node in self.get_nodes(type_filter='zBone'):
                b_node.apply(attr_filter=attr_filter, permissive=permissive,
                             check_meshes=check_meshes, interp_maps=interp_maps)
            # node_types_to_apply.append('zBone')
        if tissues:
            logger.info('Building tissues.')
            for node_type in ['zTissue', 'zTet']:
                for b_node in self.get_nodes(type_filter=node_type):
                    b_node.apply(attr_filter=attr_filter, permissive=permissive,
                                 check_meshes=check_meshes, interp_maps=interp_maps)
            # node_types_to_apply.append('zTissue')
            # node_types_to_apply.append('zTet')
        if cloth:
            logger.info('Building cloth.')
            for b_node in self.get_nodes(type_filter='zCloth'):
                b_node.apply(attr_filter=attr_filter, permissive=permissive,
                             check_meshes=check_meshes, interp_maps=interp_maps)
            # node_types_to_apply.append('zCloth')
        if materials:
            logger.info('Building materials.')
            for b_node in self.get_nodes(type_filter='zMaterial'):
                b_node.apply(attr_filter=attr_filter, permissive=permissive,
                             check_meshes=check_meshes, interp_maps=interp_maps)
            # node_types_to_apply.append('zMaterial')
        if attachments:
            logger.info('Building attachments.')
            for b_node in self.get_nodes(type_filter='zAttachment'):
                b_node.apply(attr_filter=attr_filter, permissive=permissive,
                             check_meshes=check_meshes, interp_maps=interp_maps)
            #node_types_to_apply.append('zAttachment')
        if fibers:
            logger.info('Building fibers.')
            for b_node in self.get_nodes(type_filter='zFiber'):
                b_node.apply(attr_filter=attr_filter, permissive=permissive,
                             check_meshes=check_meshes, interp_maps=interp_maps)
            # node_types_to_apply.append('zFiber')
        if lineOfActions:
            logger.info('Building lines of action.')
            for b_node in self.get_nodes(type_filter='zLineOfAction'):
                b_node.apply(attr_filter=attr_filter, permissive=permissive,
                             check_meshes=check_meshes, interp_maps=interp_maps)
            # node_types_to_apply.append('zLineOfAction')
        if embedder:
            logger.info('Building embedder.')
            for b_node in self.get_nodes(type_filter='zEmbedder'):
                b_node.apply(attr_filter=attr_filter, permissive=permissive,
                             check_meshes=check_meshes, interp_maps=interp_maps)
            # node_types_to_apply.append('zEmbedder')



        # build the nodes by calling apply method on each one
        # for node_type in node_types_to_apply:
        #     for b_node in self.get_nodes(type_filter=node_type):
        #         b_node.apply(attr_filter=attr_filter, permissive=permissive,
        #                      check_meshes=check_meshes, interp_maps=interp_maps)

        # turn on solver
        mc.setAttr(sn + '.enable', solver_value)
        mc.select(sel, r=True)
