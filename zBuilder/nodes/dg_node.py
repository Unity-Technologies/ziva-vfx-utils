import logging

from maya import cmds
from zBuilder.utils.commonUtils import get_first_element
from zBuilder.utils.mayaUtils import get_short_name, build_attr_list, build_attr_key_values, get_type
from .base import Base

logger = logging.getLogger(__name__)


class DGNode(Base):
    """ The base node for the node functionality of all nodes

    Args:
        builder (object, optional): The builder object for reference.

    Attributes:
        :rtype: :func:`type` (str): type of parameter.  Tied with maya node type.
        attrs (dict): A place for the maya attributes dictionary.

    """

    # List of maya node attribute names that represent the paintable map.
    MAP_LIST = []

    # This is an inherited class attribute.
    SEARCH_EXCLUDE = Base.SEARCH_EXCLUDE + [
        'parameters',
    ]

    # List of maya node attribute names to add to the auto generated attribute list to include.
    EXTEND_ATTR_LIST = list()

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

    def post_populate(self):
        """ Callback function that is called after populate() function returns successfully.
        """
        pass

    def do_post_build(self):
        """ Callback function that is called after the build() function.  
        """
        pass

    def populate(self, maya_node=None):
        """ Populates the node with the info from the passed maya node in args.

        This deals with basic stuff including attributes.
        For other things it is meant to be overridden in inherited node.

        Args:
            maya_node (str): The maya node to populate parameter with.
        """
        self.name = get_first_element(maya_node)
        self.type = get_type(self.long_name)
        self.get_maya_attrs()

    def do_build(self, *args, **kwargs):
        """ Builds the node in maya.
        This is a virtual function that must be overriden by derive node class.
        It will be called by each Builder's build() method to set attribte values to the node.
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
        return [get_short_name(item) for item in self._association]

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
            Prints out items that are different.
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

    def get_maya_attrs(self):
        """ Get attribute values from maya and update self.
        """
        # build the attribute list to aquire from scene
        attr_list = build_attr_list(self.long_name)
        if self.EXTEND_ATTR_LIST:
            attr_list.extend(self.EXTEND_ATTR_LIST)

        # with attribute list, get values in dictionary format and update node.
        self.attrs = build_attr_key_values(self.long_name, attr_list)

    def set_maya_attrs(self):
        """ Given a Builder node this set the attributes of the object in the maya scene.
        """
        for attr in self.attrs.keys():
            node_dot_attr = '{}.{}'.format(self.name, attr)
            if not cmds.objExists(node_dot_attr):
                logger.info('{} not found, skipping.'.format(node_dot_attr))
                continue

            # Skip locked or connected attributes
            if cmds.getAttr(node_dot_attr, settable=True):
                try:
                    cmds.setAttr(node_dot_attr,
                                 self.attrs[attr]['value'],
                                 type=self.attrs[attr]['type'])
                except RuntimeError:
                    # setAttr() throws when attr type is bool, double, or other types.
                    # For such case, call setAttr() again w/o specifying type should make it work.
                    try:
                        cmds.setAttr(node_dot_attr, self.attrs[attr]['value'])
                    except RuntimeError:
                        # Unfortunately, in the Maya field nodes unit test,
                        # when retrieving Maya DragField node attr list,
                        # its maxDistance attr returns -1.0, not minimum value 0.
                        # When setting "dragField1.maxDistance" attr during do_build() operation,
                        # it first throws exception:
                        # RuntimeError: setAttr: The type 'doubleLinear' is not the name of a recognized type.
                        # This makes sense. But after invoking setAttr() again with -1.0 value,
                        # it throw another exception:
                        # RuntimeError: setAttr: Cannot set the attribute 'dragField1.maxDistance' below its minimum value of 0.
                        # If we want to prevent this problem, we need to verify attr type and its min/max range,
                        # in the build_attr_key_values() function.
                        # That imposes extra work in our code for Maya's bug.
                        # The easiest solution is mute this error and skip setting this attr value.
                        # The downside is it also mutes any our errors.
                        pass
