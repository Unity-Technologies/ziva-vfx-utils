from zBuilder.nodes import Ziva
import logging
import zBuilder.zMaya as mz
from maya import cmds
from maya import mel

logger = logging.getLogger(__name__)


class TissueNode(Ziva):
    """ This node for storing information related to zTissues.
    """
    type = 'zTissue'
    """ The type of node. """

    def __init__(self, parent=None, builder=None):
        super(TissueNode, self).__init__(parent=parent, builder=builder)
        self.children_tissues = None
        self.parent_tissue = None

    def populate(self, maya_node=None):
        """ This populates the node given a selection.

        Args:
            maya_node: Maya node to populate with.
        """
        super(TissueNode, self).populate(maya_node=maya_node)

        scene_name = self.get_scene_name()
        self.children_tissues = get_tissue_children(scene_name)
        self.parent_tissue = get_tissue_parent(scene_name)

    def build(self, *args, **kwargs):
        """ Builds the zTissue in maya scene.

        Kwargs:
            attr_filter (dict):  Attribute filter on what attributes to get.
                dictionary is key value where key is node type and value is
                list of attributes to use.

                tmp = {'zSolver':['substeps']}

            interp_maps (str): Interpolating maps.  Defaults to ``auto``
            permissive (bool): Pass on errors. Defaults to ``True``
        """
        solver = None
        if args:
            solver = mel.eval('zQuery -t zSolver {}'.format(args[0]))

        if not solver:
            solver = self.solver

        attr_filter = kwargs.get('attr_filter', list())
        name_filter = kwargs.get('name_filter', list())
        permissive = kwargs.get('permissive', True)
        interp_maps = kwargs.get('interp_maps', 'auto')

        tissue_items = self.builder.get_scene_items(type_filter='zTissue', name_filter=name_filter)
        tet_items = self.builder.get_scene_items(type_filter='zTet', name_filter=name_filter)

        if self is tissue_items[0]:

            # checking if length of tissue_items and tet_items are the same.  If they are not we
            # are not going to build.
            # There is a rare situation where there may be a tet and no tissue and you need
            # to apply the attributes
            assert (len(tissue_items) == len(tet_items)
                    ), 'zTet and zTissue have a different amount.  Not building.'

            build_multiple(tissue_items,
                           tet_items,
                           attr_filter=attr_filter,
                           permissive=permissive,
                           solver=solver,
                           interp_maps=interp_maps)

            # we only want to execute this if tissue_items is empty or self is the first tissue.
            # set the attributes in maya
            for ztet, ztissue in zip(tet_items, tissue_items):
                ztet.set_maya_attrs(attr_filter=attr_filter)
                ztissue.set_maya_attrs(attr_filter=attr_filter)
                ztet.set_maya_weights(interp_maps=interp_maps)


def build_multiple(tissue_items,
                   tet_items,
                   interp_maps='auto',
                   attr_filter=None,
                   permissive=True,
                   solver=None):
    """
    Each node can deal with it's own building.  Though, with zBones it is much
    faster to build them all at once with one command instead of looping
    through them.  This function builds all the zBones at once.

    Args:
        permissive (bool):
        tissue_items:
        tet_items:
        attr_filter (obj):
        solver:
        interp_maps:

    Returns:

    """
    sel = cmds.ls(sl=True)
    # cull none buildable------------------------------------------------------
    tet_results = mz.cull_creation_nodes(tet_items, permissive=permissive)
    tissue_results = mz.cull_creation_nodes(tissue_items, permissive=permissive)

    # build tissues all at once---------------------------------------------
    if tissue_results['meshes']:

        Ziva.check_meshes(tissue_results['meshes'])

        cmds.select(tissue_results['meshes'], r=True)
        outs = mel.eval('ziva -t')

        # rename zTissues and zTets-----------------------------------------
        for new_name, name_in_builder, node in zip(outs[1::4], tissue_results['names'],
                                                   tissue_results['scene_items']):
            node.name = cmds.rename(new_name, name_in_builder)

        for new_name, name_in_builder, node in zip(outs[2::4], tet_results['names'],
                                                   tet_results['scene_items']):
            node.name = cmds.rename(new_name, name_in_builder)

        for ztet, ztissue in zip(tet_items, tissue_items):
            ztet.apply_user_tet_mesh()

            if ztissue.children_tissues:
                """ If there are children lets check if there are parameters for
                them.  If there are none, then lets check scene.
                """
                children_parms = ztissue.builder.get_scene_items(
                    name_filter=ztissue.children_tissues)
                if children_parms:
                    children = [x.association[0] for x in children_parms]
                else:
                    cmds.select(ztissue.children_tissues, r=True)
                    children = mel.eval('zQuery -type zTissue -m ')

                cmds.select(ztissue.association)
                cmds.select(children, add=True)
                mel.eval('ziva -ast')

    cmds.select(sel)


def get_tissue_children(ztissue):
    """ This checks a zTissue if it has children.  Useful for sub-tissues.
    Args:
        ztissue (str): The zTissue object in the maya scene.

    Returns:
        (str) Children mesh of zTissue, or None if none found.
    """
    tmp = []
    if cmds.objectType(ztissue) == 'zTissue':
        child_attr = '{}.oChildTissue'.format(ztissue)
        if cmds.objExists(child_attr):
            children = cmds.listConnections(child_attr)

            if children:
                # sel = cmds.ls(sl=True)
                # cmds.select(children)
                # tmp.extend(mel.eval('zQuery -t zTissue -m -l'))
                # cmds.select(sel)
                return children
    return None


def get_tissue_parent(ztissue):
    """ This checks a zTissue if it has a parent.  Useful for sub-tissues.
    Args:
        ztissue (str): The zTissue object in the maya scene.

    Returns:
        (str) Parent mesh of zTissue, or None if none found
    """
    if cmds.objectType(ztissue) == 'zTissue':
        parent_attr = '{}.iParentTissue'.format(ztissue)
        if cmds.objExists(parent_attr):
            parent = cmds.listConnections(parent_attr)
            if parent:
                # parent = mel.eval('zQuery -t zTissue -m -l')
                return parent[0]
    return None
