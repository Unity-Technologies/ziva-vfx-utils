from maya import cmds, mel
from maya import OpenMayaUI as mui
from shiboken2 import wrapInstance
from PySide2 import QtWidgets, QtCore
import logging
import os

logger = logging.getLogger(__name__)

sortRole = QtCore.Qt.UserRole  # scene_item.type ( zTissue, zBone, ... )
nodeRole = QtCore.Qt.UserRole + 1  # scene_item object
longNameRole = QtCore.Qt.UserRole + 2  # long name of scene_item object in the scene
enableRole = QtCore.Qt.UserRole + 3  # is node enabled

zGeo_UI_node_types = ['ui_{}_body'.format(item) for item in ('zTissue', 'zBone', 'zCloth')]


def dock_window(dialog_class, *args, **kwargs):
    """
    Create dock window for Maya
    """
    try:
        cmds.deleteUI(dialog_class.CONTROL_NAME)
        logger.info('removed workspace {}'.format(dialog_class.CONTROL_NAME))
    except:
        pass

    # building the workspace control with maya.cmds
    main_control = cmds.workspaceControl(dialog_class.CONTROL_NAME,
                                         ttc=["AttributeEditor", -1],
                                         iw=300,
                                         mw=100,
                                         wp='preferred',
                                         label=dialog_class.DOCK_LABEL_NAME)

    # after maya is ready we should restore the window since it may not be visible
    cmds.evalDeferred(lambda: cmds.workspaceControl(main_control, e=True, rs=True))

    # now lets get a C++ pointer to it using OpenMaya
    control_widget = mui.MQtUtil.findControl(dialog_class.CONTROL_NAME)
    # conver the C++ pointer to Qt object we can use
    control_wrap = wrapInstance(int(control_widget), QtWidgets.QWidget)

    # control_wrap is the widget of the docking window and now we can start working with it:
    control_wrap.setAttribute(QtCore.Qt.WA_DeleteOnClose)
    return dialog_class(control_wrap, *args, **kwargs)


def get_icon_path_from_node(node, parent):
    """
    Given a node, find the corresponding icon path that matches its type.

    Args:
        node (node): A node object to query.
        parent: parent of the node in scene panel tree

    Returns:
        str: The path to the matching icon. For 'zAttachment' node,
             it return seperate icons based on source and target.
    """
    if node.type == "zAttachment" and parent:
        target_cmd = 'zQuery -at {}'.format(node.name)
        target_attachment = mel.eval(target_cmd)

        source_cmd = 'zQuery -as {}'.format(node.name)
        source_attachment = mel.eval(source_cmd)

        if source_attachment[0] == parent:
            return get_icon_path_from_name(node.type + "Source")
        elif target_attachment[0] == parent:
            return get_icon_path_from_name(node.type + "Target")

    return get_icon_path_from_name(node.type)


def get_icon_path_from_name(name):
    """
    Given a name, find the corresponding icon path that matches.

    Args:
        name (str): A name of the icon to find.

    Returns:
        str: The path to the matching icon.
    """
    # look for repo icons first
    icons_folder = os.path.normpath(os.path.join(os.path.dirname(os.path.realpath(__file__)), '..'))
    # if repo does not exist try to use Ziva module folder else ignore it
    if "icons" not in os.listdir(icons_folder):
        try:
            icons_folder = cmds.moduleInfo(moduleName='ZivaVFX', path=True)
        except RuntimeError:
            return ''

    return os.path.join(icons_folder, 'icons', '{name}.png'.format(name=name))
