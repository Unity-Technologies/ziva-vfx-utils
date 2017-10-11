from zBuilder.parameters import ZivaBaseParameter
import logging
import zBuilder.zMaya as mz
import maya.cmds as mc
import maya.mel as mm

logger = logging.getLogger(__name__)


class TissueNode(ZivaBaseParameter):
    """ This node for storing information related to zTissues.
    """
    type = 'zTissue'
    """ The type of node. """

    def __init__(self, *args, **kwargs):
        self._children_tissues = None
        self._parent_tissue = None

        ZivaBaseParameter.__init__(self, *args, **kwargs)

    # TODO property and store zTissue instead of mesh for parents and childs
    def set_children_tissues(self, children):
        """ Stores children tissues.
        Args:
            children: The children tissues to store.
        """
        self._children_tissues = children

    def set_parent_tissue(self, parent):
        """ Stores parent tissues.
        Args:
            children: The parent tissues to store.
        """
        self._parent_tissue = parent

    def get_children_tissues(self, long_name=False):
        """ Get children tissues.
        Args:
            long_name: return long name or not.  Defaults to ``False``

        Returns:
            list of str: list of children tissues.

        """
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
        """ Get parent tissues.
        Args:
            long_name: return long name or not.  Defaults to ``False``

        Returns:
            list of str: list of parent tissues.

        """
        if self._parent_tissue:
            if long_name:
                return self._parent_tissue
            else:
                return self._parent_tissue.split('|')[-1]
        else:
            return None

    def populate(self, *args, **kwargs):
        """ This extends ZivaBase.populate()

        Adds parent and child storage.

        Args:
            *args: Maya node to populate with.
        """
        super(TissueNode, self).populate(*args, **kwargs)

        self.set_children_tissues(mz.get_tissue_children(self.get_scene_name()))
        self.set_parent_tissue(mz.get_tissue_parent(self.get_scene_name()))

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
        attr_filter = kwargs.get('attr_filter', list())
        name_filter = kwargs.get('name_filter', list())
        permissive = kwargs.get('permissive', True)
        check_meshes = kwargs.get('check_meshes', True)

        b_nodes = self._setup.get_parameters(type_filter='zTissue',
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
