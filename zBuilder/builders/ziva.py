import logging

import maya.cmds as mc
import maya.mel as mm

import zBuilder.zMaya as mz
from zBuilder.builder import Builder

logger = logging.getLogger(__name__)

mc.loadPlugin('ziva', qt=True)


class Ziva(Builder):
    """
    To capture a Ziva rig
    """

    def __init__(self):
        Builder.__init__(self)

        for plugin in mc.pluginInfo(query=True, listPluginsPath=True):
            cmds = mc.pluginInfo(plugin, q=True, c=True)
            if cmds and 'ziva' in cmds:
                self.info['plugin_name'] = plugin
                self.info['plugin_version'] = mc.pluginInfo(plugin, q=True, v=True)
                self.info['plugin_version'] = mc.pluginInfo(plugin, q=True, p=True)
                continue

    @Builder.time_this
    def retrieve_from_scene(self, *args, **kwargs):
        """
        This gets the scene items from the scene for further manipulation or saving.
        It works on selection or something passed in args.  If nothing is selected
        it looks for a zSolver in the scene.  If something is selected or passed it uses
        that specific solver to retrieve.

        Items captured in this case are:

        * All the Ziva nodes. (zTissue, zTet, zAttachment, etc..)
        * Order of the nodes so we can re-create material layers reliably.
        * Attributes and values of the nodes. (Including weight maps)
        * Sub-tissue information.
        * User defined tet mesh reference. (Not the actual mesh)
        * Any embedded mesh reference. (Not the actual mesh)
        * Curve reference to drive zLineOfAction. (Not actual curve)
        * Relevant zSolver for each node.
        * Mesh information used for world space lookup to interpolate maps if needed.

        Args:
            get_parameters (bool): To get parameters or not.

        """
        # ----------------------------------------------------------------------
        # KWARG PARSING---------------------------------------------------------
        # ----------------------------------------------------------------------
        get_parameters = kwargs.get('get_parameters', True)

        # ----------------------------------------------------------------------
        # ARG PARSING-----------------------------------------------------------
        # ----------------------------------------------------------------------
        solver = None
        if args:
            solver = mm.eval('zQuery -t "zSolver" {}'.format(args[0]))
        else:
            solver = mm.eval('zQuery -t "zSolver"')

        # ----------------------------------------------------------------------
        # NODE STORING----------------------------------------------------------
        # ----------------------------------------------------------------------
        if solver:
            solver = solver[0]
        else:
            raise StandardError('zSolver not connected to selection.  Please try again.')

        b_solver = self.node_factory(solver)
        self.bundle.extend_scene_items(b_solver)

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
        Gets scene items based on selection.

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
                    loas = mz.get_fiber_lineofaction(fiber)
                    if loas:
                        nodes.append(loas)
            if embedder:
                mc.select(selection)
                embedder = mm.eval('zQuery -t "zEmbedder"')
                if embedder:
                    nodes.extend(embedder)
        else:
            nodes = selection

        if nodes:
            print nodes
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
            self.bundle.extend_scene_items(parameter)

    @Builder.time_this
    def build(self, name_filter=None, attr_filter=None, interp_maps='auto',
              solver=True, bones=True, tissues=True, attachments=True,
              materials=True, fibers=True, embedder=True, cloth=True,
              lineOfActions=True, mirror=False, permissive=True,
              check_meshes=False):

        """
        This builds the Ziva rig into the Maya scene.  It does not build geometry as the expectation is
        that the geometry is in the scene.

        Args:
            solver (bool): Build the solver.
            bones (bool): Build the bones.
            tissues (bool): Build the tissue and tets.
            attachments (bool): Build the attachments.
            materials (bool): Build the materials.
            fibers (bool): build the fibers.
            embedder (bool): Build the embedder.
            cloth (bool): Build the cloth.
            lineOfActions (bool): Build the line of actions.
            interp_maps (str): Option to interpolate maps.
                True: Yes interpolate
                False: No
                auto: Interpolate if it needs it (vert check)
            mirror (bool): This mirrors the geometry in bundle.
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

        if check_meshes:
            logger.info('DEPRECATED FLAG:check_meshes not used.  Use ziva -mq.')

        logger.info('Building....')
        sel = mc.ls(sl=True)

        # lets build the solver first so we can turn it off to build rest.
        # speeds up the process
        solvers = list()
        if solver:
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
                parameter.build(attr_filter=attr_filter,
                                permissive=permissive,
                                interp_maps=interp_maps)

        # turn on solver
        mc.select(sel, r=True)

        mc.setAttr(sn + '.enable', solver_value)

        # last ditch check of map validity for zAttachments and zFibers
        mz.check_map_validity(self.get_scene_items(type_filter='map'))
