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

        Args:
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
        check_meshes = kwargs.get('check_meshes', True)

        parameters = self.builder.bundle.get_scene_items(type_filter='zTissue',
                                                         name_filter=name_filter)

        if self == parameters[0]:
            apply_multiple(parameters, attr_filter=attr_filter,
                           permissive=permissive, check_meshes=check_meshes,
                           solver=solver)


def apply_multiple(parameters, attr_filter=None, permissive=True,
                   check_meshes=True, solver=None):
    """
    Each node can deal with it's own building.  Though, with zBones it is much
    faster to build them all at once with one command instead of looping
    through them.  This function builds all the zBones at once.

    Args:
        check_meshes:
        permissive (bool):
        parameters:
        attr_filter (obj):

    Returns:

    """
    sel = mc.ls(sl=True)
    # cull none buildable-------------------------------------------------------
    culled = mz.cull_creation_nodes(parameters, permissive=permissive)

    # check mesh quality--------------------------------------------------------
    if check_meshes:
        mz.check_mesh_quality(culled['meshes'])

    # build tissues all at once-------------------------------------------------
    results = None
    if culled['meshes']:

        mc.select(culled['meshes'], r=True)
        # if solver:
        #     mc.select(solver, add=True)
        results = mm.eval('ziva -t ')

    # rename zBones-------------------------------------------------------------
    if results:
        results = mc.ls(results, type='zTissue')

        for new, name, parameter in zip(results, culled['names'], culled['parameters']):
            parameter.mobject = new
            mc.rename(new, name)

    # set the attributes
    for parameter in parameters:
        parameter.set_maya_attrs(attr_filter=attr_filter)

        # add subtissues--------------------------------------------------------
        if parameter.children_tissues:
            children_parms = parameter.setup.bundle.get_scene_items(name_filter=parameter.children_tissues)
            mc.select(parameter.association)
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
