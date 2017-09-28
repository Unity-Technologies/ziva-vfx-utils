from zBuilder.nodes import ZivaBaseNode
import logging
import zBuilder.zMaya as mz
import maya.cmds as mc
import maya.mel as mm

logger = logging.getLogger(__name__)


class TissueNode(ZivaBaseNode):
    TYPE = 'zTissue'

    def __init__(self, *args, **kwargs):
        self._children_tissues = None
        self._parent_tissue = None

        ZivaBaseNode.__init__(self, *args, **kwargs)

    # TODO property and store zTissue instead of mesh for parents and childs
    def set_children_tissues(self, children):
        self._children_tissues = children

    def set_parent_tissue(self, parent):
        self._parent_tissue = parent

    def get_children_tissues(self, long_name=False):
        if not long_name:
            tmp = []
            if self._children_tissues:
                for item in self._children_tissues:
                    tmp.append(item.split('|')[-1])
                return tmp
            else:
                return None
        else:
            return self._children_tissues

    def get_parent_tissue(self, long_name=False):
        if self._parent_tissue:
            if long_name:
                return self._parent_tissue
            else:
                return self._parent_tissue.split('|')[-1]
        else:
            return None


    # TODO super this, dont need duplicate code
    def populate(self, *args, **kwargs):
        """

        Returns:
            object:
        """

        # logger.info('retrieving {}'.format(args))
        selection = mz.parse_args_for_selection(args)

        self.name = selection[0]
        self.type = mz.get_type(selection[0])
        self.set_attr_list(mz.build_attr_list(selection[0]))
        self.populate_attrs(selection[0])
        self.mobject = selection[0]

        mesh = mz.get_association(selection[0])
        self.association = mesh

        self.set_children_tissues(mz.get_tissue_children(self.get_scene_name()))
        self.set_parent_tissue(mz.get_tissue_parent(self.get_scene_name()))

    def apply(self, *args, **kwargs):
        attr_filter = kwargs.get('attr_filter', None)
        name_filter = kwargs.get('name_filter', None)
        permissive = kwargs.get('permissive', True)
        check_meshes = kwargs.get('check_meshes', True)

        b_nodes = self._setup.get_nodes(type_filter='zTissue',
                                        name_filter=name_filter)

        if self == b_nodes[0]:
            apply_multiple(b_nodes, attr_filter=attr_filter,
                           permissive=permissive, check_meshes=check_meshes)


def apply_multiple(b_nodes, attr_filter=None, permissive=True,
                   check_meshes=True):
    """
    Each node can deal with it's own building.  Though, with zBones it is much
    faster to build them all at once with one command instead of looping
    through them.  This function builds all the zBones at once.

    Args:
        check_meshes:
        permissive (bool):
        b_nodes:
        attr_filter (obj):

    Returns:

    """
    sel = mc.ls(sl=True)
    # cull none buildable-------------------------------------------------------
    culled = mz.cull_creation_nodes(b_nodes, permissive=permissive)

    # check mesh quality--------------------------------------------------------
    if check_meshes:
        mz.check_mesh_quality(culled['meshes'])

    # build tissues all at once-------------------------------------------------
    results = None
    if culled['meshes']:
        mc.select(culled['meshes'], r=True)
        results = mm.eval('ziva -t')

    # rename zBones-------------------------------------------------------------
    if results:
        results = mc.ls(results, type='zTissue')

        for new, name, b_node in zip(results, culled['names'], culled['b_nodes']):
            b_node.mobject = new
            mc.rename(new, name)

    # set the attributes
    for b_node in b_nodes:
        b_node.set_maya_attrs(attr_filter=attr_filter)

    mc.select(sel)
