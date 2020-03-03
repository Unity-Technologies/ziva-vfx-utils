import logging
from collections import defaultdict

from maya import cmds
from maya import mel

import zBuilder.zMaya as mz
from zBuilder.builder import Builder
from zBuilder.nodes.utils.fields import Field

logger = logging.getLogger(__name__)

try:
    cmds.loadPlugin('ziva', qt=True)
except RuntimeError:
    pass

ZNODES = [
    'zSolver',
    'zSolverTransform',
    'zTet',
    'zTissue',
    'zBone',
    'zCloth',
    'zAttachment',
    'zMaterial',
    'zFiber',
    'zEmbedder',
]
"""This is order that the Ziva nodes get retrieved and built.  We need to have solver first 
then the bodies.  After that the order is not so crutial.  
This is an uncomplete list as of now.  Some nodes get added on after, that will be changed in
VFXACT-578
"""


class SolverDisabler:
    def __init__(self, solver_name):
        """SolverDisabler is a context manager object that disables a solver for the duration of
        the context and then restores its initial state. This is useful for improving the
        performance of a code block that's making many changes to a solver. This manager object
        is preferable to doing it 'by hand' because it handles exceptions and DG connections that
        the naive solution (getAttr/setAttr) would fail to handle."""

        self.enable_plug = solver_name + '.enable'
        self.connection_source = None
        self.enable_value = True

    def __enter__(self):
        self.enable_value = cmds.getAttr(self.enable_plug)
        self.connection_source = cmds.listConnections(self.enable_plug, plugs=True)
        if self.connection_source:
            cmds.disconnectAttr(self.connection_source[0], self.enable_plug)

        cmds.setAttr(self.enable_plug, False)

    def __exit__(self, type, value, traceback):
        cmds.setAttr(self.enable_plug, self.enable_value)

        if self.connection_source:
            cmds.connectAttr(self.connection_source[0], self.enable_plug)


class Ziva(Builder):
    """To capture a Ziva rig.
    """

    def __init__(self):
        super(Ziva, self).__init__()

        self.geo = {}

        for plugin in cmds.pluginInfo(query=True, listPluginsPath=True):
            commands = cmds.pluginInfo(plugin, q=True, c=True)
            if commands and 'ziva' in commands:
                self.info['plugin_name'] = plugin
                self.info['plugin_version'] = cmds.pluginInfo(plugin, q=True, v=True)
                self.info['plugin_version'] = cmds.pluginInfo(plugin, q=True, p=True)
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

        # solvers
        collected_solver_dict = {}
        for item in self.get_scene_items(type_filter=['zSolver']):
            for x in self.get_scene_items(type_filter=['zSolverTransform']):
                if x.solver == item.solver:
                    parent_node = x
                    collected_solver_dict[item.long_name] = x
                    parent_node.add_child(item)

        # get geometry-----------------------------------------------------------
        for item in self.get_scene_items(type_filter=['zBone', 'zTissue', 'zCloth']):
            # proxy object to represent geometry
            grp = DGNode()
            grp.name = item.nice_association[0]
            grp.type = 'ui_{}_body'.format(item.type)
            # store ziva node this geometry depends on
            # to synchronize enable/envelope behaviour in the scene panel
            grp.depends_on = item
            self.geo[item.nice_association[0]] = grp

        for item in self.get_scene_items(type_filter=['zBone', 'zTissue', 'zCloth']):
            if item.type == 'zTissue':
                # if it is a zTissue node we need to check if it is part of a subTissue
                if item.parent_tissue:
                    # This node has a parent subTissue, so lets find the parents mesh
                    # for proper parenting.
                    parent_tissue_mesh = item.parent_tissue.nice_association[0]
                    parent_node = self.geo.get(parent_tissue_mesh, self.root_node)
                else:
                    parent_node = collected_solver_dict.get(item.solver.long_name, self.root_node)
            else:
                parent_node = collected_solver_dict.get(item.solver.long_name, self.root_node)

            self.geo[item.nice_association[0]].parent = parent_node
            parent_node.add_child(self.geo[item.nice_association[0]])

            self.geo[item.nice_association[0]].add_child(item)

        for item in self.get_scene_items(type_filter=['zTet']):
            parent_node = self.geo.get(item.nice_association[0], self.root_node)
            parent_node.add_child(item)

        for item in self.get_scene_items(type_filter=['zMaterial', 'zFiber', 'zAttachment']):
            parent_node = self.geo.get(item.nice_association[0], None)
            if parent_node:
                parent_node.add_child(item)

            if item.type == 'zAttachment':
                parent_node = self.geo.get(item.nice_association[1], None)
                if parent_node:
                    parent_node.add_child(item)

        # rest shapes
        for item in self.get_scene_items(type_filter=['zRestShape']):
            parent_node = self.get_scene_items(name_filter=item.tissue_item.name)
            if parent_node:
                parent_node = parent_node[0]
                parent_node.add_child(item)

            # targets ----------------------
            for target in item.targets:
                grp = DGNode()
                grp.name = target
                grp.type = 'ui_target_body'
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
            parent_node = item.fiber_item

            for crv in item.nice_association:
                # proxy object to represent geometry
                # curve geometry does not need depends_on parameter
                # because zLineOfAction does not have enable/envelope attribute
                grp = DGNode()
                grp.name = crv
                grp.type = 'ui_curve_body'
                parent_node.add_child(grp)

                grp.add_child(item)
                item.parent = parent_node
                rivet_items = rivets.get(crv, None)
                if rivet_items:
                    for rivet in rivet_items:
                        grp.add_child(rivet)
                self.geo[item.nice_association[0]] = grp

        for item in self.get_scene_items(type_filter=Field.TYPES):
            self.root_node.add_child(item)

        # assign zFieldAdapter to solver
        for item in self.get_scene_items(type_filter=['zFieldAdaptor']):
            parent_node = self.get_scene_items(name_filter=item.input_field)[0]
            parent_node.add_child(item)

    def __add_bodies(self, bodies):
        '''This is using zQuery -a under the hood.  It queries everything connected to bodies.
        If bodies is an empty list then it returns contents of whole scene.
        
        Args:
            bodies (list()): The bodies to query.
        
        Returns:
            list(): list of Ziva VFX nodes associated with bodies.  If nothing returns an empty list
        '''

        # query all the ziva nodes---------------------------------------------
        cmds.select(bodies)
        nodes = mel.eval('zQuery -a -l')

        if nodes:
            # find zFiber---------------------------------------------
            fiber_names = [x for x in nodes if cmds.objectType(x) == 'zFiber']
            if fiber_names:
                # find line of action----------------------------------------
                line_of_actions = cmds.listHistory(fiber_names)
                line_of_actions = cmds.ls(line_of_actions, type='zLineOfAction')
                nodes.extend(line_of_actions)

            tet_names = [x for x in nodes if cmds.objectType(x) == 'zTet']
            for tet_name in tet_names:
                # find the rest shape--------------------------------------
                rest_shape = cmds.listConnections('{}.oGeo'.format(tet_name), type='zRestShape')
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
        scene_selection = cmds.ls(sl=True, l=True)
        if args:
            selection = args[0]
            cmds.select(selection)
        else:
            selection = scene_selection

        selection = transform_rivet_and_LoA_into_tissue_meshes(selection)

        nodes = []
        nodes.extend(self.__add_bodies(selection))

        # find attahment source and or targets to add to nodes.................
        attachment_names = [x for x in nodes if cmds.objectType(x) == 'zAttachment']
        meshes = []
        if attachment_names:
            for attachment in attachment_names:
                meshes.extend(mel.eval('zQuery -as -l {}'.format(attachment)))
                meshes.extend(mel.eval('zQuery -at -l {}'.format(attachment)))

        if meshes:
            nodes.extend(self.__add_bodies(meshes))

        # # find attahment source and or targets to add to nodes.................
        tissue_names = [x for x in nodes if cmds.objectType(x) == 'zTissue']

        children = []
        for tissue in tissue_names:
            children.extend(mz.none_to_empty(cmds.listConnections(tissue + '.oChildTissue')))

        if children:
            nodes.extend(self.__add_bodies(children))

        body_names = [x for x in nodes if cmds.objectType(x) in ['zCloth', 'zTissue']]
        if body_names:
            history = cmds.listHistory(body_names)
            types = []
            types.append('zFieldAdaptor')
            types.extend(Field.TYPES)
            fields = cmds.ls(history, type=types)
            nodes.extend(fields)

        fibers = mz.get_zFibers(selection)
        if fibers:
            hist = cmds.listHistory(fibers)
            nodes.extend(cmds.ls(hist, type='zRivetToBone'))

        def reorder_items_from_retrieve_connnections(nodes):
            """The items coming from retrieve_connections are coming in at wrong order.
            order should be same as what is listed in ZNODES.  THis conforms nodes to
            that order.
            
            Args:
                nodes (list): list of node names to re-order
            
            Returns:
                list: ordered list
            """

            nodes_reordered = []
            tmp = []
            for item in ZNODES:
                for x in nodes:
                    if cmds.objectType(x) == item:
                        nodes_reordered.append(x)
                    elif cmds.objectType(x) == 'zGeo':
                        nodes.remove(x)
                    else:
                        tmp.append(x)
            nodes = nodes_reordered + tmp
            # remove duplicates
            seen = set()
            seen_add = seen.add
            nodes = [x for x in nodes if not (x in seen or seen_add(x))]
            return nodes

        if nodes:
            nodes = reorder_items_from_retrieve_connnections(nodes)
            self._populate_nodes(nodes, get_parameters=get_parameters)
            self.setup_tree_hierarchy()

        cmds.select(scene_selection)
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

        Existing scene items are retained. If this retrieve finds a scene items
        with the same long name as an existing scene item, it replaces the old one.

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
            solver = mel.eval('zQuery -t "zSolver" -l {}'.format(args[0]))
        else:
            solver = mel.eval('zQuery -t "zSolver" -l')

        # ---------------------------------------------------------------------
        # NODE STORING---------------------------------------------------------
        # ---------------------------------------------------------------------
        if solver:
            solver = solver[0]
        else:
            raise Exception('zSolver not connected to selection.  Please try again.')

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
        sel = cmds.ls(sl=True)

        # args
        if args:
            selection = cmds.ls(args[0], l=True)
        else:
            selection = cmds.ls(sl=True, l=True)

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
                    hist = cmds.listHistory(fibers)
                    nodes.extend(cmds.ls(hist, type='zRivetToBone'))
            if lineOfAction:
                for fiber in mz.get_zFibers(selection):
                    loas = mz.get_fiber_lineofaction(fiber)
                    if loas:
                        nodes.append(loas)
            if restShape:
                cmds.select(selection)
                rest_shapes = mel.eval('zQuery -t zRestShape')
                if rest_shapes:
                    nodes.extend(rest_shapes)
            if embedder:
                cmds.select(selection)
                embedder = mel.eval('zQuery -t "zEmbedder"')
                if embedder:
                    nodes.extend(embedder)
        else:
            nodes = selection

        if nodes:
            self._populate_nodes(nodes, get_parameters=get_parameters)

        cmds.select(sel, r=True)
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
        sel = cmds.ls(sl=True)

        # get stored solver enable value to build later. The solver comes in OFF
        solver_transform = self.get_scene_items(type_filter='zSolverTransform')

        solvers = list()
        if solver:
            solvers.append('zSolver')
            solvers.append('zSolverTransform')

            # build the nodes by calling build method on each one

            for scene_item in self.get_scene_items(type_filter=solvers,
                                                   association_filter=association_filter):
                logger.info('Building: {}'.format(scene_item.type))
                scene_item.build(attr_filter=attr_filter,
                                 permissive=permissive,
                                 interp_maps=interp_maps)

        with SolverDisabler(solver_transform[0].name):

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
            for node_type in node_types_to_build:
                scene_items = self.get_scene_items(type_filter=node_type,
                                                   association_filter=association_filter)
                if scene_items:
                    logger.info('Building: {}'.format(node_type))
                for scene_item in scene_items:
                    scene_item.build(attr_filter=attr_filter,
                                     permissive=permissive,
                                     interp_maps=interp_maps)

        cmds.select(sel, r=True)

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
        list(): Selection list with some items replaced.
    """
    # these are the types we need to find the tissue mesh for.
    type_ = ['zLineOfAction', 'zRivetToBone']

    output = []
    for item in selection:
        if cmds.objectType(item) in type_:
            history = cmds.listHistory(item, future=True)
            fiber = cmds.ls(history, type='zFiber')
            cmds.select(fiber)
            meshes = mel.eval('zQuery -t zTissue -m -l')
            output.append(meshes[0])
        else:
            output.append(item)
    return output


def zQuery(types, solver):
    """ This is a wrapper around Ziva VFX zQuery as currently it does not handle 
    all the queries needed.  This will sort through the types and if given a type that
    zQuery is unfamiliar with it searches solver for it by history instead.
    
    Args:
        types (list() of str()): The types of nodes to get information about
        solver (str()): The solver to query.
    
    Returns:
        list() of str(): 
    """
    return_value = []

    # Full history of solver
    solver_history = cmds.listHistory(solver)

    # Types that are not in ZNODES.  This means that zQuery will not know what to do with it.
    types_not_in_znodes = set(types) - set(ZNODES)
    types_in_znodes = list(set(ZNODES).intersection(set(types)))

    # Dictionary to hold used types not in ZNODES (The actual ones we currently cannot zQuery)
    solver_history_dict = defaultdict(list)

    # Go through the full solver history and put items in a dictionary with type as key.
    for item in solver_history:
        item_type = cmds.objectType(item)
        if item_type in types_not_in_znodes:
            solver_history_dict[item_type].append(item)

    # go through ordered 'types' list and fill up the return_value in a nice ordered manner
    for type_ in types:
        if type_ in types_in_znodes:
            tmp = mel.eval('zQuery -t "{}" -l {}'.format(type_, solver))
            if tmp:
                return_value.extend(tmp)
        else:
            return_value.extend(solver_history_dict[type_])

    return return_value
