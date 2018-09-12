import logging

import maya.cmds as mc
import maya.mel as mm

import zBuilder.zMaya as mz
from zBuilder.builder import Builder
from zBuilder.nodes.utils.fields import Field

logger = logging.getLogger(__name__)

try:
    mc.loadPlugin('ziva', qt=True)
except RuntimeError:
    pass

class Ziva(Builder):
    """To capture a Ziva rig.
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


    def get_parent(self):
        from zBuilder.nodes.base import Base

        # reset stuff............
        for item in self.get_scene_items():
            self.root_node._children = []
            item._parent = None
            item._children = []

        # solver transforms
        for item in self.get_scene_items(type_filter='zSolverTransform'):
            self.root_node.add_child(item)
            item._parent = self.root_node

        # solvers
        solver = {}
        for item in self.get_scene_items(type_filter=['zSolver']):
            for x in self.get_scene_items(type_filter='zSolverTransform'):
                if x.solver == item.solver:
                    parent_node = x
                    solver[item.name] = x
  
            parent_node.add_child(item)
            item._parent = parent_node

        # get bodies......
        bodies = {}
        for item in self.get_scene_items(type_filter=['zBone','zTissue','zCloth']):
            grp = Base()
            grp.name = item.association[0]
            grp.type = 'ui_{}_body'.format(item.type)
            bodies[item.association[0]] = grp

        for item in self.get_scene_items(type_filter=['zBone','zTissue','zCloth']):
            if item.type == 'zTissue':
                if item.parent_tissue:
                    bd = mm.eval('zQuery -t zTissue -m {}'.format(item.parent_tissue))[0]
                    parent_node = bodies.get(bd, self.root_node)
                else:
                    parent_node = solver.get(item.solver,self.root_node)
            else:
                parent_node = solver.get(item.solver,self.root_node)

            bodies[item.association[0]]._parent = parent_node
            parent_node.add_child(bodies[item.association[0]])

            bodies[item.association[0]].add_child(item)
            item._parent = bodies[item.association[0]]

        for item in self.get_scene_items(type_filter=['zTet']):
            parent_node = bodies.get(item.association[0], self.root_node)
            parent_node.add_child(item)
            item._parent = parent_node

        for item in self.get_scene_items(type_filter=['zMaterial', 'zFiber', 'zAttachment']):
            parent_node = bodies.get(item.association[0], None)
            if parent_node:
                parent_node.add_child(item)
                item._parent = parent_node

            if item.type == 'zAttachment':
                parent_node = bodies.get(item.association[1], None)
                if parent_node:
                    parent_node.add_child(item)

        for item in self.get_scene_items(type_filter=['zLineOfAction']):
            parent_node = self.get_scene_items(name_filter=item.fiber)[0]
            parent_node.add_child(item)
            item._parent = parent_node

        for item in self.get_scene_items(type_filter=Field.TYPES):
            self.root_node.add_child(item)
            item._parent = self.root_node

        # assign zFieldAdapter to solver
        for item in self.get_scene_items(type_filter=['zFieldAdaptor']):
            parent_node = self.get_scene_items(name_filter=item.input_field)[0]
            parent_node.add_child(item)
            item._parent = parent_node

    def retrieve_connections(self, *args, **kwargs):
        """ This retrieves the scene items from the scene based on connections to
        selection and does not get parameters for speed.  This is main call to 
        check scene for loading into a ui.

        Args:
            get_parameters (bool): To get parameters or not. Default False
        """
        # ----------------------------------------------------------------------
        # KWARG PARSING---------------------------------------------------------
        # ----------------------------------------------------------------------
        get_parameters = kwargs.get('get_parameters', False)

        # ----------------------------------------------------------------------
        # ARG PARSING-----------------------------------------------------------
        # ----------------------------------------------------------------------
        scene_selection = mc.ls(sl=True)
        selection = []
        if args:
            selection = args[0]
            mc.select(selection)
        else:
            selection = mc.ls(sl=True)

        #-----------------------------------------------------------------------
        # this gets the selected and what is connected to it by attachments.
        attachments = mm.eval('zQuery -type zAttachment')
        mc.select(attachments)
        source = mm.eval('zQuery -as')
        target = mm.eval('zQuery -at')
        mc.select(source,target)
        nodes = mm.eval('zQuery -a')

        fiber_names = [x for x in mc.ls(nodes)if mc.objectType(x) == 'zFiber']
        if fiber_names:
            line_of_actions = mc.listHistory(fiber_names)
            line_of_actions = mc.ls(line_of_actions,type='zLineOfAction')
            nodes.extend(line_of_actions)

        body_names = [x for x in mc.ls(nodes)if mc.objectType(x) in ['zCloth','zTissue']]
        if body_names:
            history = mc.listHistory(body_names)
            types = []
            types.append('zFieldAdaptor')
            types.extend(Field.TYPES)
            fields = mc.ls(history,type=types)
            nodes.extend(fields)

        if nodes:
            self._populate_nodes(nodes, get_parameters=get_parameters)
            self.get_parent()

        mc.select(scene_selection)

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

        b_solver = self.node_factory(solver, parent=None)
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
                      'zLineOfAction',
                      'zFieldAdaptor',
                      ]
        
        node_types.extend(Field.TYPES)
        
        nodes = zQuery(node_types, solver)
        if nodes:
            self._populate_nodes(nodes, get_parameters=get_parameters)
            self.get_parent()

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
            fields (bool): Gets field data.  Defaults to True
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
        fields = kwargs.get('fields', True)
        lineOfAction = kwargs.get('lineOfAction', True)
        embedder = kwargs.get('embedder', True)
        get_parameters = kwargs.get('get_parameters', True)

        print '\ngetting ziva......'

        if not attr_filter:
            attr_filter = {}

        nodes = list()

        if connections and selection:
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
            if fields:
                soft_bodies = mz.get_soft_bodies(selection)
                adaptors = mz.get_zFieldAdaptors(soft_bodies)
                fields = mz.get_fields_on_zFieldAdaptors(adaptors)
                # fields needs to come before adaptors, so that
                # they are created first when applying to scene.
                nodes.extend(fields)
                nodes.extend(adaptors)
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
            self._populate_nodes(nodes, get_parameters=get_parameters)

        mc.select(sel, r=True)
        self.get_parent()
        self.stats()

    def _populate_nodes(self, nodes, get_parameters=True):
        """
        This instantiates a builder node and populates it with given maya node.

        Args:
            nodes:

        Returns:

        """

        for node in nodes:
            parameter = self.node_factory(node, parent=None, get_parameters=get_parameters)
            self.bundle.extend_scene_items(parameter)

    def reset_solvers(self):
        """
         This resets the solvers stored in the zBuilder. Specifically, it removes
         any stored MObjects from the solvers.
        """

        solvers = list()
        solvers.append('zSolver')
        solvers.append('zSolverTransform')

        # reset the solver nodes' mobjects
        for node_type in solvers:
            logger.info('Resetting: {}'.format(node_type))
            for parameter in self.get_scene_items(type_filter=node_type):
                parameter.mobject_reset()
    
    @Builder.time_this
    def build(self, association_filter=list(), attr_filter=None, interp_maps='auto',
              solver=True, bones=True, tissues=True, attachments=True,
              materials=True, fibers=True, embedder=True, cloth=True, 
              fields=True, lineOfActions=True, mirror=False, permissive=True, 
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
            fibers (bool): Build the fibers.
            embedder (bool): Build the embedder.
            cloth (bool): Build the cloth.
            fields (bool): Build the fields.
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
            association_filter (str): filter by node association.  Defaults to list()
            

        """
        if mirror:
            for item in self.get_scene_items(type_filter='mesh'):
                item.mirror()

        if check_meshes:
            logger.info('DEPRECATED FLAG:check_meshes not used.  Use ziva -mq.')

        logger.info('Building Ziva Rig.')
        sel = mc.ls(sl=True)

        # Let's build the solver first, so we can turn it off to build the rest of the scene.
        # This speeds up the process.
        solvers = list()
        if solver:
            solvers.append('zSolver')
            solvers.append('zSolverTransform')

        # build the nodes by calling build method on each one
        for node_type in solvers:
            logger.info('Building: {}'.format(node_type))
            for parameter in self.get_scene_items(type_filter=node_type):
                parameter.build(attr_filter=attr_filter, permissive=permissive)

        # get stored solver enable value to build later. The solver comes in OFF
        solver_transform = self.get_scene_items(type_filter='zSolverTransform')
        sn = None
        if solver_transform:
            sn = solver_transform[0].name
            solver_value = solver_transform[0].attrs['enable']['value']

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
        if fields:
            node_types_to_build.extend(Field.TYPES)
            node_types_to_build.append('zFieldAdaptor')

        # build the nodes by calling build method on each one
        for node_type in node_types_to_build:
            logger.info('Building: {}'.format(node_type))
            for scene_item in self.get_scene_items(type_filter=node_type,
                                                   association_filter=association_filter):
                scene_item.build(attr_filter=attr_filter,
                                permissive=permissive,
                                interp_maps=interp_maps)

        # turn on solver
        mc.select(sel, r=True)
        if sn:
            mc.setAttr(sn + '.enable', solver_value)

        # last ditch check of map validity for zAttachments and zFibers
        mz.check_map_validity(self.get_scene_items(type_filter='map'))


def zQuery(types,solver):
    hist = mc.listHistory(solver)
    nodes = [x for x in hist if mc.objectType(x) in types]
    return nodes


