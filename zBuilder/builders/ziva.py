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

ZNODES = [
    'zSolver', 'zSolverTransform', 'zTet', 'zTissue', 'zBone', 'zCloth', 'zSolver', 'zEmbedder',
    'zAttachment', 'zMaterial', 'zFiber'
]


class Ziva(Builder):
    """To capture a Ziva rig.
    """

    def __init__(self):
        super(Ziva, self).__init__()

        self.bodies = {}

        for plugin in mc.pluginInfo(query=True, listPluginsPath=True):
            cmds = mc.pluginInfo(plugin, q=True, c=True)
            if cmds and 'ziva' in cmds:
                self.info['plugin_name'] = plugin
                self.info['plugin_version'] = mc.pluginInfo(plugin, q=True, v=True)
                self.info['plugin_version'] = mc.pluginInfo(plugin, q=True, p=True)
                continue

    def setup_tree_hierarchy(self):
        """Sets up hierarchy for a tree view.  This will look at items and assign the proper 
        children, parent for QT.
        """
        from zBuilder.nodes.base import Base
        from zBuilder.nodes.dg_node import DGNode

        # reset stuff............
        for item in self.get_scene_items():
            self.root_node.children = []
            item.parent = None
            item.children = []

        # solver transforms
        for item in self.get_scene_items(type_filter='zSolverTransform'):
            self.root_node.add_child(item)
            item.parent = self.root_node

        # solvers
        solver = {}
        for item in self.get_scene_items(type_filter=['zSolver']):
            for x in self.get_scene_items(type_filter='zSolverTransform'):
                if x.solver == item.solver:
                    parent_node = x
                    solver[item.name] = x

            parent_node.add_child(item)
            item.parent = parent_node

        # get bodies-----------------------------------------------------------
        for item in self.get_scene_items(type_filter=['zBone', 'zTissue', 'zCloth']):
            grp = DGNode()
            grp.name = item.long_association[0]
            grp.type = 'ui_{}_body'.format(item.type)
            grp.depends_on = item.mobject
            grp.mobject = item.long_association[0]

            self.bodies[item.long_association[0]] = grp

        for item in self.get_scene_items(type_filter=['zBone', 'zTissue', 'zCloth']):
            if item.type == 'zTissue':
                if item.parent_tissue:
                    bd = mm.eval('zQuery -t zTissue -l -m {}'.format(item.parent_tissue))[0]
                    parent_node = self.bodies.get(bd, self.root_node)
                else:
                    parent_node = solver.get(item.solver, self.root_node)
            else:
                parent_node = solver.get(item.solver, self.root_node)

            self.bodies[item.long_association[0]].parent = parent_node
            parent_node.add_child(self.bodies[item.long_association[0]])

            self.bodies[item.long_association[0]].add_child(item)
            item.parent = self.bodies[item.long_association[0]]

        for item in self.get_scene_items(type_filter=['zTet']):
            parent_node = self.bodies.get(item.long_association[0], self.root_node)
            parent_node.add_child(item)
            item.parent = parent_node

        for item in self.get_scene_items(type_filter=['zMaterial', 'zFiber', 'zAttachment']):
            parent_node = self.bodies.get(item.long_association[0], None)
            if parent_node:
                parent_node.add_child(item)
                item.parent = parent_node

            if item.type == 'zAttachment':
                parent_node = self.bodies.get(item.long_association[1], None)
                if parent_node:
                    parent_node.add_child(item)

        # rest shapes
        for item in self.get_scene_items(type_filter=['zRestShape']):
            parent_node = self.get_scene_items(name_filter=item.tissue_name)
            if parent_node:
                parent_node = parent_node[0]
                parent_node.add_child(item)
                item.parent = parent_node

            # targets ----------------------
            for target in item.targets:
                grp = DGNode()
                grp.name = target
                grp.type = 'ui_target_body'
                grp.mobject = target
                grp.parent = item
                item.add_child(grp)

        # rivets ------
        rivets = {}
        for x in self.get_scene_items(type_filter='zRivetToBone'):
            if x.long_curve_name not in rivets:
                rivets[x.long_curve_name] = []
            rivets[x.long_curve_name].append(x)

        # line of actions
        for item in self.get_scene_items(type_filter=['zLineOfAction']):
            parent_node = self.get_scene_items(name_filter=item.fiber)[0]

            for crv in item.long_association:
                grp = DGNode()
                grp.name = crv
                grp.type = 'ui_curve_body'
                grp.depends_on = item.mobject
                parent_node.add_child(grp)
                grp.parent = parent_node

                grp.add_child(item)
                item.parent = parent_node
                rivet_items = rivets.get(crv, None)
                if rivet_items:
                    for rivet in rivet_items:
                        grp.add_child(rivet)
                        rivet.parent = grp

        for item in self.get_scene_items(type_filter=Field.TYPES):
            self.root_node.add_child(item)
            item.parent = self.root_node

        # assign zFieldAdapter to solver
        for item in self.get_scene_items(type_filter=['zFieldAdaptor']):
            parent_node = self.get_scene_items(name_filter=item.input_field)[0]
            parent_node.add_child(item)
            item.parent = parent_node

    def __add_bodies(self, bodies):
        '''This is using zQuery -a under the hood.  It queries everything connected to bodies.
        If bodies is an empty list then it returns contents of whole scene.
        
        Args:
            bodies (list()): The bodies to query.
        
        Returns:
            list(): list of Ziva VFX nodes associated with bodies.  If nothing returns an empty list
        '''

        # query all the ziva nodes---------------------------------------------
        mc.select(bodies)
        nodes = mm.eval('zQuery -a')

        if nodes:
            # find zFiber---------------------------------------------
            fiber_names = [x for x in nodes if mc.objectType(x) == 'zFiber']
            if fiber_names:
                # find line of action----------------------------------------
                line_of_actions = mc.listHistory(fiber_names)
                line_of_actions = mc.ls(line_of_actions, type='zLineOfAction')
                nodes.extend(line_of_actions)

            tet_names = [x for x in nodes if mc.objectType(x) == 'zTet']
            for tet_name in tet_names:
                # find the rest shape--------------------------------------
                rest_shape = mc.listConnections('{}.oGeo'.format(tet_name), type='zRestShape')
                if rest_shape:
                    nodes.extend(rest_shape)

            return nodes
        else:
            return []

    def retrieve_connections(self, *args, **kwargs):
        """ This retrieves the scene items from the scene based on connections to
        selection and does not get parameters for speed.  This is main call to 
        check scene for loading into a ui.

        Args:
            get_parameters (bool): To get parameters or not. Default False
        """
        # ---------------------------------------------------------------------
        # KWARG PARSING--------------------------------------------------------
        # ---------------------------------------------------------------------
        get_parameters = kwargs.get('get_parameters', False)

        # ---------------------------------------------------------------------
        # ARG PARSING----------------------------------------------------------
        # ---------------------------------------------------------------------
        scene_selection = mc.ls(sl=True, l=True)
        if args:
            selection = args[0]
            mc.select(selection)
        else:
            selection = scene_selection

        selection = transform_rivet_and_LoA_into_tissue_meshes(selection)

        nodes = []
        nodes.extend(self.__add_bodies(selection))

        # find attahment source and or targets to add to nodes.................
        attachment_names = [x for x in nodes if mc.objectType(x) == 'zAttachment']
        meshes = []
        if attachment_names:
            for attachment in attachment_names:
                meshes.extend(mm.eval('zQuery -as -l {}'.format(attachment)))
                meshes.extend(mm.eval('zQuery -at -l {}'.format(attachment)))

        if meshes:
            nodes.extend(self.__add_bodies(meshes))

        # # find attahment source and or targets to add to nodes.................
        tissue_names = [x for x in nodes if mc.objectType(x) == 'zTissue']

        children = []
        for tissue in tissue_names:
            children.extend(mz.none_to_empty(mc.listConnections(tissue + '.oChildTissue')))

        if children:
            nodes.extend(self.__add_bodies(children))

        body_names = [x for x in nodes if mc.objectType(x) in ['zCloth', 'zTissue']]
        if body_names:
            history = mc.listHistory(body_names)
            types = []
            types.append('zFieldAdaptor')
            types.extend(Field.TYPES)
            fields = mc.ls(history, type=types)
            nodes.extend(fields)

        fibers = mz.get_zFibers(selection)
        if fibers:
            hist = mc.listHistory(fibers)
            nodes.extend(mc.ls(hist, type='zRivetToBone'))

        if nodes:
            self._populate_nodes(nodes, get_parameters=get_parameters)
            self.setup_tree_hierarchy()

        mc.select(scene_selection)
        self.stats()

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
        # ---------------------------------------------------------------------
        # KWARG PARSING--------------------------------------------------------
        # ---------------------------------------------------------------------
        get_parameters = kwargs.get('get_parameters', True)

        # ---------------------------------------------------------------------
        # ARG PARSING----------------------------------------------------------
        # ---------------------------------------------------------------------
        solver = None
        if args:
            solver = mm.eval('zQuery -t "zSolver" {}'.format(args[0]))
        else:
            solver = mm.eval('zQuery -t "zSolver"')

        # ---------------------------------------------------------------------
        # NODE STORING---------------------------------------------------------
        # ---------------------------------------------------------------------
        if solver:
            solver = solver[0]
        else:
            raise StandardError('zSolver not connected to selection.  Please try again.')

        b_solver = self.node_factory(solver, parent=None)
        self.bundle.extend_scene_items(b_solver)

        node_types = [
            'zSolverTransform',
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
            'zRivetToBone',
            'zRestShape',
        ]

        node_types.extend(Field.TYPES)
        nodes = zQuery(node_types, solver)
        if nodes:
            self._populate_nodes(nodes, get_parameters=get_parameters)
            self.setup_tree_hierarchy()

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
        rivetToBone = kwargs.get('rivetToBone', True)
        restShape = kwargs.get('restShape', True)
        embedder = kwargs.get('embedder', True)
        get_parameters = kwargs.get('get_parameters', True)

        print('\ngetting ziva......')

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
            if rivetToBone:
                fibers = mz.get_zFibers(selection)
                if fibers:
                    hist = mc.listHistory(fibers)
                    nodes.extend(mc.ls(hist, type='zRivetToBone'))
            if lineOfAction:
                for fiber in mz.get_zFibers(selection):
                    loas = mz.get_fiber_lineofaction(fiber)
                    if loas:
                        nodes.append(loas)
            if restShape:
                mc.select(selection)
                rest_shapes = mm.eval('zQuery -t zRestShape')
                if rest_shapes:
                    nodes.extend(rest_shapes)
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
        self.setup_tree_hierarchy()
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
            for scene_item in self.get_scene_items(type_filter=node_type):
                scene_item.mobject_reset()

    @Builder.time_this
    def build(self,
              association_filter=list(),
              attr_filter=None,
              interp_maps='auto',
              solver=True,
              bones=True,
              tissues=True,
              attachments=True,
              materials=True,
              fibers=True,
              embedder=True,
              cloth=True,
              fields=True,
              lineOfActions=True,
              rivetToBone=True,
              restShape=True,
              mirror=False,
              permissive=True):
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
            for scene_item in self.get_scene_items(type_filter=node_type):
                scene_item.build(attr_filter=attr_filter, permissive=permissive)

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
        if rivetToBone:
            node_types_to_build.append('zRivetToBone')
        if restShape:
            node_types_to_build.append('zRestShape')
        if embedder:
            node_types_to_build.append('zEmbedder')
        if fields:
            node_types_to_build.extend(Field.TYPES)
            node_types_to_build.append('zFieldAdaptor')

        # build the nodes by calling build method on each one
        build_type_list = []  # keep track of types built to not print it over for each item.
        for node_type in node_types_to_build:
            for scene_item in self.get_scene_items(type_filter=node_type,
                                                   association_filter=association_filter):

                # This is checking if we already built a particular type so we only print it out
                # once.
                if scene_item.type not in build_type_list:
                    logger.info('Building: {}'.format(node_type))
                build_type_list.append(scene_item.type)

                scene_item.build(attr_filter=attr_filter,
                                 permissive=permissive,
                                 interp_maps=interp_maps)

        # turn on solver
        mc.select(sel, r=True)
        if sn:
            mc.setAttr(sn + '.enable', solver_value)

        # last ditch check of map validity for zAttachments and zFibers
        mz.check_map_validity(self.get_scene_items(type_filter='map'))


def transform_rivet_and_LoA_into_tissue_meshes(selection):
    """ This takes a list of items from a maya scene and if it finds any 
    zLineOfAction or zRivetToBone it replaces that item with the corresponding
    tissued mesh.

    This is until zQuery is re-implemented in python.
    
    Args:
        selection ([str]): List of items in mayas scene

    Returns:
        list(): Selection list with item types in 'type_' replaced with 
        corresponding tissued mesh.
    """
    # these are the types we need to find the tissued mesh for.
    type_ = ['zLineOfAction', 'zRivetToBone']

    output = []
    for item in selection:
        if mc.objectType(item) in type_:
            history = mc.listHistory(item, future=True)
            fiber = mc.ls(history, type='zFiber')
            mc.select(fiber)
            meshes = mm.eval('zQuery -t zTissue -m -l')
            output.append(meshes[0])
        else:
            output.append(item)
    return output


def zQuery(types, solver):

    solver_history = mc.listHistory(solver)
    types_not_in_znodes = set(types) - set(ZNODES)
    nodes = [x for x in solver_history if mc.objectType(x) in types_not_in_znodes]

    types_in_znodes = list(set(ZNODES) & set(types))

    for node_type in types_in_znodes:
        tmp = mm.eval('zQuery -t "{}" {}'.format(node_type, solver))
        if tmp:
            nodes.extend(tmp)

    return nodes
