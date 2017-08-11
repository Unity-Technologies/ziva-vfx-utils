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
        # TODO a way to instantiate a b_node based on maya node type.  Lookup?
        # This way I would just need to query solver then from there maintain
        # a list of node types and classes.  Then, just pass the node and have
        # the correct class instantiate.
        solver = mm.eval('zQuery -t "zSolver" {}'.format(args[0]))[0]
        b_solver = nds.SolverNode().create(solver)
        solver_transform = mm.eval('zQuery -t "zSolverTransform" {}'.format(solver))
        b_solver_transform = nds.SolverTransformNode().create(solver_transform)

        self.add_node(b_solver)
        self.add_node(b_solver_transform)

        bones = mm.eval('zQuery -t "zBone" {}'.format(solver))

        if bones:
            for bone in bones:
                b_bone = nds.BoneNode().create(bone)
                self.add_node(b_bone)

        tets = mm.eval('zQuery -t "zTet" {}'.format(solver))
        if tets:
            for tet in tets:
                b_tet = nds.TetNode().create(tet)
                self.add_node(b_tet)
                # TODO ok, so currently I am getting map_name and mesh_name
                # from the object.  Reason is this is not consistent between
                # nodes the mesh needs to correspond with the map in order to
                # get vert info.
                # So, can either figure out a better way to get full map without
                # knowing length OR storing the association between map and mesh
                # in node.  I am creating that link here, not best place.
                map_names.extend(b_tet.get_maps())
                mesh_names.extend(b_tet.get_association(long_name=True))

        tissues = mm.eval('zQuery -t "zTissue" {}'.format(solver))
        if tissues:
            for tissue in tissues:
                self.add_node(nds.TissueNode().create(tissue))

        clothes = mm.eval('zQuery -t "zCloth" {}'.format(solver))
        if clothes:
            for cloth in clothes:
                self.add_node(nds.ClothNode().create(cloth))

        materials = mm.eval('zQuery -t "zMaterial" {}'.format(solver))
        if materials:
            for material in materials:
                b_material = nds.MaterialNode().create(material)
                self.add_node(b_material)
                map_names.extend(b_material.get_maps())
                mesh_names.extend(b_material.get_association(long_name=True))

        attachments = mm.eval('zQuery -t "zAttachment" {}'.format(solver))
        if attachments:
            for attachment in attachments:
                b_attachment = nds.AttachmentNode().create(attachment)
                self.add_node(b_attachment)
                map_names.extend(b_attachment.get_maps())
                mesh_names.extend(b_attachment.get_association(long_name=True))

        fibers = mm.eval('zQuery -t "zFiber" {}'.format(solver))
        if fibers:
            for fiber in fibers:
                b_fiber = nds.FiberNode().create(fiber)
                self.add_node(b_fiber)
                map_names.extend(b_fiber.get_maps())
                mesh_name = b_fiber.get_association(long_name=True)
                mesh_names.append([mesh_name, mesh_name])

        embedder = mm.eval('zQuery -t "zEmbedder" {}'.format(solver))
        if embedder:
            b_embedder = nds.EmbedderNode().create(embedder)
            self.add_node(b_embedder)

        # line_of_actions = mm.eval('zQuery -t "zLineOfAction" {}'.format(solver))
        # if line_of_actions:
        #     for line_of_action in line_of_actions:
        #         self.add_node(nds.LineOfActionNode().create(line_of_action))

        # ----------------------------------------------------------------------
        # MAP AND MESH STORING--------------------------------------------------
        # ----------------------------------------------------------------------
        # TODO so at this level this could be much simpler.  Maybe wrap this
        # up so it works on a b_node.  Pass the list of b_nodes and it looks up
        # to see what maps/meshes it needs to store.  Would be 2 lines
        # better?  not sure.  More obfuscated? ya  shorter?  yes
        for map_name, mesh_name in zip(map_names, mesh_names):

            if get_maps:
                map_data_object = dta.Map(map_name=map_name, mesh_name=mesh_name)
                self.add_data('map', map_name, data=map_data_object)

            if get_mesh:
                if not self.get_data_by_key_name('mesh', mesh_name):
                    mesh_data_object = msh.Mesh(mesh_name=mesh_name)
                    self.add_data('mesh', mesh_name, data=mesh_data_object)

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
