import logging
import inspect
import copy

from maya import OpenMaya as om
from maya import cmds
from maya import mel

import zBuilder.zMaya as mz
from zBuilder.nodes.base import Base
from zBuilder.nodes.base import serialize_object

logger = logging.getLogger(__name__)


class DGNode(Base):
    """ The base node for the node functionality of all nodes

    Args:
        builder (object, optional): The builder object for reference.

    Attributes:
        :rtype: :func:`type` (str): type of parameter.  Tied with maya node type.
        attrs (dict): A place for the maya attributes dictionary.

    """
    """ Types of maya nodes this parameter is aware of.  Only needed 
        if parameter can deal with multiple types.  Else leave at None """
    MAP_LIST = []
    """ List of maya node attribute names that represent the paintable map. """
    SEARCH_EXCLUDE = ['_class', 'attrs', '_builder_type', 'type', 'parameters']
    """ A list of attribute names in __dict__ to
            exclude from the string_replace method. """
    EXTEND_ATTR_LIST = list()
    """ List of maya node attribute names to add
            to the auto generated attribute list to include."""

    def __init__(self, parent=None, builder=None):
        super(DGNode, self).__init__(parent=parent, builder=builder)

        self.attrs = {}
        self._association = []

    def __str__(self):
        if self.name:
            name = self.name
            output = ''
            output += '= {} <{} {}> ==================================\n'.format(
                name, self.__class__.__module__, self.__class__.__name__)
            for key in self.__dict__:
                try:
                    output += '\t{} - {}\n'.format(key, self.__dict__[key].__repr__())
                except:
                    output += '\t{} - {}\n'.format(key, self.__dict__[key])

            return output
        return '<%s.%s>' % (self.__class__.__module__, self.__class__.__name__)

    def __repr__(self):
        output = '{}("{}")'.format(self.__class__.__name__, self.name)
        return output

    def __deepcopy__(self, memo):
        # Some attributes cannot be deepcopied so define a listy of attributes
        # to ignore.  These items are zBuilder scene items.  We need to not copy these
        # attributes and apply them to copy afterwards.
        non_copyable_attrs = ['depends_on']
        non_copyable_attrs.extend(Base.SCENE_ITEM_ATTRIBUTES)

        non_copyable_items = {}
        for attr in non_copyable_attrs:
            non_copyable_items[attr] = self.__dict__.get(attr, None)

        result = type(self)()

        for k, v in self.__dict__.items():
            # skip over attributes defined as non-copyable in non_copyable_attrs
            if k not in non_copyable_attrs:
                setattr(result, k, copy.deepcopy(v, memo))

        # Add non-copyable attrs back into scene item manually after it's copied.
        for item in non_copyable_items:
            if item in result.__dict__:
                result.__dict__[item] = non_copyable_items[item]

        return result

    def populate(self, maya_node=None):
        """ Populates the node with the info from the passed maya node in args.

        This is deals with basic stuff including attributes.  For other things it
        is meant to be overridden in inherited node.

        Args:
            maya_node (str): The maya node to populate parameter with.

        """
        self.name = mz.check_maya_node(maya_node)
        self.type = cmds.objectType(self.long_name)
        self.get_maya_attrs()

    def build(self, *args, **kwargs):
        """ Builds the node in maya.  meant to be overwritten.
        """
        raise NotImplementedError

    @property
    def nice_association(self):
        """ if long name exists in the maya scene return it, else return short name
        """
        out = []
        for i, item in enumerate(self._association):
            if cmds.objExists(item):
                out.append(item)
            else:
                out.append(self.association[i])
        return out

    @property
    def association(self):
        """ associations of node.
        """
        tmp = []
        for item in self._association:
            tmp.append(item.split('|')[-1])
        return tmp

    @association.setter
    def association(self, association):
        self._association = cmds.ls(association, long=True)

    @property
    def long_association(self):
        """ Long names of associations.
        """
        return self._association

    def compare(self):
        """ Compares populated parameter with that which is in maya scene.

        Returns:
            prints out items that are different.
        """
        name = self.long_name

        attr_list = self.attrs.keys()
        if cmds.objExists(name):
            if attr_list:
                for attr in attr_list:
                    scene_val = cmds.getAttr(name + '.' + attr)
                    obj_val = self.attrs[attr]['value']
                    if scene_val != obj_val:
                        print('DIFF:', name + '.' + attr, '\tobject value:', obj_val,
                              '\tscene value:', scene_val)

    def get_scene_name(self, long_name=False):
        """This returns either long name or short name.

        Args:
            long_name (bool): Return the fullpath or not. Defaults to False.

        Returns:
            (str) Name of maya object.
        """
        name = self.long_name

        if not long_name:
            name = name.split('|')[-1]

        return name

    def get_maya_attrs(self):
        """ Get attribute values from maya and update self.
        """

        # build the attribute list to aquire from scene
        attr_list = mz.build_attr_list(self.long_name)
        if self.EXTEND_ATTR_LIST:
            attr_list.extend(self.EXTEND_ATTR_LIST)

        # with attribute list, get values in dictionary format and update node.
        self.attrs = mz.build_attr_key_values(self.long_name, attr_list)

    def set_maya_attrs(self, attr_filter=None):
        """Given a Builder node this set the attributes of the object in the maya
        scene. 

        Args:
            attr_filter (dict):  Attribute filter on what attributes to set.
                dictionary is key value where key is node type and value is
                list of attributes to use.

                af = {'zSolver':['substeps']}

        Returns:
            nothing.
        """
        scene_name = self.get_scene_name()

        type_ = self.type
        node_attrs = self.attrs.keys()
        if attr_filter:
            if attr_filter.get(type_, None):
                node_attrs = list(set(node_attrs).intersection(attr_filter[type_]))

        for attr in node_attrs:
            if self.attrs[attr]['type'] == 'doubleArray':
                if cmds.objExists('{}.{}'.format(scene_name, attr)):
                    if not cmds.getAttr('{}.{}'.format(scene_name, attr), l=True):
                        cmds.setAttr('{}.{}'.format(scene_name, attr),
                                     self.attrs[attr]['value'],
                                     type='doubleArray')
                else:
                    text = '{}.{} not found, skipping.'.format(scene_name, attr)
                    logger.info(text)
            else:
                if cmds.objExists('{}.{}'.format(scene_name, attr)):
                    if not cmds.getAttr('{}.{}'.format(scene_name, attr), l=True):
                        try:
                            cmds.setAttr('{}.{}'.format(scene_name, attr),
                                         self.attrs[attr]['value'])
                        except:
                            pass
                else:
                    text = '{}.{} not found, skipping.'.format(scene_name, attr)
                    logger.info(text)

            # check the alias
            if cmds.objExists('{}.{}'.format(scene_name, attr)):
                alias = self.attrs[attr].get('alias', None)
                if alias:
                    try:
                        cmds.aliasAttr(alias, '{}.{}'.format(scene_name, attr))
                    except RuntimeError:
                        pass
