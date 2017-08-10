import zBuilder.zMaya as mz

import zBuilder.nodes.base as base
import zBuilder.nodes.zEmbedder as embedderNode


import zBuilder.data.mesh as msh
import zBuilder.data.maps as mps

import zBuilder.nodes as nds

import zBuilder.data as dta
from zBuilder.main import Builder

import maya.cmds as mc
import maya.mel as mm

import logging

logger = logging.getLogger(__name__)


class ZivaSetup(Builder):
    """
    To capture a ziva setup
    """

    def __init__(self):
        Builder.__init__(self)

        for plugin in mc.pluginInfo(query=True, listPluginsPath=True):
            cmds = mc.pluginInfo(plugin, q=True, c=True)
            if cmds:
                if 'ziva' in cmds:
                    plug = plugin.split('/')[-1]
                    continue
                    # self.info['plugin_name'] = plug
                    # self.info['plugin_version'] = mc.pluginInfo(plug,q=True,v=True)

    @Builder.time_this
    def retrieve_from_scene(self, *args, **kwargs):
        # ----------------------------------------------------------------------
        # KWARG PARSING---------------------------------------------------------
        # ----------------------------------------------------------------------
        get_mesh = kwargs.get('get_mesh', True)
        get_maps = kwargs.get('get_maps', True)

        # ----------------------------------------------------------------------
        # NODE STORING----------------------------------------------------------
        # ----------------------------------------------------------------------
        solver = mm.eval('zQuery -t "zSolver" {}'.format(args[0]))[0]
        b_solver = nds.SolverNode(solver)
        solver_transform = mm.eval('zQuery -t "zSolverTransform" {}'.format(solver))
        b_solver_transform = nds.SolverTransformNode(solver_transform)

        self.add_node(b_solver)
        self.add_node(b_solver_transform)


        bones = mm.eval('zQuery -t "zBone" {}'.format(solver))


        for bone in bones:
            b_bone = nds.BoneNode(bone)
            self.add_node(b_bone)

        tets = mm.eval('zQuery -t "zTet" {}'.format(solver))
        tissues = mm.eval('zQuery -t "zTissue" {}'.format(solver))

        map_names = []
        mesh_names = []


        if tets:
            for tet in tets:
                b_tet = nds.TetNode(tet)
                self.add_node(b_tet)
                # TODO ok, so currently I am getting map_name and mesh_name
                # from the object.  Reason is this is not consistent between
                # nodes the mesh needs to correspond with the map in order to
                # get vert info.
                # So, can either figure out a better way to get full map without
                # knowing length OR storing the association between map and mesh
                # in node.  I am creating that link here, not best place.
                map_names.append(b_tet.get_maps()[0])
                mesh_names.append(b_tet.get_association(long_name=True)[0])
        if tissues:
            for tissue in tissues:
                self.add_node(nds.TissueNode(tissue))

        # ----------------------------------------------------------------------
        # MAP AND MESH STORING--------------------------------------------------
        # ----------------------------------------------------------------------
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
            nodes = self.get_nodes(type_filter=node_type)
            for node in nodes:
                node.apply(attr_filter=attr_filter)

    def __apply_bones(self, name_filter=None, attr_filter=None):
        """

        Args:
            attr_filter:

        Returns:

        """
        from zBuilder.nodes.zBone import apply_multiple

        nodes = self.get_nodes(type_filter='zBone', name_filter=name_filter)
        apply_multiple(nodes, attr_filter=attr_filter)



