from zBuilder.commonUtils import is_sequence
from maya import cmds
from maya import OpenMaya as om
import re
'''
The module contains helper functions depends on Maya Python API.
'''


def get_short_name(node_name):
    # type: (str) -> str
    '''
    Return short name of Maya node, if it's already short name, return it as is.
    '''
    return node_name.split('|')[-1]


def get_type(body):
    """
    Really light wrapper for getting type of maya node.  Ya, I know.

    Args:
        body (str): Maya node to get type of

    Returns:
        str: String of node type.
    """
    return cmds.objectType(body)


def parse_maya_node_for_selection(args):
    """
    This is used to check passed args in a function to see if they are valid
    maya objects in the current scene.  If any of the passed names are not in
    the  it raises a Exception.  If nothing is passed it looks at what is
    actively selected in scene to get selection.  This way it functions like a
    lot of the maya tools, uses what is passed OR it uses what is selected.

    Args:
        args: The args to test

    Returns:
        (list) maya selection

    """
    selection = None
    if len(args) > 0:
        if is_sequence(args[0]):
            selection = args[0]
        else:
            selection = [args[0]]

        tmp = []
        # check if it exists and get long name----------------------------------
        for sel in selection:
            if cmds.objExists(sel):
                tmp.extend(cmds.ls(sel, l=True))
            else:
                raise Exception('{} does not exist in scene, stopping!'.format(sel))
        selection = tmp

    # if nothing valid has been passed then we check out active selection in
    # maya.
    if not selection:
        selection = cmds.ls(sl=True, l=True)
        # if still nothing is selected then we raise an error
        if not selection:
            raise Exception('Nothing selected or passed, please select something and try again.')
    return selection


def replace_long_name(search, replace, long_name):
    """ does a search and replace on a long name.  It splits it up by ('|') then
    performs it on each piece

    Args:
        search (str): search term
        replace (str): replace term
        long_name (str): the long name to perform action on

    returns:
        str: result of search and replace
    """
    new_name = ''
    # check if long_name is valid.  If it is not, return itself
    if long_name and long_name != ' ':
        items = long_name.split('|')
        for item in items:
            # This checks if the item is an empty string.  If this check is not made
            # it will, under certain circumstances, add a prefex to an empty string
            # and make the long name invalid.
            if item:
                matches = re.finditer(search, item)
                for match in matches:
                    if match.groups():
                        # if there are groups in the regular expression, (), this splits them up and
                        # creates a new replace string based on the groups and what is between them.
                        # on this string: '|l_loa_curve'
                        # This expression: "(^|_)l($|_)"
                        # yeilds this replace string: "l_"
                        # as it found an "_" at end of string.
                        # then it performs a match replace on original string
                        with_this = item[match.span(1)[0]:match.span(1)[1]] + replace + item[
                            match.span(2)[0]:match.span(2)[1]]
                        item = item[:match.start()] + with_this + item[match.end():]
                    else:
                        item = re.sub(search, replace, item)

                # reconstruct long name if applicable
                if '|' in long_name and item != '':
                    new_name += '|' + item
                else:
                    new_name += item
    else:
        return long_name

    return new_name


def replace_dict_keys(search, replace, dictionary):
    """
    Does a search and replace on dictionary keys

    Args:
        search (:obj:`str`): search term
        replace (:obj:`str`): replace term
        dictionary (:obj:`dict`): the dictionary to do search on

    Returns:
        :obj:`dict`: result of search and replace
    """
    tmp = {}
    for key in dictionary:
        new = replace_long_name(search, replace, key)
        tmp[new] = dictionary[key]

    return tmp


def build_attr_list(selection):
    """
    Builds a list of attributes to store values for.  It is looking at keyable
    attributes and if they are in channelBox.

    Args:
        selection (str): maya object to find attributes

    returns:
        list: list of attributes names
    """
    attributes = []
    keyable = cmds.listAttr(selection, k=True)
    channel_box = cmds.listAttr(selection, cb=True)
    if channel_box:
        attributes.extend(channel_box)
    if keyable:
        attributes.extend(keyable)

    attribute_names = []
    for attr in attributes:
        obj = '{}.{}'.format(selection, attr)
        if cmds.objExists(obj):
            type_ = cmds.getAttr(obj, type=True)
            if not type_ == 'TdataCompound':
                attribute_names.append(attr)

    return attribute_names


def build_attr_key_values(selection, attr_list):
    """ Builds a dictionary of attribute key/values.  Stores the value, type, and
    locked status.
    Args:
        selection: Items to save attrbutes for.
        attr_list: List of attributes to save.

    Returns:
        dict: of attribute values.

    """
    attr_dict = {}
    for attr in attr_list:
        obj = '{}.{}'.format(selection, attr)
        for item in cmds.ls(obj):
            type_ = cmds.getAttr(item, type=True)
            if not type_ == 'TdataCompound':
                # we do not want to get any attribute that is not writable as we cannot change it.
                if cmds.attributeQuery(attr, node=selection, w=True):
                    attr_dict[attr] = {}
                    attr_dict[attr]['type'] = type_
                    attr_dict[attr]['value'] = cmds.getAttr(item)
                    attr_dict[attr]['locked'] = cmds.getAttr(item, lock=True)
                    attr_dict[attr]['alias'] = cmds.aliasAttr(obj, q=True)

    return attr_dict


def safe_rename(old_name, new_name):
    """
    Same as cmds.rename but does not throw an exception if renaming failed
    Useful if need to rename all the nodes that are not referenced
    """
    if old_name != new_name:
        try:
            return cmds.rename(old_name, new_name)
        except RuntimeError:
            pass

    return old_name


def get_mdagpath_from_mesh(mesh_name):
    """ Maya stuff, getting the dagpath from a mesh name

    Args:
        mesh_name: The mesh to get dagpath from.
    """
    mesh_m_dag_path = om.MDagPath()
    sel_list = om.MSelectionList()
    sel_list.add(mesh_name)
    sel_list.getDagPath(0, mesh_m_dag_path)

    return mesh_m_dag_path


def get_name_from_m_object(m_object, long_name=True):
    """ Gets maya scene name from given mObject.
    Args:
        m_object: The m_object to get name from.
        long_name: Returns long name. Default = ``True``

    Returns:
        str: Maya object name.

    """
    if m_object.hasFn(om.MFn.kDagNode):
        dagpath = om.MDagPath()
        om.MFnDagNode(m_object).getPath(dagpath)
        if long_name:
            name = dagpath.fullPathName()
        else:
            name = dagpath.partialPathName()
    else:
        name = om.MFnDependencyNode(m_object).name()
    return name
