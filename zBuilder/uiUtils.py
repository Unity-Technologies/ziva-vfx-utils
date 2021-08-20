import logging
import os
import re

from maya import cmds
from maya import OpenMayaUI as mui
from shiboken2 import wrapInstance
from PySide2 import QtWidgets, QtCore

logger = logging.getLogger(__name__)

sortRole = QtCore.Qt.UserRole  # scene_item.type ( zTissue, zBone, ... )
nodeRole = QtCore.Qt.UserRole + 1  # scene_item object
longNameRole = QtCore.Qt.UserRole + 2  # long name of scene_item object in the scene
enableRole = QtCore.Qt.UserRole + 3  # is node enabled

zGeo_UI_node_types = ["ui_{}_body".format(item) for item in ("zTissue", "zBone", "zCloth")]

name_duplication_check_pattern = re.compile(r".*?(\d+)$")

name_validation_pattern = re.compile(r"[a-zA-Z][\w]*")

def dock_window(dialog_class, *args, **kwargs):
    """ Create dock window for Maya
    """
    try:
        cmds.deleteUI(dialog_class.CONTROL_NAME)
        logger.info("removed workspace {}".format(dialog_class.CONTROL_NAME))
    except:
        pass

    # building the workspace control with maya.cmds
    main_control = cmds.workspaceControl(dialog_class.CONTROL_NAME,
                                         ttc=["AttributeEditor", -1],
                                         iw=300,
                                         mw=100,
                                         wp="preferred",
                                         label=dialog_class.DOCK_LABEL_NAME)

    # after Maya is ready we should restore the window since it may not be visible
    cmds.evalDeferred(lambda: cmds.workspaceControl(main_control, e=True, rs=True))

    # now lets get a C++ pointer to it using OpenMaya
    control_widget = mui.MQtUtil.findControl(dialog_class.CONTROL_NAME)
    # convert the C++ pointer to Qt object we can use
    control_wrap = wrapInstance(int(control_widget), QtWidgets.QWidget)

    # control_wrap is the widget of the docking window and now we can start working with it:
    control_wrap.setAttribute(QtCore.Qt.WA_DeleteOnClose)
    return dialog_class(control_wrap, *args, **kwargs)


def get_icon_path_from_node(node, parent):
    """ Given a node, find the corresponding icon path that matches its type.
    Args:
        node (node): A node object to query.
        parent: parent of the node in scene panel tree

    Returns:
        str: The path to the matching icon. For "zAttachment" node,
             it return separate icons based on source and target.
    """

    if node.type == "zAttachment" and parent:
        try:
            source_attachment = cmds.zQuery(node.name, attachmentSource=True)
            target_attachment = cmds.zQuery(node.name, attachmentTarget=True)
        except:
            # fallback to normal attachment icon if error happens
            return get_icon_path_from_name(node.type)

        if source_attachment[0] == parent:
            return get_icon_path_from_name(node.type + "Source")
        if target_attachment[0] == parent:
            return get_icon_path_from_name(node.type + "Target")

    return get_icon_path_from_name(node.type)


def get_icon_path_from_name(name):
    """ Given a name, find the corresponding icon path that matches.
    Args:
        name (str): A name of the icon to find.

    Returns:
        str: The path to the matching icon.
    """
    # look for repo icons first
    icons_folder = os.path.normpath(os.path.join(os.path.dirname(os.path.realpath(__file__)), ".."))
    # if repo does not exist try to use Ziva module folder else ignore it
    if "icons" not in os.listdir(icons_folder):
        try:
            icons_folder = cmds.moduleInfo(moduleName="ZivaVFX", path=True)
        except RuntimeError:
            return ""

    return os.path.join(icons_folder, "icons", "{name}.png".format(name=name))


def get_node_by_index(index, fallback_val):
    """ Given QModelIndex, return associated model data.
    If the index or its reference data is invalid, return fallback value
    """
    if index.isValid():
        node = index.internalPointer()
        if node:
            return node
    return fallback_val

def get_unique_name(proposed_name, list_of_names):
    """
    Given a proposed name and a list of names to check against, this function
    checks for duplicate names and generates a unique name if duplicate found.
    Args:
        proposed_name (str): The proposed name
        list_of_names (list): Names to check against for duplicates
    Returns:
        str: A unique name
    """
    # Find ending digits, if any

    result = re.match(name_duplication_check_pattern, proposed_name)
    base_name = proposed_name.rstrip(result.group(1)) if result else proposed_name
    index = 1
    while True:
        find_conflict = any(name == proposed_name for name in list_of_names)
        if find_conflict:
            proposed_name = "{}{}".format(base_name, index)
            index += 1
        else:
            break
    return proposed_name

def validate_group_node_name(name):
    """
    Given a name, this method checks its validity by checking if the name starts
    with alphabet and can only have alphanumeric values and underscore.
    Args:
        name (str): name for checking validity
    Returns:
        bool: result of validity check
    """
    return re.match(name_validation_pattern, name)
