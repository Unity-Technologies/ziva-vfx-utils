import logging

import maya.cmds as mc
import maya.mel as mm

import zBuilder.zMaya as mz
from zBuilder.builder import Builder

logger = logging.getLogger(__name__)


class Ziva(Builder):
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

        b_solver = self.parameter_factory(solver)
        self.bundle.extend_parameters(b_solver)

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
                self._populate_nodes(nodes,
                                     get_mesh=get_mesh,
                                     get_maps=get_maps)

        self.bundle.stats()

    @Builder.time_this
    def retrieve_from_scene_selection(self, *args, **kwargs):
        """
        Gets data based on selection

        Args:
            attr_filter (dict):  Attribute filter on what attributes to get.
                dictionary is key value where key is node type and value is
                list of attributes to use.

                af = {'zSolver':['substeps']}
            connections (bool): Gets the ziva nodes connected to selection as well. Defaults to True
            solver (bool): Gets solver data.  Defaults to True
            bones (bool): Gets bone data.  Defaults to True
            tissue (bool): Gets tissue data.  Defaults to True
            attachments (bool): Gets attachments data.  Defaults to True
            materials (bool): Gets materials data.  Defaults to True
            fibers (bool): Gets fibers data.  Defaults to True
            cloth (bool): Gets cloth data.  Defaults to True
            lineOfAction (bool): Gets line of action data.  Defaults to True
            embedder (bool): Gets embedder data.  Defaults to True
            get_mesh (bool): get mesh info. Defaults to True
            get_maps (bool): get map info. Defaults to True
        """

        # get current selection to re-apply
        sel = mc.ls(sl=True)

        # args
        selection = None
        if args:
            selection = mc.ls(args[0], l=True)
        else:
            selection = mc.ls(sl=True, l=True)

        # kwargs
        connections = kwargs.get('connections', True)
        attr_filter = kwargs.get('attr_filter', None)
        solver = kwargs.get('solver', True)
        bones = kwargs.get('bones', True)
        tissues = kwargs.get('tissues', True)
        attachments = kwargs.get('attachments', True)
        materials = kwargs.get('materials', True)
        fibers = kwargs.get('fibers', True)
        cloth = kwargs.get('cloth', True)
        lineOfAction = kwargs.get('lineOfAction', True)
        embedder = kwargs.get('embedder', True)
        get_mesh = kwargs.get('get_mesh', True)
        get_maps = kwargs.get('get_map_names', True)

        print '\ngetting ziva......'

        if not attr_filter:
            attr_filter = {}

        nodes = list()
        if connections:
            if solver:
                sol = mz.get_zSolver(selection[0])
                if sol:
                    nodes.extend(sol)
                    nodes.extend(mz.get_zSolverTransform(selection[0]))
            if bones:
                nodes.extend(mz.get_zBones(selection))
            if tissues:
                nodes.extend(mz.get_zTissues(selection))
                nodes.extend(mz.get_zTets(selection))
            if attachments:
                nodes.extend(mz.get_zAttachments(selection))
            if materials:
                nodes.extend(mz.get_zMaterials(selection))
            if fibers:
                nodes.extend(mz.get_zFibers(selection))
            if cloth:
                nodes.extend(mz.get_zCloth(selection))
            if lineOfAction:
                for fiber in mz.get_zFibers(selection):
                    nodes.append(mz.get_fiber_lineofaction(fiber))
            if embedder:
                mc.select(selection)
                embedder = mm.eval('zQuery -t "zEmbedder"')
                if embedder:
                    nodes.extend(embedder)
        else:
            nodes = selection

        if nodes:
            self._populate_nodes(nodes)

        mc.select(sel, r=True)
        self.bundle.stats()

    def _populate_nodes(self, nodes, get_mesh=True, get_maps=True):
        """
        This instantiates a builder node and populates it with given maya node.

        Args:
            nodes:

        Returns:

        """
        for node in nodes:
            b_node = self.parameter_factory(node)
            self.bundle.extend_parameters(b_node)

    @Builder.time_this
    def build(self, name_filter=None, attr_filter=None, interp_maps='auto',
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
            [item.mirror() for item in self.bundle.get_parameters(type_filter='mesh')]

        logger.info('Building setup....')
        sel = mc.ls(sl=True)

        # get stored solver enable value to build later. The solver comes in OFF
        solver_transform = self.bundle.get_parameters(type_filter='zSolverTransform')[0]
        sn = solver_transform.name
        solver_value = solver_transform.attrs['enable']['value']

        # generate list of node types to build
        node_types_to_build = list()
        if solver:
            # logger.info('Building solver.')
            # for node_type in ['zSolver', 'zSolverTransform']:
            #     for b_node in self.get_parameters(type_filter=node_type):
            #         b_node.apply(attr_filter=attr_filter, permissive=permissive,
            #                      check_meshes=check_meshes, interp_maps=interp_maps)
            node_types_to_build.append('zSolver')
            node_types_to_build.append('zSolverTransform')
        if bones:
            # logger.info('Building bones.')
            # for b_node in self.get_parameters(type_filter='zBone'):
            #     b_node.apply(attr_filter=attr_filter, permissive=permissive,
            #                  check_meshes=check_meshes, interp_maps=interp_maps)
            node_types_to_build.append('zBone')
        if tissues:
            # logger.info('Building tissues.')
            # for node_type in ['zTissue', 'zTet']:
            #     for b_node in self.get_parameters(type_filter=node_type):
            #         b_node.apply(attr_filter=attr_filter, permissive=permissive,
            #                      check_meshes=check_meshes, interp_maps=interp_maps)
            node_types_to_build.append('zTissue')
            node_types_to_build.append('zTet')
        if cloth:
            # logger.info('Building cloth.')
            # for b_node in self.get_parameters(type_filter='zCloth'):
            #     b_node.apply(attr_filter=attr_filter, permissive=permissive,
            #                  check_meshes=check_meshes, interp_maps=interp_maps)
            node_types_to_build.append('zCloth')
        if materials:
            # logger.info('Building materials.')
            # for b_node in self.get_parameters(type_filter='zMaterial'):
            #     b_node.apply(attr_filter=attr_filter, permissive=permissive,
            #                  check_meshes=check_meshes, interp_maps=interp_maps)
            node_types_to_build.append('zMaterial')
        if attachments:
            # logger.info('Building attachments.')
            # for b_node in self.get_parameters(type_filter='zAttachment'):
            #     b_node.apply(attr_filter=attr_filter, permissive=permissive,
            #                  check_meshes=check_meshes, interp_maps=interp_maps)
            node_types_to_build.append('zAttachment')
        if fibers:
            # logger.info('Building fibers.')
            # for b_node in self.get_parameters(type_filter='zFiber'):
            #     b_node.apply(attr_filter=attr_filter, permissive=permissive,
            #                  check_meshes=check_meshes, interp_maps=interp_maps)
            node_types_to_build.append('zFiber')
        if lineOfActions:
            # logger.info('Building lines of action.')
            # for b_node in self.get_parameters(type_filter='zLineOfAction'):
            #     b_node.apply(attr_filter=attr_filter, permissive=permissive,
            #                  check_meshes=check_meshes, interp_maps=interp_maps)
            node_types_to_build.append('zLineOfAction')
        if embedder:
            # logger.info('Building embedder.')
            # for b_node in self.get_parameters(type_filter='zEmbedder'):
            #     b_node.apply(attr_filter=attr_filter, permissive=permissive,
            #                  check_meshes=check_meshes, interp_maps=interp_maps)
            node_types_to_build.append('zEmbedder')

        # build the nodes by calling build method on each one
        for node_type in node_types_to_build:
            for b_node in self.bundle.get_parameters(type_filter=node_type):
                b_node.build(attr_filter=attr_filter, permissive=permissive,
                             check_meshes=check_meshes, interp_maps=interp_maps)

        # turn on solver
        mc.setAttr(sn + '.enable', solver_value)
        mc.select(sel, r=True)
