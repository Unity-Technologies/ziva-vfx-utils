from zBuilder.nodes import Ziva
import logging
import zBuilder.zMaya as mz
import maya.cmds as mc
import maya.mel as mm

logger = logging.getLogger(__name__)


class TissueNode(Ziva):
    """ This node for storing information related to zTissues.
    """
    type = 'zTissue'
    """ The type of node. """

    def __init__(self, *args, **kwargs):
        self.children_tissues = None
        self.parent_tissue = None

        Ziva.__init__(self, *args, **kwargs)

    def populate(self, maya_node=None):
        """ This populates the node given a selection.

        Args:
            maya_node: Maya node to populate with.
        """
        super(TissueNode, self).populate(maya_node=maya_node)

        self.children_tissues = get_tissue_children(self.get_scene_name())
        self.parent_tissue = get_tissue_parent(self.get_scene_name())

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
            solver = mm.eval('zQuery -t zSolver {}'.format(args[0]))

        if not solver:
            solver = self.solver

        attr_filter = kwargs.get('attr_filter', list())
        name_filter = kwargs.get('name_filter', list())
        permissive = kwargs.get('permissive', True)
        interp_maps = kwargs.get('interp_maps', 'auto')

        tissue_items = self.builder.get_scene_items(type_filter='zTissue',
                                                    name_filter=name_filter)
        tet_items = self.builder.get_scene_items(type_filter='zTet',
                                                 name_filter=name_filter)

        if self == tissue_items[0]:
            build_multiple(tissue_items, tet_items,
                           attr_filter=attr_filter,
                           permissive=permissive,
                           solver=solver,
                           interp_maps=interp_maps)


def build_multiple(tissue_items, tet_items, interp_maps='auto',
                   attr_filter=None, permissive=True, solver=None):
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
    sel = mc.ls(sl=True)
    # cull none buildable-------------------------------------------------------
    tet_results = mz.cull_creation_nodes(tet_items, permissive=permissive)
    tissue_results = mz.cull_creation_nodes(tissue_items, permissive=permissive)

    # build tissues all at once---------------------------------------------
    if tissue_results['meshes']:
        mc.select(tissue_results['meshes'], r=True)
        outs = mm.eval('ziva -t')

        # rename zTissues and zTets-----------------------------------------
        for new, name, node in zip(outs[1::4], tissue_results['names'],
                                   tissue_results['parameters']):
            node.mobject = new
            mc.rename(new, name)

        for new, name, node in zip(outs[2::4], tet_results['names'],
                                   tet_results['parameters']):
            node.mobject = new
            mc.rename(new, name)

        for ztet, ztissue in zip(tet_items, tissue_items):

            # set the attributes in maya
            ztet.set_maya_attrs(attr_filter=attr_filter)
            ztissue.set_maya_attrs(attr_filter=attr_filter)
            ztet.set_maya_weights(interp_maps=interp_maps)

            ztet.apply_user_tet_mesh()

            if ztissue.children_tissues:
                    children_parms = ztissue.builder.get_scene_items(name_filter=ztissue.children_tissues)
                    mc.select(ztissue.association)
                    mc.select([x.association[0] for x in children_parms], add=True)
                    mm.eval('ziva -ast')

    mc.select(sel)


def get_tissue_children(ztissue):
    """ This checks a zTissue if it has children.  Useful for sub-tissues.
    Args:
        ztissue (str): The zTissue object in the maya scene.

    Returns:
        (str) Children mesh of zTissue, or None if none found.
    """
    tmp = []
    if mc.objectType(ztissue) == 'zTissue':
        child_attr = '{}.oChildTissue'.format(ztissue)
        if mc.objExists(child_attr):
            children = mc.listConnections(child_attr)

            if children:
                # sel = mc.ls(sl=True)
                # mc.select(children)
                # tmp.extend(mm.eval('zQuery -t zTissue -m -l'))
                # mc.select(sel)
                return children
    return None


def get_tissue_parent(ztissue):
    """ This checks a zTissue if it has a parent.  Useful for sub-tissues.
    Args:
        ztissue (str): The zTissue object in the maya scene.

    Returns:
        (str) Parent mesh of zTissue, or None if none found
    """
    if mc.objectType(ztissue) == 'zTissue':
        parent_attr = '{}.iParentTissue'.format(ztissue)
        if mc.objExists(parent_attr):
            parent = mc.listConnections(parent_attr)
            if parent:
                # parent = mm.eval('zQuery -t zTissue -m -l')
                return parent[0]
    return None
