import logging
import os
import re

from maya import cmds, mel
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

name_validation_pattern = re.compile(r"^[a-zA-Z][\w]*$")

# Attribute name of the zSolver node that stores scene panel data
SCENE_PANEL_DATA_ATTR_NAME = "scenePanelSerializedData"


def dock_window(dialog_class, *args, **kwargs):
    """ Create dock window for Maya
    """
    if mui.MQtUtil.findControl(dialog_class.CONTROL_NAME):
        # Delete existing control
        cmds.deleteUI(dialog_class.CONTROL_NAME)
        logger.info("removed workspace {}".format(dialog_class.CONTROL_NAME))

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

    elif is_zsolver_node(node) and is_default_solver(node):
        return get_icon_path_from_name(node.type + "Default")

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
    """ Given a proposed name and a list of names to check against, 
    this function checks for duplicate names and generates a unique name if duplicate found.

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
    """ Given a name, this method checks its validity by checking
    if the name starts with alphabet and
    can only have alphanumeric values and underscore.

    Args:
        name (str): name for checking validity
    Returns:
        bool: result of validity check
    """
    return re.match(name_validation_pattern, name)


class ProximityWidget(QtWidgets.QWidget):
    """ Widget in right-click menu to change map weights for attachments
    """

    def __init__(self, parent=None):
        super(ProximityWidget, self).__init__(parent)
        h_layout = QtWidgets.QHBoxLayout(self)
        h_layout.setContentsMargins(15, 15, 15, 15)
        self.from_edit = MenuLineEdit()
        self.from_edit.setFixedHeight(24)
        self.from_edit.setPlaceholderText("From")
        self.from_edit.setText("0.1")
        self.from_edit.setFixedWidth(40)
        self.to_edit = MenuLineEdit()
        self.to_edit.setFixedHeight(24)
        self.to_edit.setPlaceholderText("To")
        self.to_edit.setText("0.2")
        self.to_edit.setFixedWidth(40)
        ok_button = QtWidgets.QPushButton()
        ok_button.setText("Ok")
        h_layout.addWidget(self.from_edit)
        h_layout.addWidget(self.to_edit)
        h_layout.addWidget(ok_button)
        ok_button.clicked.connect(self.paint_by_prox)
        # setTabOrder doesn't work when used for menu
        # need to use next 2 lines as a workaround
        self.setFocusProxy(self.to_edit)
        ok_button.setFocusProxy(self.from_edit)
        self.from_edit.acceptSignal.connect(self.paint_by_prox)
        self.to_edit.acceptSignal.connect(self.paint_by_prox)

    def paint_by_prox(self):
        """Paints attachment map by proximity.
        """
        # to_edit can't have smaller value then from_edit
        from_value = float(self.from_edit.text())
        to_value = float(self.to_edit.text())
        if to_value < from_value:
            self.to_edit.setText(str(from_value))
        mel.eval('zPaintAttachmentsByProximity -min {} -max {}'.format(
            self.from_edit.text(), self.to_edit.text()))


class MenuLineEdit(QtWidgets.QLineEdit):
    """ Groups LineEdits together so after you press Tab it switch focus to sibling_right.
    If Shift+Tab pressed it uses sibling_left.
    Sends acceptSignal when Enter or Return button is pressed.
    This is for use in Menus, where tab navigation is broken out of the box,
    and the 'entered pressed' action undesirably causes the menu to close sometimes.
    """
    acceptSignal = QtCore.Signal()

    def __init__(self, parent=None):
        super(MenuLineEdit, self).__init__(parent)

    def event(self, event):
        if event.type() == QtCore.QEvent.KeyPress and event.key() == QtCore.Qt.Key_Tab:
            self.nextInFocusChain().setFocus()
            return True
        if event.type() == QtCore.QEvent.KeyPress and event.modifiers() == QtCore.Qt.ShiftModifier:
            # PySide bug, have to use this number instead of Key_Tab with modifiers
            if event.key() == 16777218:
                self.previousInFocusChain().setFocus()
                return True

        if event.type() == QtCore.QEvent.KeyPress and event.key() in [
                QtCore.Qt.Key_Enter, QtCore.Qt.Key_Return
        ]:
            self.acceptSignal.emit()
            # This will prevent menu to close after Enter/Return is pressed
            return True
        return super(MenuLineEdit, self).event(event)


def is_zsolver_node(node):
    """ Checks if a node type is "zSolver" or "zSolverTransform".

    Args:
        node: node to check

    Returns:
        bool: result of "zSolver" node type check
    """
    return node.type.startswith("zSolver")


def is_default_solver(node):
    """ Checks if a solver node is the default solver.

    Args:
        node: node to check
    Returns:
        bool: result of default solver check
    """
    # "defaultSolver" command returns name of the Transform node
    defaultSolver = cmds.zQuery(defaultSolver=True)
    if node.type == "zSolverTransform":
        return defaultSolver and defaultSolver[0] == node.name
    if node.type == "zSolver":
        return defaultSolver and defaultSolver[0] == node.parent.name
    return False


def get_zSolverTransform_treeitem(item):
    """ Given a TreeItem instance, return its zSolverTransform TreeItem.
    If not found, return None.
    """
    cur_item = item
    while cur_item:
        if cur_item.data.type == "zSolverTransform":
            return cur_item
        cur_item = cur_item.parent
    return None
