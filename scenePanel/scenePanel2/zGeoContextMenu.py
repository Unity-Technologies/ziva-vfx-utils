from functools import partial
from maya import cmds
from PySide2 import QtWidgets, QtGui
from ..uiUtils import get_icon_path_from_name


def create_general_context_menu(parent):
    """ Create context menu when nothing is selected.
    """
    # Currently it only contains the Refresh action
    icon = QtGui.QIcon(QtGui.QPixmap(get_icon_path_from_name("refresh")))
    action = QtWidgets.QAction(icon, "Refresh", parent)
    action.triggered.connect(partial(parent.reset_builder, False, False))
    menu = QtWidgets.QMenu(parent)
    menu.addAction(action)
    return menu


def create_solver_context_menu(parent, solverTM):
    """ Create context menu when solverTM item is selected.
    """

    # Some helper functions
    def toggle_attribute(node, attr):
        value = node.attrs[attr]["value"]
        if isinstance(value, bool):
            value = not value
        elif isinstance(value, int):
            value = 1 - value
        else:
            cmds.error("Attribute is not bool/int: {}.{}".format(node.name, attr))
            return
        node.attrs[attr]["value"] = value
        cmds.setAttr("{}.{}".format(node.long_name, attr), value)

    def create_checkable_action(parent, node, text, attr):
        action = QtWidgets.QAction(parent)
        action.setText(text)
        action.setCheckable(True)
        action.setChecked(node.attrs[attr]["value"])
        action.changed.connect(partial(toggle_attribute, node, attr))
        return action

    def create_info_action(parent):

        def run_info_command():
            sel = cmds.ls(sl=True)
            print(cmds.ziva(sel[0], i=True))

        action = QtWidgets.QAction(parent)
        action.setText("Info")
        action.setToolTip("Outputs solver statistics.")
        action.triggered.connect(run_info_command)
        return action

    def create_set_default_action(parent):

        def run_set_default_command(sel):
            print(cmds.ziva(sel, defaultSolver=True))

        action = QtWidgets.QAction(parent)
        action.setText("Set Default")
        action.setToolTip(
            "Set the default solver to the solver inferred from selection."
            "The default solver is used in case of solver ambiguity when there are 2 or more solvers in the scene."
        )
        sel = cmds.ls(sl=True)
        default_solver = cmds.zQuery(defaultSolver=True)
        if default_solver and default_solver[0] == sel[0]:
            action.setEnabled(False)
        action.triggered.connect(partial(run_set_default_command, sel[0]))
        return action

    # Create actions
    menu = QtWidgets.QMenu(parent)
    solver = solverTM.children[0]
    menu.addAction(create_checkable_action(parent, solverTM, "Enable", "enable"))
    menu.addAction(
        create_checkable_action(parent, solver, "Collision Detection", "collisionDetection"))
    menu.addAction(create_checkable_action(parent, solver, "Show Bones", "showBones"))
    menu.addAction(create_checkable_action(parent, solver, "Show Tet Meshes", "showTetMeshes"))
    menu.addAction(create_checkable_action(parent, solver, "Show Muscle Fibers",
                                           "showMuscleFibers"))
    menu.addAction(create_checkable_action(parent, solver, "Show Attachments", "showAttachments"))
    menu.addAction(create_checkable_action(parent, solver, "Show Collisions", "showCollisions"))
    menu.addAction(create_checkable_action(parent, solver, "Show Materials", "showMaterials"))
    menu.addSeparator()
    menu.addAction(create_info_action(parent))
    menu.addAction(create_set_default_action(parent))
    return menu


def create_group_context_menu(parent, group_index):
    """ Create context menu when Group item is selected.
    """
    action = QtWidgets.QAction(parent)
    action.setText("Select Hierarchy")
    action.triggered.connect(partial(parent.select_group_hierarchy, group_index))
    # TODO: Add Enable action
    menu = QtWidgets.QMenu(parent)
    menu.addAction(action)
    return menu
