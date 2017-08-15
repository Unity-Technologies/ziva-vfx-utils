import logging

import maya.OpenMaya as om
import maya.cmds as mc
import maya.mel as mm
import zBuilder.zMaya as mz

logger = logging.getLogger(__name__)


class BaseNode(object):
    TYPE = None
    MAP_LIST = []

    def __init__(self, *args, **kwargs):
        """

        Returns:
            object: 
        """
        self._attr_list = []

        self._name = None
        self._attrs = {}
        self._maps = {}
        self._association = []

        self._class = (self.__class__.__module__, self.__class__.__name__)

        if args:
            self.create(args[0])

    def __str__(self):
        if self.get_name():
            name = self.get_name()
            output = ''
            output += '= {} ====================================\n'.format(name)
            for key in self.__dict__:
                output += '\t{} - {}\n'.format(key, self.__dict__[key])

            return output
        return '<%s.%s>' % (self.__class__.__module__, self.__class__.__name__)

    def __repr__(self):
        return self.__str__()

    def serialize(self):
        """
        This replaces an mObject with the name of the object in scene to make it
        serializable for writing out to json.

        Returns:
            nothing
        """
        if self.__mobject:
            print 'serialize: ', self.__mobject
            self.__mobject = mz.get_name_from_m_object(self.__mobject)

    def unserialize(self):
        """
        For now this sets the mobject with the string that is there now.

        Returns:

        """
        self.set_mobject(self.get_mobject())
        print 'unserialize: ', self.get_mobject()


    # def __setattr__(self, key, value):
    #     try:
    #         json.dumps(value)
    #         tmp = {}
    #         tmp[key] = value
    #         # object.__setattr__(self, self._serialize, tmp)
    #     except TypeError:
    #         pass
    #
    #     # print self._serialize
    #     object.__setattr__(self, key, value)

    def create(self, *args, **kwargs):
        """

        Returns:
            object:
        """
        # logger.info('retrieving {}'.format(args))
        selection = mz.parse_args_for_selection(args)

        self.set_name(selection[0])
        self.set_type(mc.objectType(selection[0]))
        self.set_attr_list(mz.build_attr_list(selection[0]))
        self.populate_attrs(selection[0])
        self.set_mobject(selection[0])

        return self

    def print_(self):
        print self

    def string_replace(self, search, replace):
        # name replace----------------------------------------------------------
        name = self.get_name(long_name=True)
        new_name = mz.replace_long_name(search, replace, name)
        self.set_name(new_name)

        # association replace---------------------------------------------------
        ass_names = self.get_association(long_name=True)
        new_names = []
        if ass_names:
            for name in ass_names:
                new_name = mz.replace_long_name(search, replace, name)
                new_names.append(new_name)
            self.set_association(new_names)

        # maps-------------------------------------------------------------------
        maps = self.get_maps()
        tmp = []
        if maps:
            for item in maps:
                tmp.append(mz.replace_long_name(search, replace, item))
            self.set_maps(tmp)

    def get_attr_value(self, attr):
        """
        gets value of an attribute in node

        Args:
            attr (str): The attribute to get value of

        Returns:
            value of attribute
        """
        return self._attrs[attr]['value']

    def set_attr_value(self, attr, value):
        """
        sets value of an attribute in node

        Args:
            attr (str): The attribute to get value of
            value : the value to set
        """
        self._attrs[attr]['value'] = value

    def get_attr_list(self):
        """
        gets list of attribute names stored with node

        Returns:
            [] of attribute names
        """
        return self._attr_list

    def set_attr_list(self, attrs):

        self._attr_list = attrs

    def get_attr_key(self, key):
        return self._attrs.get(key)

    def get_attr_key_value(self, attr, key):
        return self._attrs[attr][key]

    def set_attr_key_value(self, attr, key, value):
        self._attrs[attr][key] = value

    def get_name(self, long_name=False):
        """
        get name of node

        Args:
            long_name (bool): If True returns the long name of node.  Defaults to **False**

        Returns:
            (str) of node name
        """
        if self._name:
            if long_name:
                return self._name
            else:
                return self._name.split('|')[-1]
        else:
            return None

    def set_name(self, name):
        """
        Sets name of node

        Args:
            name (str): the name of node.
        """
        self._name = name
    @classmethod
    def get_type(cls):
        """
        get type of node

        Returns:
            (str) of node name
        """
        try:
            return cls.TYPE
        except AttributeError:
            return None

    def set_type(self, type_):
        """
        Sets type of node

        Args:
            type_ (str): the type of node.
        """
        self._type = type_

    def get_maps(self):
        return self._maps

    def set_maps(self, maps):
        self._maps = maps

    def set_attrs(self, attrs):
        # TODO explicit set 
        self._attrs = attrs

    def populate_attrs(self, item):
        attr_list = self.get_attr_list()
        attrs = mz.build_attr_key_values(item, attr_list)
        self.set_attrs(attrs)

    def get_association(self, long_name=False):
        if not long_name:
            tmp = []
            for item in self._association:
                tmp.append(item.split('|')[-1])
            return tmp
        else:
            return self._association

    def set_association(self, association):

        if isinstance(association, str):
            self._association = [association]
        else:
            self._association = association

    def compare(self):
        name = self.get_name(long_name=False)

        attr_list = self.get_attr_list()
        if mc.objExists(name):
            if attr_list:
                for attr in attr_list:
                    scene_val = mc.getAttr(name + '.' + attr)
                    obj_val = self.get_attr_key_value(attr, 'value')
                    if scene_val != obj_val:
                        print 'DIFF:', name + '.' + attr, '\tobject value:', obj_val, '\tscene value:', scene_val

    def get_scene_name(self, long_name=True):
        """
        This checks stored mObject and gets name of object in scene.  If no
        mObject it returns node name.

        Args:
            long_name (bool): Return the fullpath or not.  Defaults to True.

        Returns:
            (str) Name of maya object.
        """
        name = None
        if self.get_mobject():
            name = mz.get_name_from_m_object(self.get_mobject())

        if not name:
            name = self.get_name(long_name=long_name)

        return name

    def set_maya_attrs(self, attr_filter=None):
        """
        Given a Builder node this set the attributes of the object in the maya
        scene.  It first does a mObject check to see if it has been tracked, if
        it has it uses that instead of stored name.
        Args:
            attr_filter (dict):  Attribute filter on what attributes to set.
                dictionary is key value where key is node type and value is
                list of attributes to use.

                af = {'zSolver':['substeps']}
        Returns:
            nothing.
        """
        scene_name = self.get_scene_name()

        type_ = self.get_type()
        node_attrs = self.get_attr_list()
        if attr_filter:
            if attr_filter.get(type_, None):
                node_attrs = list(
                    set(node_attrs).intersection(attr_filter[type_]))

        for attr in node_attrs:
            if self.get_attr_key('type') == 'doubleArray':
                if mc.objExists(scene_name + '.' + attr):
                    if not mc.getAttr(scene_name + '.' + attr, l=True):
                        mc.setAttr(scene_name + '.' + attr,
                                   self.get_attr_value(attr),
                                   type='doubleArray')
                else:
                    print scene_name + '.' + attr + ' not found, skipping'
            else:
                if mc.objExists(scene_name + '.' + attr):
                    if not mc.getAttr(scene_name + '.' + attr, l=True):
                        try:
                            mc.setAttr(scene_name + '.' + attr,
                                       self.get_attr_value(attr))
                        except:
                            pass
                else:
                    print scene_name + '.' + attr + ' not found, skipping'

    def set_maya_weights(self, interp_maps=False):
        """
        Given a Builder node this set the map values of the object in the maya
        scene.  It first does a mObject check to see if it has been tracked, if
        it has it uses that instead of stored scene_name.

        Args:
            b_node (object):  The Builder node with the stored map to be applied
                in scene.
            interp_maps (str): Do you want maps interpolated?
                True forces interpolation.
                False cancels it.
                auto checks if it needs to.  Default = "auto"

        Returns:
            nothing.
        """
        maps = self.get_maps()
        scene_name = self.get_scene_name()
        original_name = self.get_name()
        created_mesh = None

        for map_ in maps:
            # TODO bah, mesh needs to be here!
            map_data = self.get_data_by_key_name('map', map_)
            mesh_data = self.get_data_by_key_name('mesh', map_data.get_mesh(
                long_name=True))
            mesh_name_short = mesh_data.get_name(long_name=False)
            weight_list = map_data.get_value()

            if mc.objExists(mesh_name_short):
                if interp_maps == 'auto':
                    cur_conn = mz.get_mesh_connectivity(mesh_name_short)

                    if len(cur_conn['points']) != len(
                            mesh_data.get_point_list()):
                        interp_maps = True

                if interp_maps == True or interp_maps == 'True' or interp_maps == 'true':
                    logger.info('interpolating maps...{}'.format(map_))
                    created_mesh = mesh_data.build()
                    weight_list = mz.interpolate_values(created_mesh,
                                                    mesh_name_short,
                                                    weight_list)

                map_ = map_.replace(original_name, scene_name)

                if mc.objExists('%s[0]' % map_):
                    if not mc.getAttr('%s[0]' % map_, l=True):
                        tmp = []
                        for w in weight_list:
                            tmp.append(str(w))
                        val = ' '.join(tmp)
                        cmd = "setAttr " + '%s[0:%d] ' % (
                            map_, len(weight_list) - 1) + val
                        mm.eval(cmd)

                else:
                    try:
                        mc.setAttr(map_, weight_list, type='doubleArray')
                    except:
                        pass
                if created_mesh:
                    mc.delete(created_mesh)

    def get_mobject(self):
        """
        Gets mObject stored with node.
        Returns:
            mObject

        """
        return self.__mobject

    def set_mobject(self, maya_node):
        """
        Tracks an mObject with a builder node.  Given a maya node it looks up
        its mobject and stores that in a list that corresponds with the
        builder node list.
        Args:
            maya_node (str): The maya node to track.

        Returns:
            Nothing

        """
        self.__mobject = None

        if mc.objExists(maya_node):
            selection_list = om.MSelectionList()
            selection_list.add(maya_node)
            mobject = om.MObject()
            selection_list.getDependNode(0, mobject)
            self.__mobject = mobject

            # logger.info('{} - {}'.format(self.__mobject, maya_node))


def set_attrs(nodes, attr_filter=None):
    logger.info('DEPRECATED: Use .set_maya_attrs')

    for node in nodes:
        name = node.get_name()
        type_ = node.get_type()
        node_attrs = node.get_attr_list()
        if attr_filter:
            if attr_filter.get(type_, None):
                node_attrs = list(
                    set(node_attrs).intersection(attr_filter[type_]))

        for attr in node_attrs:
            if node.get_attr_key('type') == 'doubleArray':
                if mc.objExists(name + '.' + attr):
                    if not mc.getAttr(name + '.' + attr, l=True):
                        mc.setAttr(name + '.' + attr, node.get_attr_value(attr),
                                   type='doubleArray')
                else:
                    print name + '.' + attr + ' not found, skipping'
            else:
                if mc.objExists(name + '.' + attr):
                    if not mc.getAttr(name + '.' + attr, l=True):
                        try:
                            mc.setAttr(name + '.' + attr,
                                       node.get_attr_value(attr))
                        except:
                            # print 'tried...',attr
                            pass
                else:
                    print name + '.' + attr + ' not found, skipping'
