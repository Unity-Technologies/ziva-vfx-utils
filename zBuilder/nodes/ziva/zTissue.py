from zBuilder.nodes import ZivaBaseNode
import logging
import zBuilder.zMaya as mz

from zBuilder.zMaya import replace_long_name

logger = logging.getLogger(__name__)


class TissueNode(ZivaBaseNode):
    TYPE = 'zTissue'

    def __init__(self, *args, **kwargs):
        ZivaBaseNode.__init__(self, *args, **kwargs)
        self._children_tissues = None
        self._parent_tissue = None

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

    def string_replace(self, search, replace):
        super(TissueNode, self).string_replace(search, replace)

        # name replace----------------------------------------------------------
        parent = self.get_parent_tissue(long_name=True)
        if parent:
            newName = replace_long_name(search, replace, parent)
            self.set_parent_tissue(newName)

        children = self.get_children_tissues(long_name=True)
        if children:
            new_names = list()
            for child in children:
                new_names.append(replace_long_name(search, replace, child))
            self.set_children_tissues(new_names)

    # TODO super this, dont need duplicate code
    def create(self, *args, **kwargs):
        """

        Returns:
            object:
        """

        #logger.info('retrieving {}'.format(args))
        selection = mz.parse_args_for_selection(args)

        self.set_name(selection[0])
        # self.set_type(mz.get_type(selection[0]))
        self.set_attr_list(mz.build_attr_list(selection[0]))
        self.populate_attrs(selection[0])
        self.set_mobject(selection[0])

        mesh = mz.get_association(selection[0])
        self.set_association(mesh)

        # print 'getting maps', self._map_list

        # tmp = []
        # for map_ in self._map_list:
        #     map_name = '{}.{}'.format(selection[0], map_)
        #     tmp.append(map_name)
        # self.set_maps(tmp)

        self.set_children_tissues(mz.get_tissue_children(self.get_scene_name()))
        self.set_parent_tissue(mz.get_tissue_parent(self.get_scene_name()))


