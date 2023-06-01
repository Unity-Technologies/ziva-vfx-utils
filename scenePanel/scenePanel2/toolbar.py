""" Helper functions to setup Scene Panel 2 toolbar widget.
"""
from functools import partial
from PySide2 import QtGui, QtWidgets, QtCore
from maya import cmds, mel
from utility.scriptCommands.zCacheCommands import clear_zcache, save_zcache, load_zcache
from zBuilder.utils.commonUtils import is_string
from zBuilder.commands import remove_zRivetToBone_nodes, remove_solver, remove_all_solvers
from ..uiUtils import get_icon_path_from_name
from .zGeoWidget import zGeoWidget

# Toolbar action data structure, it can be a single QAction item with following items:
# - Icon name
# - Title text
# - Tooltip text, pass None if not available
# - Slot function
# - Slot arguments
# Or it can be a QAction with menu. The first entry is a normal QAction,
# while the rest entries form a QMenu items:
# - Icon name(optional for menu item)
# - Action name
# - Tooltip text, pass None if not available
# - Slot function
_create_section_tuple = (
    ("zSolver", "Create zSolver", None, lambda: cmds.ziva(s=True)),
    ("zTissue", "Create zTissue", None, lambda: cmds.ziva(t=True)),
    ("zBone", "Create zBone", None, lambda: cmds.ziva(b=True)),
    ("zCloth", "Create zCloth", None, lambda: cmds.ziva(c=True)),
    (
        (
            "zAttachment",
            "Create zAttachment",
            "Create zAttachment: select source vertices and target object",
            lambda: cmds.ziva(a=True),
        ),
        (
            None,
            "Goal Attachment",
            "Attracts (goals) the selected tissue to the selected bone, "
            "using an adjustable soft constraint. "
            "Bone may deform and/or be animated using any Maya technique.",
            lambda: cmds.ziva(ga=True),
        ),
        (
            None,
            "Swap Attachment Direction",
            "Swaps the source and target Ziva objects of the selected attachment.",
            lambda: cmds.ziva(sai=True),
        ),
    ),
    (
        (
            "zCache",
            "Add zCache",
            "Adds a cache node to the selected solver. Once a cache node is added, "
            "simulations are cached automatically.",
            lambda: cmds.ziva(acn=True),
        ),
        (
            "clear_zCache",
            "Clear",
            "Clears the solver's simulation cache. "
            "Do this each time before re-running a simulation that was previously cached.",
            lambda: clear_zcache(),
        ),
        (
            None,
            "Load",
            "Loads a simulation cache from a .zcache disk file and applies it to the current solver.",
            lambda: load_zcache(),
        ),
        (
            None,
            "Save",
            "Saves the solver's simulation cache to a .zcache file.",
            lambda: save_zcache(),
        ),
        (
            None,
            "Select",
            "Select the solver's simulation cache node.",
            lambda: mel.eval("select -r `zQuery -t zCacheTransform`"),
        ),
    ),
    ("create-group", "Create Group", "Create Group: select tree view items",
     (zGeoWidget.create_group, )),
)

_add_section_tuple = (
    ("zMaterial", "Add zMaterial", "Add zMaterial: select tissue geometry",
     lambda: cmds.ziva(m=True)),
    ("zFiber", "Add zFiber", "Add zFiber: select tissue geometry", lambda: cmds.ziva(f=True)),
    ("subtissue", "Add zSubtissue", "Add Subtissue: select parent and then child tissue mesh",
     lambda: cmds.ziva(ast=True)),
    ("zRestShape", "Add zRestShape", "Add zRestShape: select tissue mesh and then restShape mesh",
     lambda: cmds.zRestShape(a=True)),
    ("zLineOfAction", "Add zLineOfAction", "Add zLineOfAction: select zFiber and curve",
     lambda: cmds.ziva(loa=True)),
    ("curve", "Add Fiber Curve", "Add Fiber Curve: select zFiber",
     lambda: cmds.zLineOfActionUtil()),
    ("zRivetToBone", "Add zRivetToBone",
     "Add zRivetToBone: select target curve vertex and bone mesh", lambda: cmds.zRivetToBone()),
)

_edit_section_tuple = (
    (  # Remove menu items
        (
            "remove_body",
            "Remove zTissue/zBone/zCloth from selected mesh",
            None,
            lambda: cmds.ziva(rm=True),
        ),
        ("Remove", ),  # separator
        (
            None,
            "Remove Rest Shape",
            "Removes rest shape(s) from a tissue.",
            lambda: mel.eval("ZivaDeleteSelectedRestShape"),
        ),
        (
            None,
            "Remove Rest Shape Target Mesh",
            "Removes rest shape target mesh from a tissue.",
            lambda: cmds.zRestShape(r=True),
        ),
        (
            None,
            "Remove Rivet to Bone",
            "Removes zRivetToBone and its connected locator node.",
            lambda: remove_zRivetToBone_nodes(cmds.ls(sl=True)),
        ),
        (
            None,
            "Remove Subtissue",
            "Removes subtissue connections, making the selected tissues full tissues again.",
            lambda: cmds.ziva(rst=True),
        ),
        (
            "remove_zSolver",
            "Remove Selected Solver(s)",
            "Removes the solver(s) inferred from selection, including their Ziva rigs.",
            lambda: remove_solver(askForConfirmation=False),
        ),
        (
            None,
            "Remove All Solvers",
            "Removes all Ziva solvers from the scene, including all Ziva rigs.",
            lambda: remove_all_solvers(confirmation=False),
        ),
        ("Delete", ),  # separator
        (
            None,
            "Delete selection",
            "Deletes the selected objects after first removing them from the solver.",
            lambda: mel.eval("ZivaDeleteSelection"),
        ),
    ),
    (  # Select menu items
        (
            "out_zTissue",
            "Select zTissues",
            "Selects zTissue nodes that are connected to the currently selected mesh(es).",
            lambda: mel.eval("select -r `zQuery -t zTissue`"),
        ),
        ("Select Connected", ),  # separator
        (
            "out_zBone",
            "Select zBones",
            "Selects zBones nodes that are connected to the currently selected mesh(es).",
            lambda: mel.eval("select -r `zQuery -t zBone`"),
        ),
        (
            "out_zCloth",
            "Select zCloth",
            "Selects zCloth nodes that are connected to the currently selected mesh(es).",
            lambda: mel.eval("select -r `zQuery -t zCloth`"),
        ),
        (
            "out_zAttachment",
            "Select zAttachments",
            "Selects zAttachments nodes that are connected to the currently selected mesh(es).",
            lambda: mel.eval("select -r `zQuery -t zAttachment`"),
        ),
        (
            "out_zRestShape",
            "Select zRestShape",
            "Selects zRestShape nodes that are connected to the currently selected mesh(es).",
            lambda: mel.eval("select -r `zQuery -t zRestShape`"),
        ),
        (
            "out_zTet",
            "Select zTet",
            "Selects zTet nodes that are connected to the currently selected mesh(es).",
            lambda: mel.eval("select -r `zQuery -t zTet`"),
        ),
        (
            "out_zMaterial",
            "Select zMaterials",
            "Selects zMaterials nodes that are connected to the currently selected mesh(es).",
            lambda: mel.eval("select -r `zQuery -t zMaterial`"),
        ),
        (
            "out_zFiber",
            "Select zFibers",
            "Selects zFibers nodes that are connected to the currently selected mesh(es).",
            lambda: mel.eval("select -r `zQuery -t zFiber`"),
        ),
        ("Select in Hierarchy", ),  # separator
        (
            "out_zTissue",
            "Tissues",
            "Selects tissue meshes in the currently selected hierarchy.",
            lambda: mel.eval("ZivaSelectInHierarchy zTissue"),
        ),
        (
            "out_zBone",
            "Bones",
            "Selects bone meshes in the currently selected hierarchy.",
            lambda: mel.eval("ZivaSelectInHierarchy zTissue"),
        ),
        (
            "out_zCloth",
            "Cloth",
            "Selects cloth meshes in the currently selected hierarchy.",
            lambda: mel.eval("ZivaSelectInHierarchy zTissue"),
        ),
    ),
)


def _setup_toolbar_action(zGeo_widget_inst, parent, name, text, tooltip, slot, slot_arguments=None):
    """ Create a single toolbar button
    """
    action = QtWidgets.QAction(parent)
    action.setText(text)
    if name:
        icon_path = get_icon_path_from_name(name)
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(icon_path))
        action.setIcon(icon)

    if tooltip:
        action.setToolTip(tooltip)

    if callable(slot):  # If it's a normal function, bind it directly
        if slot_arguments:
            action.triggered.connect(slot, *slot_arguments)
        else:
            action.triggered.connect(slot)
    else:
        # If this is a tuple, that means it's a class member function.
        # bind with widget instance first
        if slot_arguments:
            action.triggered.connect(partial(slot[0], zGeo_widget_inst, *slot_arguments))
        else:
            action.triggered.connect(partial(slot[0], zGeo_widget_inst))
    return action


def _setup_toolbar_menu(zGeo_widget_inst, parent, action_tuple):
    """ Create a toolbar action with menu, which has with multiple actions.
    """
    assert len(action_tuple) > 1, "Toolbar action tuple {} has only one item.".format(
        action_tuple[0][0])
    # First item is a toolbar action
    action = _setup_toolbar_action(zGeo_widget_inst, parent, *(action_tuple[0]))
    # The rest items form a menu
    menu = QtWidgets.QMenu()
    menu.setToolTipsVisible(True)
    for item in action_tuple[1:]:
        if item and len(item) > 1:
            menu.addAction(_setup_toolbar_action(zGeo_widget_inst, parent, *item))
        elif item and len(item) == 1:
            menu.addSection(item[0])
        else:
            menu.addSeparator()

    action.setMenu(menu)
    return action


def _create_toolbar(zGeo_widget_inst, title, action_tuple):
    """ Create the toolbar and label combo.
    Return the layout that contain both widgets.
    """
    toolbar = QtWidgets.QToolBar()
    toolbar.setIconSize(QtCore.QSize(27, 27))
    toolbar.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
    for item in action_tuple:
        action = None
        if is_string(item[0]):  # single action
            action = _setup_toolbar_action(zGeo_widget_inst, toolbar, *item)
        elif isinstance(item[0], tuple):  # action with menu
            action = _setup_toolbar_menu(zGeo_widget_inst, toolbar, item)
        assert action, "Unknown toolbar action type, check the data table."
        toolbar.addAction(action)

    lblTitle = QtWidgets.QLabel(title)
    lblTitle.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)

    lytContainer = QtWidgets.QVBoxLayout()
    lytContainer.addWidget(lblTitle)
    lytContainer.addWidget(toolbar)
    return lytContainer


def setup_toolbar(zGeo_widget_inst):
    """ Entry function to create the toolbar.

    Args:
        zGeo_widget_inst(zGeoWidget):
            zGeoWidget instance for bind its member functions to some buttons.

    Returns:
        Toolbar layout instance.
    """
    lytToolbar = QtWidgets.QHBoxLayout()
    lytToolbar.setAlignment(QtCore.Qt.AlignLeft)
    lytToolbar.addLayout(_create_toolbar(zGeo_widget_inst, "Create", _create_section_tuple))
    lytToolbar.addLayout(_create_toolbar(zGeo_widget_inst, "Add", _add_section_tuple))
    lytToolbar.addLayout(_create_toolbar(zGeo_widget_inst, "Edit", _edit_section_tuple))
    return lytToolbar
