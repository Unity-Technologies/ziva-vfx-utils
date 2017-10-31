import logging

import maya.cmds as mc
import maya.mel as mm

import zBuilder.zMaya as mz
from zBuilder.builder import Builder

logger = logging.getLogger(__name__)

mc.loadPlugin('ziva', qt=True)


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
        get_parameters = kwargs.get('get_parameters', True)

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
        self.bundle.extend_scene_item(b_solver)

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
                self._populate_nodes(nodes, get_parameters=get_parameters)

        self.stats()

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
            get_parameters (bool): get mesh info. Defaults to True
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
        get_parameters = kwargs.get('get_parameters', True)


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
            self._populate_nodes(nodes, get_parameters=get_parameters)

        mc.select(sel, r=True)
        self.stats()

    def _populate_nodes(self, nodes, get_parameters=True):
        """
        This instantiates a builder node and populates it with given maya node.

        Args:
            nodes:

        Returns:

        """
        for node in nodes:
            parameter = self.node_factory(node, get_parameters=get_parameters)
            self.bundle.extend_scene_item(parameter)

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
            for item in self.get_scene_items(type_filter='mesh'):
                item.mirror()

        logger.info('Building....')
        sel = mc.ls(sl=True)

        # lets build the solver first so we can turn it off to build rest.
        # speeds up the process
        solvers = list()
        if solver:
            # logger.info('Building solver.')
            # for node_type in ['zSolver', 'zSolverTransform']:
            #     for parameter in self.get_scene_items(type_filter=node_type):
            #         parameter.apply(attr_filter=attr_filter, permissive=permissive,
            #                      check_meshes=check_meshes, interp_maps=interp_maps)
            solvers.append('zSolver')
            solvers.append('zSolverTransform')

        # build the nodes by calling build method on each one
        for node_type in solvers:
            for parameter in self.get_scene_items(type_filter=node_type):
                parameter.build(attr_filter=attr_filter, permissive=permissive)

        # get stored solver enable value to build later. The solver comes in OFF
        solver_transform = self.get_scene_items(type_filter='zSolverTransform')[0]
        sn = solver_transform.name
        solver_value = solver_transform.attrs['enable']['value']

        # generate list of node types to build
        node_types_to_build = list()

        if bones:
            node_types_to_build.append('zBone')
        if tissues:
            node_types_to_build.append('zTissue')
            node_types_to_build.append('zTet')
        if cloth:
            node_types_to_build.append('zCloth')
        if materials:
            node_types_to_build.append('zMaterial')
        if attachments:
            node_types_to_build.append('zAttachment')
        if fibers:
            node_types_to_build.append('zFiber')
        if lineOfActions:
            node_types_to_build.append('zLineOfAction')
        if embedder:
            node_types_to_build.append('zEmbedder')

        # build the nodes by calling build method on each one
        for node_type in node_types_to_build:
            for parameter in self.get_scene_items(type_filter=node_type):
                parameter.build(attr_filter=attr_filter, permissive=permissive,
                                check_meshes=check_meshes,
                                interp_maps=interp_maps)

        # turn on solver
        mc.select(sel, r=True)

        mc.setAttr(sn + '.enable', solver_value)

        # last ditch check of map validity for zAttachments and zFibers
        mz.check_map_validity(self.get_scene_items(type_filter='map'))
