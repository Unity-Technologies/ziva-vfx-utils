# Helper functions to create Scene Panel 2 menubar
import zBuilder.utils as utility

from ..uiUtils import get_icon_path_from_name
from utility.licenseRegister import licenseRegisterWidget
from PySide2 import QtWidgets, QtGui, QtCore
from maya import cmds, mel

# Menu bar data structure:
# key: menu name
# value: each menu action. It can be a tuple of:
# - Action name
# - Status bar text
# - Slot
# - Icon name(optional)
# Or it can be another submenu dict with same structure.
_menubar_dict = {
    "File": (
        (
            "Load...",
            "Load a Ziva rig from a file, into a new solver, or a specified existing solver. "
            "Geometry must already be present in the scene.",
            lambda: mel.eval("zLoadRigOptions"),
        ),
        (
            "Save...",
            "Save a Ziva rig for the selected solver to a file. "
            "If multiple solvers are selected, only the first solver is saved",
            lambda: mel.eval("zSaveRigOptions"),
        ),
        (
            "Cut",
            "Cut the Ziva rig in selected objects to the Ziva clipboard. "
            "Selected objects must come from exactly one solver. "
            "Selected objects may contain a solver node.",
            utility.rig_cut,
        ),
        (
            "Copy",
            "Copy the Ziva rig in selected objects to the Ziva clipboard. "
            "Selected objects must come from exactly one solver. "
            "Selected objects may contain a solver node.",
            utility.rig_copy,
        ),
        (
            "Paste",
            "Paste the Ziva rig from the Ziva clipboard onto scene geometry, "
            "into the solver stored in the Ziva clipboard. "
            "If such a solver does not exist in the scene, it is created.",
            utility.rig_paste,
        ),
        (),  # separator
        (
            "Copy/Paste With Name Substitution...",
            "Copy/pastes Ziva rig items using a name substitution (defined via regular expressions). "
            "Useful for mirroring the Ziva rig from one side of a character onto the other. "
            "Select the objects whose Ziva rig is to be copy/pasted. "
            "Selected objects should come from exactly one solver.",
            lambda: mel.eval("zRigCopyPasteWithNameSubstitutionOptions()"),
        ),
        (
            "Update",
            "Update Ziva rig in the selected solver to use the current geometry. "
            "Useful if you modified geometry after converting it to Ziva bodies. "
            "This updates the solver to use the new geometry.",
            utility.rig_update,
        ),
        (
            "Transfer...",
            "Transfer Ziva rig from one solver into another. "
            "Two copies of geometries must exist in the scene; "
            "the target copies must be prefixed with a specified prefix.",
            lambda: mel.eval("zRigTransferOptions()"),
        ),
    ),
    "Tools": (
        (
            "Merge Solvers",
            "Merges selected solvers into one.",
            lambda: utility.merge_solvers(cmds.ls(sl=True)),
        ),
        (
            "Toggle Enabled Bodies",
            "Toggles the active state of the selected Ziva objects.",
            lambda: mel.eval("ZivaToggleEnabled"),
        ),
        (),  # separator
        (
            "zPolyCombine",
            "Will combine multiple polySets into a single polySet.",
            cmds.zPolyCombine,
        ),
        (
            "Extract RestShape",
            "Extracts a new shape from a simulated mesh + sculpted mesh that can be used as a Rest Shape target",
            lambda: cmds.zRestShape(pg=True),
        ),
        (),  # separator
        (
            "Run Mesh Analysis",
            "Quality-check the selected mesh(es).",
            lambda: cmds.zMeshCheck(select=True),
        ),
        (
            "Find Intersections",
            "Find intersections between Maya meshes.",
            lambda: mel.eval("ZivaSelectIntersections"),
        ),
        (
            "Find Self Intersections",
            "Find self-intersections (self-collisions) on a Maya mesh.",
            lambda: mel.eval("ZivaSelectSelfIntersections"),
        ),
        (),  # separator
        (
            "Select Vertices",
            "Selects vertices on the first Maya mesh based on their distance to the second selected Maya mesh.",
            lambda: mel.eval("zSelectVerticesByProximityRadius $ZivaSelectByProximityRadiusFloat"),
        ),
        (
            "Paint Attachments By Proximity",
            "For a selected existing attachment, choose new source vertices "
            "(and repaint the source attachment map accordingly), "
            "by selecting the vertices that are within the specified distance threshold "
            "to the attachment target object.",
            lambda: mel.eval(
                "zPaintAttachmentsByProximity -min $ZivaPaintByProximityMinFloat -max $ZivaPaintByProximityMaxFloat"
            ),
        ),
    ),
    "Help": (
        (
            "Ziva Command Help",
            "Print Ziva command help to the Maya script editor.",
            lambda: print(cmds.ziva(h=True)),
        ),
        {
            "Run Demo": (
                (
                    "Anatomical Arm",
                    "Demonstrates an anatomical human arm.",
                    lambda: mel.eval("ziva_main_anatomicalArmDemo(1)"),
                ),
                (
                    "Goaling, Self-Collisions, Ziva Cache and Spatially Varying Materials",
                    "Demonstrates goaling, self-collisions, Ziva caching, "
                    "and spatially varying materials, on a Maya-rigged fish example.",
                    lambda: mel.eval("ziva_main_goalingDemo(1)"),
                ),
                (
                    "Self-Collisions, Ziva Cache and Delaunay Tet Mesher",
                    "Demonstrates self-collisions, Ziva cache and the Delaunay tet mesher.",
                    lambda: mel.eval("ziva_main_selfCollisionsCacheAndDelaunayTetMesherDemo(1)"),
                ),
                (
                    "Attachments",
                    "Demonstrates attachments.",
                    lambda: mel.eval("ziva_main_attachmentTest(1)"),
                ),
                (
                    "Collisions",
                    "Demonstrates collisions",
                    lambda: mel.eval("ziva_main_collisionTest(1)"),
                ),
                (
                    "One Of Each Attachments",
                    "Demonstrates one of each of the four attachment types.",
                    lambda: mel.eval("ziva_main_oneOfEachAttachments(1)"),
                ),
                (
                    "One Of Each Collision Types",
                    "Demonstrates one of each of the four collision types.",
                    lambda: mel.eval("ziva_main_oneOfEachCollisionTypes(1)"),
                ),
                (
                    "Spatially Varying Materials",
                    "Demonstrates spatially varying materials.",
                    lambda: mel.eval("ziva_main_spatiallyVaryingMaterials(1)"),
                ),
                (
                    "Cloth",
                    "Demonstrates cloth and cloth-object collisions.",
                    lambda: mel.eval("ziva_main_clothDemo(1)"),
                ),
                (
                    "Cloth Rest Scale and Pressure",
                    "Demonstrates cloth rest scale and pressure.",
                    lambda: mel.eval("ziva_main_restScalePressureDemo(1)"),
                ),
                (
                    "Isomesher",
                    "Demonstrates the Ziva isomesher.",
                    lambda: mel.eval("ziva_main_isoMesherDemo(1)"),
                ),
            ),
        },
        (
            "Register License...",
            "Register Ziva VFX license.",
            licenseRegisterWidget.main,
        ),
        (),
        (
            "About",
            "About the Ziva Maya plug-in.",
            lambda: print(cmds.ziva(z=True)),
        ),
        (
            "Online Resources",
            "Loads Ziva resource library.",
            lambda: mel.eval("launch -webPage 'http://zivadynamics.com/resource-library'"),
        ),
    ),
}


def _add_menu_actions(menu, text, statusbar_text, slot, icon_name=None):
    action = QtWidgets.QAction(menu)
    action.setText(text)
    action.setStatusTip(statusbar_text)
    action.triggered.connect(slot)
    if icon_name:
        icon = QtGui.QIcon()
        icon_path = get_icon_path_from_name(icon_name)
        icon.addPixmap(QtGui.QPixmap(icon_path))
        action.setIcon(icon)
    menu.addAction(action)


def _create_menu(menubar, menu_name, menu_action_tuple):
    menu = menubar.addMenu(menu_name)
    for item in menu_action_tuple:
        if item:
            if isinstance(item, tuple):
                _add_menu_actions(menu, *item)
            elif isinstance(item, dict):
                for name, actions in item.items():
                    _create_menu(menu, name, actions)
        else:  # empty tuple means a separator
            menu.addSeparator()


def setup_menubar(parent):
    """ Entry function to create the toolbar.

    Args:
        parent: parent widget the menu bar belongs to.

    Returns:
        Menubar layout instance.
    """
    menubar = QtWidgets.QMenuBar(parent)
    for name, actions in _menubar_dict.items():
        _create_menu(menubar, name, actions)
    # restrict the size of the menubar to prevent uneven expansion
    menubar.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
    lytMenuBar = QtWidgets.QHBoxLayout()
    lytMenuBar.addWidget(menubar)
    lytMenuBar.setAlignment(menubar, QtCore.Qt.AlignRight)
    return lytMenuBar
