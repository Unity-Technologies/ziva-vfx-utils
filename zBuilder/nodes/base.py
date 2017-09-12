import logging

import maya.OpenMaya as om
import maya.cmds as mc
import maya.mel as mm
import zBuilder.zMaya as mz
import json

logger = logging.getLogger(__name__)


class BaseNode(object):
    TYPE = None
    MAP_LIST = []
    SEARCH_EXCLUDE = ['_class', '_attrs', '_attr_list']

    def __init__(self, *args, **kwargs):
        """

        Returns:
            object: 
        """
        self._attr_list = []
        self._name = None
        self._attrs = {}
        self._maps = []
        self._association = []
        self.__mobject = None

        self._class = (self.__class__.__module__, self.__class__.__name__)

        self._setup = kwargs.get('setup', None)

        if kwargs.get('deserialize', None):
            self.deserialize(kwargs.get('deserialize', None))

        if args:
            self.populate(args[0])

    def __str__(self):
        if self.get_name():
            name = self.get_name()
            output = ''
            output += '= {} <{} {}> ==================================\n'.format(name,self.__class__.__module__, self.__class__.__name__)
            for key in self.__dict__:
                output += '\t{} - {}\n'.format(key, self.__dict__[key])

            return output
        return '<%s.%s>' % (self.__class__.__module__, self.__class__.__name__)

    def __repr__(self):
        output = '{}("{}")'.format(self.__class__.__name__, self.get_name())
        return output

    def serialize(self):
        """
        This replaces an mObject with the name of the object in scene to make it
        serializable for writing out to json.  Then it loops through keys in
        dict and saves out a temp dict of items that can be serializable and
        returns that temp dict for json writing purposes.

        Returns:
            dict: of serializable items
        """
        # removing and storing mobject as a string (object name)
        if self.__mobject:
            # print 'serialize: ', self.__mobject
            self.__mobject = mz.get_name_from_m_object(self.__mobject)

        # culling __dict__ of any non-serializable items so we can save as json
        output = dict()
        for key in self.__dict__:
            try:
                json.dumps(self.__dict__[key])
                output[key] = self.__dict__[key]
            except TypeError:
                pass
        return output

    def deserialize(self, dictionary):
        """
        For now this sets the mobject with the string that is there now.

        Returns:

        """
        for key in dictionary:
            if key not in ['_setup', '_class']:
                self.__dict__[key] = dictionary[key]

        self.set_attr_list(self._attrs.keys())

    def populate(self, *args, **kwargs):
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

    def apply(self, *args, **kwargs):
        raise NotImplementedError
    
    def print_(self):
        print self

    def string_replace(self, search, replace):
        """

        Args:
            search:
            replace:

        Returns:

        """
        for item in self.__dict__:
            if item not in self.SEARCH_EXCLUDE:
                if isinstance(self.__dict__[item], (tuple, list)):
                    if self.__dict__[item]:
                        new_names = []
                        for name in self.__dict__[item]:
                            new_name = mz.replace_long_name(search, replace, name)
                            new_names.append(new_name)
                        self.__dict__[item] = new_names
                elif isinstance(self.__dict__[item], basestring):
                    if self.__dict__[item]:
                        self.__dict__[item] = mz.replace_long_name(
                            search, replace, self.__dict__[item])
                elif isinstance(self.__dict__[item], dict):
                    # TODO needs functionality (replace keys)
                    print 'DICT', item

    def set_attrs(self, attrs):
        """

        Args:
            attrs:

        Returns:

        """
        self._attrs = attrs

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

    def get_type(self):
        """
        get type of node

        Returns:
            (str) of node name
        """
        try:
            return self.TYPE
        except AttributeError:
            return None

    def set_type(self, type_):
        """
        Sets type of node

        Args:
            type_ (str): the type of node.
        """
        self.TYPE = type_

    def get_map_meshes(self):
        """
        This is the mesh associated with each map in obj.MAP_LIST.  Typically
        it seems to coincide with mesh store in get_association.  Sometimes
        it deviates, so you can override this method to define your own
        list of meshes against the map list.

        Returns:
            list(): of long mesh names.
        """
        return self.get_association(long_name=True)

    def get_mesh_objects(self):
        """

        Returns:

        """
        meshes = list()
        for mesh_name in self.get_map_meshes():
            meshes.append(self._setup.get_data_by_key_name('mesh', mesh_name))
        return meshes

    def mirror(self):
        """

        Returns:

        """
        for mesh in self.get_mesh_objects():
            mesh.mirror()

    def get_map_objects(self):
        """

        Returns:

        """
        maps_ = list()
        for map_name in self.get_map_names():
            maps_.append(self._setup.get_data_by_key_name('map', map_name))
        return maps_

    def get_map_names(self):
        """

        Returns:

        """
        return self._maps

    def set_map_names(self, maps):
        """
        Sets the maps for a b_node as a list.

        Args:
            maps:

        Returns:

        """
        self._maps = maps

    def populate_attrs(self, item):
        """

        Args:
            item:

        Returns:

        """
        attr_list = self.get_attr_list()
        attrs = mz.build_attr_key_values(item, attr_list)
        self.set_attrs(attrs)

    def get_association(self, long_name=False):
        """

        Args:
            long_name:

        Returns:

        """
        if not long_name:
            tmp = []
            for item in self._association:
                tmp.append(item.split('|')[-1])
            return tmp
        else:
            return self._association

    # TODO get long name under hood and check for duplicate short names
    def set_association(self, association):
        """

        Args:
            association:

        Returns:

        """

        if isinstance(association, str):
            self._association = [association]
        else:
            self._association = association

    def compare(self):
        """

        Returns:

        """
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

    def interpolate_maps(self, interp_maps):
        """

        Args:
            interp_maps:

        Returns:

        """
        map_objects = self.get_map_objects()
        if interp_maps == 'auto':
            for map_object in map_objects:
                if not map_object.is_topologically_corrispoding():
                    interp_maps = True

        if interp_maps in [True, 'True', 'true']:
            for map_object in map_objects:
                map_object.interpolate()

    def set_maya_weights(self, interp_maps=False):
        """
        Given a Builder node this set the map values of the object in the maya
        scene.  It first does a mObject check to see if it has been tracked, if
        it has it uses that instead of stored scene_name.

        Args:
            interp_maps (str): Do you want maps interpolated?
                True forces interpolation.
                False cancels it.
                auto checks if it needs to.  Default = "auto"

        Returns:
            nothing.
        """
        maps = self.get_map_names()
        scene_name = self.get_scene_name()
        original_name = self.get_name()

        for map_ in maps:
            map_data = self._setup.get_data_by_key_name('map', map_)
            self.interpolate_maps(interp_maps)
            weight_list = map_data.get_value()

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
        if maya_node:
            if mc.objExists(maya_node):
                selection_list = om.MSelectionList()
                selection_list.add(maya_node)
                mobject = om.MObject()
                selection_list.getDependNode(0, mobject)
                self.__mobject = mobject


            # logger.info('{} - {}'.format(self.__mobject, maya_node))
