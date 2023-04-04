from maya import cmds
from zBuilder.utils.mayaUtils import safe_rename
from zBuilder.utils.vfxUtils import cull_creation_nodes
from .zivaBase import Ziva


class TissueNode(Ziva):
    """ This node for storing information related to zTissues.
    """
    type = 'zTissue'

    def __init__(self, parent=None, builder=None):
        super(TissueNode, self).__init__(parent=parent, builder=builder)
        self.children_tissues = None
        self.parent_tissue = None
        # parent_tissues and children_tissues are used to define sub-tissues.
        # This is storing the scene_item for the respective tissue.
        # The parent tissue is the one that gets filled and the children_tissues are unused.
        # The reason for this is because at time of retrieval
        # the children tissues are not processed so their are no children scene items to get.

    def make_node_connections(self):
        """ Adding connections for zTissue.
        This is assiging any parent_tissues to this scene item.
        parent_tissues are its parent sub-tissue.
        """
        parent_name = get_tissue_parent(self.name)
        if parent_name:
            temp = self.builder.get_scene_items(name_filter=parent_name)
            if temp:
                self.parent_tissue = temp[0]

    def do_build(self, *args, **kwargs):
        """ Builds the zTissue in maya scene.

        Kwargs:
            interp_maps (str): Interpolating maps.  Defaults to ``auto``
            permissive (bool): Pass on errors. Defaults to ``True``
        """
        solver = None
        if args:
            solver = cmds.zQuery(args[0], t='zSolver', l=True)

        if not solver:
            solver = self.solver

        permissive = kwargs.get('permissive', True)
        interp_maps = kwargs.get('interp_maps', 'auto')

        tissue_items = self.builder.get_scene_items(type_filter='zTissue')
        tet_items = self.builder.get_scene_items(type_filter='zTet')

        if self is tissue_items[0]:

            # checking if length of tissue_items and tet_items are the same.  If they are not we
            # are not going to build.
            # There is a rare situation where there may be a tet and no tissue and you need
            # to apply the attributes
            assert (len(tissue_items) == len(tet_items)
                    ), 'zTet and zTissue have a different amount.  Not building.'

            self.build_multiple()

            # we only want to execute this if tissue_items is empty or self is the first tissue.
            # set the attributes in maya
            for ztet, ztissue in zip(tet_items, tissue_items):
                ztet.check_parameter_name()

                ztet.set_maya_attrs()
                ztissue.set_maya_attrs()
                ztet.set_maya_weights(interp_maps=interp_maps)

    def build_multiple(self):
        """
        Each node can deal with it's own building. Though, with zTissues it is much
        faster to build them all at once with one command instead of looping
        through them.  This function builds all the zTissue at once.
        """
        sel = cmds.ls(sl=True)
        tissue_items = self.builder.get_scene_items(type_filter='zTissue')
        tet_items = self.builder.get_scene_items(type_filter='zTet')

        # cull none buildable------------------------------------------------------
        tet_results = cull_creation_nodes(tet_items)
        tissue_results = cull_creation_nodes(tissue_items)

        # build tissues all at once---------------------------------------------
        if tissue_results['meshes']:
            Ziva.check_meshes(tissue_results['meshes'])

            cmds.select(tissue_results['meshes'], r=True)
            outs = cmds.ziva(t=True)
            # when creating a zTissue here we are using the ziva(t=True) command.  This
            # creates a zTissue, zTet and zMaterial.  We need to make sure that they
            # are named based on zBuilder data right after.  It is easier changing it here
            # when needed then to check and deal with it later.
            # rename zTissue
            for new_name, builder_name, node in zip(outs[1::4], tissue_results['names'],
                                                    tissue_results['scene_items']):
                safe_rename(new_name, builder_name)

            # rename zTet
            for new_name, builder_name, node in zip(outs[2::4], tet_results['names'],
                                                    tet_results['scene_items']):
                safe_rename(new_name, builder_name)

            # rename zMaterial
            for new_name, node in zip(outs[3::4], tissue_results['scene_items']):
                mesh = node.association
                for material in self.builder.get_scene_items(type_filter='zMaterial'):
                    if material.association == mesh:
                        safe_rename(new_name, material.name)
                        break

            for ztet, ztissue in zip(tet_items, tissue_items):
                ztet.apply_user_tet_mesh()
                if ztissue.parent_tissue:
                    parent_name = ztissue.parent_tissue.name
                    parent_scene_item = ztissue.builder.get_scene_items(name_filter=parent_name)
                    if parent_scene_item:
                        parent = [x.nice_association[0] for x in parent_scene_item]
                    else:
                        cmds.select(ztissue.parent_tissue.long_name, r=True)
                        parent = cmds.zQuery(type='zTissue', mesh=True)

                    cmds.select(parent)
                    tissue_mesh = ztissue.nice_association[0]
                    cmds.select(tissue_mesh, add=True)
                    cmds.ziva(addSubtissue=True)

        cmds.select(sel)


def get_tissue_children(ztissue):
    """ This checks a zTissue if it has children.  Useful for sub-tissues.
    Args:
        ztissue (str): The zTissue object in the maya scene.

    Returns:
        (str) Children mesh of zTissue, or None if none found.
    """

    child_attr = '{}.oChildTissue'.format(ztissue)
    children = cmds.listConnections(child_attr)

    if children:
        return children
    return None


def get_tissue_parent(ztissue):
    """ This checks a zTissue if it has a parent.  Useful for sub-tissues.
    Args:
        ztissue (str): The zTissue object in the maya scene.

    Returns:
        (str) Parent mesh of zTissue, or None if none found
    """
    parent_attr = '{}.iParentTissue'.format(ztissue)
    parent = cmds.listConnections(parent_attr)
    if parent:
        return parent[0]
    return None
