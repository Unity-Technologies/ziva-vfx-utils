""" Helper functions to create Scene Panel 2 menubar
"""
import logging

from collections import OrderedDict
from functools import partial
from PySide2 import QtWidgets, QtGui, QtCore
from maya import cmds, mel
from utility.licenseRegister import licenseRegisterWidget
from utility.scriptCommands.zCacheCommands import clear_zcache
from zBuilder.commands import (rig_cut, rig_copy, rig_paste, rig_update, merge_solvers,
                               remove_zRivetToBone_nodes, remove_solver, remove_all_solvers, rename_ziva_nodes)
from ..uiUtils import get_icon_path_from_name
from .zGeoWidget import zGeoWidget

logger = logging.getLogger(__name__)

# Menu bar data structure:
# key: menu name
# value: each menu action. It can be a tuple of:
# - Action name
# - Status bar text
# - Slot
# - Icon name(optional)
# Or it can be another submenu dict with same structure.
_menubar_dict = OrderedDict()

_menubar_dict["File"] = (
    (
        "Load Ziva Rig...",
        "Load a Ziva rig from a file, into a new solver, or a specified existing solver. "
        "Geometry must already be present in the scene.",
        lambda: mel.eval("zLoadRigOptions"),
    ),
    (
        "Save Ziva Rig...",
        "Save a Ziva rig for the selected solver to a file. "
        "If multiple solvers are selected, only the first solver is saved",
        lambda: mel.eval("zSaveRigOptions"),
    ),
    (),  # separator
    (
        "Cut Selection",
        "Cut the Ziva components from selected objects to the Ziva clipboard. "
        "Selected objects must come from exactly one solver. "
        "Selected objects may contain a solver node.",
        rig_cut,
    ),
    (
        "Copy Selection",
        "Copy the Ziva components from selected objects to the Ziva clipboard. "
        "Selected objects must come from exactly one solver. "
        "Selected objects may contain a solver node.",
        rig_copy,
    ),
    (
        "Paste Selection",
        "Paste the Ziva rig from the Ziva clipboard onto scene geometry, "
        "into the solver stored in the Ziva clipboard. "
        "If such a solver does not exist in the scene, it is created.",
        rig_paste,
    ),
    (),  # separator
    (
        "Mirror Ziva Rig...",
        "Mirrors a Ziva rig."
        "Select the objects whose Ziva rig is to be mirrored. "
        "Alternatively select the zSolver to mirror whole rig. ",
        lambda: mel.eval("zMirrorOptions()"),
    ),
    (
        "Update Ziva Rig",
        "Update Ziva rig in the selected solver to use the current geometry. "
        "Useful if you modified geometry after converting it to Ziva bodies. "
        "This updates the solver to use the new geometry.",
        lambda: rig_update(None),
    ),
    (
        "Transfer Ziva Rig...",
        "Transfer Ziva rig from one solver into another. "
        "Two copies of geometries must exist in the scene; "
        "the target copies must be prefixed with a specified prefix.",
        lambda: mel.eval("zRigTransferOptions()"),
    ),
    (),  # separator
    (
        "Transfer Skin Cluster...",
        "Transfer a Maya skin cluster from a mesh onto a warped mesh."
        "Select a Maya mesh that contains a skin cluster that you want to warp.",
        lambda: mel.eval("zSkinClusterTransferOptions()"),
    ),
)

_menubar_dict["Edit"] = (
    {
        "Remove": (
            ("Remove", ),  # separator
            (
                "zTissue/zBone/zCloth",
                "Remove zTissue/zBone/zCloth from selected mesh",
                lambda: cmds.ziva(rm=True),
                "remove_body",
            ),
            (
                "Rest Shape",
                "Removes rest shape(s) from a tissue.",
                lambda: mel.eval("ZivaDeleteSelectedRestShape"),
            ),
            (
                "Rest Shape Target Mesh",
                "Removes rest shape target mesh from a tissue.",
                lambda: cmds.zRestShape(r=True),
            ),
            (
                "Rivet to Bone",
                "Removes zRivetToBone and its connected locator node.",
                lambda: remove_zRivetToBone_nodes(cmds.ls(sl=True)),
            ),
            (
                "Subtissue",
                "Removes subtissue connections, making the selected tissues full tissues again.",
                lambda: cmds.ziva(rst=True),
            ),
            (
                "Selected Solver(s)",
                "Removes the solver(s) inferred from selection, including their Ziva rigs.",
                lambda: remove_solver(askForConfirmation=False),
                "remove_zSolver",
            ),
            (
                "All Solvers",
                "Removes all Ziva solvers from the scene, including all Ziva rigs.",
                lambda: remove_all_solvers(confirmation=False),
            ),
            ("Delete", ),  # separator
            (
                "Delete selection",
                "Deletes the selected objects after first removing them from the solver.",
                lambda: mel.eval("ZivaDeleteSelection"),
            ),
        ),
    },
    {
        "Select": (
            ("Select Connected", ),  # separator
            (
                "zTissues",
                "Selects zTissue nodes that are connected to the currently selected mesh(es).",
                lambda: mel.eval("select -r `zQuery -t zTissue`"),
                "out_zTissue",
            ),
            (
                "zBones",
                "Selects zBones nodes that are connected to the currently selected mesh(es).",
                lambda: mel.eval("select -r `zQuery -t zBone`"),
                "out_zBone",
            ),
            (
                "zCloth",
                "Selects zCloth nodes that are connected to the currently selected mesh(es).",
                lambda: mel.eval("select -r `zQuery -t zCloth`"),
                "out_zCloth",
            ),
            (
                "zAttachments",
                "Selects zAttachments nodes that are connected to the currently selected mesh(es).",
                lambda: mel.eval("select -r `zQuery -t zAttachment`"),
                "out_zAttachment",
            ),
            (
                "zRestShape",
                "Selects zRestShape nodes that are connected to the currently selected mesh(es).",
                lambda: mel.eval("select -r `zQuery -t zRestShape`"),
                "out_zRestShape",
            ),
            (
                "zTet",
                "Selects zTet nodes that are connected to the currently selected mesh(es).",
                lambda: mel.eval("select -r `zQuery -t zTet`"),
                "out_zTet",
            ),
            (
                "zMaterials",
                "Selects zMaterials nodes that are connected to the currently selected mesh(es).",
                lambda: mel.eval("select -r `zQuery -t zMaterial`"),
                "out_zMaterial",
            ),
            (
                "zFibers",
                "Selects zFibers nodes that are connected to the currently selected mesh(es).",
                lambda: mel.eval("select -r `zQuery -t zFiber`"),
                "out_zFiber",
            ),
            ("Select in Hierarchy", ),  # separator
            (
                "Tissues",
                "Selects tissue meshes in the currently selected hierarchy.",
                lambda: mel.eval("ZivaSelectInHierarchy zTissue"),
                "out_zTissue",
            ),
            (
                "Bones",
                "Selects bone meshes in the currently selected hierarchy.",
                lambda: mel.eval("ZivaSelectInHierarchy zTissue"),
                "out_zBone",
            ),
            (
                "Cloth",
                "Selects cloth meshes in the currently selected hierarchy.",
                lambda: mel.eval("ZivaSelectInHierarchy zTissue"),
                "out_zCloth",
            ),
        ),
    },
)

_menubar_dict["Create"] = (
    (
        "Solver",
        "Creates an empty solver.",
        lambda: cmds.ziva(s=True),
        "out_zSolver",
    ),
    (
        "Tissue",
        "Converts the selected Maya mesh(es) to tissue(s)."
        "Tissues are solid deformable objects (examples: muscles, fat, skin).",
        lambda: cmds.ziva(t=True),
        "out_zTissue",
    ),
    (
        "Bone",
        "Converts the selected Maya mesh(es) to bone(s)."
        "Bones are externally animated Maya meshes of any geometry and purpose whatsoever."
        "The bones may deform and/or be animated using any Maya technique."
        "They are *not* simulated using the Ziva solver.",
        lambda: cmds.ziva(b=True),
        "out_zBone",
    ),
    (
        "Cloth",
        "Converts the selected Maya mesh(es) to cloth."
        "Cloth objects are thin deformable objects (examples: sheets, textile, skin, membranes).",
        lambda: cmds.ziva(c=True),
        "out_zCloth",
    ),
    {
        "Attachment": (
            (
                "Attachment",
                "Creates an attachment (a constraint) between two selected Ziva objects and/or their selected vertices."
                "Parts of the mesh where constraints apply may be painted"
                "(default: entire surface, or the selected vertices if they are provided)."
                "For a sliding attachment, vertices of the first object will slide on the second object.",
                lambda: cmds.ziva(a=True),
                "out_zAttachment",
            ),
            (
                "Goal Attachment",
                "Attracts (goals) the selected tissue to the selected bone, "
                "using an adjustable soft constraint. "
                "Bone may deform and/or be animated using any Maya technique.",
                lambda: cmds.ziva(ga=True),
            ),
            (
                "Swap Attachment Direction",
                "Swaps the source and target Ziva objects of the selected attachment.",
                lambda: cmds.ziva(sai=True),
            ),
        ),
    },
    {
        "Cache": (
            (
                "Add zCache",
                "Adds a cache node to the selected solver. Once a cache node is added, "
                "simulations are cached automatically.",
                lambda: cmds.ziva(acn=True),
                "out_zCache",
            ),
            (
                "Clear",
                "Clears the solver's simulation cache. "
                "Do this each time before re-running a simulation that was previously cached.",
                lambda: clear_zcache(),
                "clear_zCache",
            ),
            (
                "Load",
                "Loads a simulation cache from a .zcache disk file and applies it to the current solver.",
                lambda: load_zcache(),
                "load_zcache"
            ),
            (
                "Save",
                "Saves the solver's simulation cache to a .zcache file.",
                lambda: save_zcache(),
                "save_zcache"
            ),
            (
                "Select",
                "Select the solver's simulation cache node.",
                lambda: mel.eval("select -r `zQuery -t zCacheTransform`"),
            ),
        ),
    },
    (
        "Group",
        "Create Group: select tree view items",
        (zGeoWidget.create_group, ),
        "create-group",
    ),
)

_menubar_dict["Add"] = (
    (
        "zMaterial",
        "Add zMaterial: select tissue geometry",
        lambda: cmds.ziva(m=True),
        "out_zMaterial",
    ),
    (
        "zFiber",
        "Add zFiber: select tissue geometry",
        lambda: cmds.ziva(f=True),
        "out_zFiber",
    ),
    (
        "zSubtissue",
        "Add Subtissue: select parent and then child tissue mesh",
        lambda: cmds.ziva(ast=True),
        "subtissue",
    ),
    (
        "zRestShape",
        "Add zRestShape: select tissue mesh and then restShape mesh",
        lambda: cmds.zRestShape(a=True),
        "out_zRestShape",
    ),
    (
        "zLineOfAction",
        "Add zLineOfAction: select zFiber and curve",
        lambda: cmds.ziva(loa=True),
        "out_zLineOfAction",
    ),
    (
        "Fiber Curve",
        "Add Fiber Curve: select zFiber",
        lambda: cmds.zLineOfActionUtil(),
        "curve",
    ),
    (
        "zRivetToBone",
        "Add zRivetToBone: select target curve vertex and bone mesh",
        lambda: cmds.zRivetToBone(),
        "out_zRivetToBone",
    ),
)

_menubar_dict["Tools"] = (
    (
        "Merge Solvers",
        "Merges selected solvers into one.",
        lambda: merge_solvers(cmds.ls(sl=True)),
    ),
    (
        "Toggle Enabled Bodies",
        "Toggles the active state of the selected Ziva objects.",
        lambda: mel.eval("ZivaToggleEnabled"),
    ),
    ("Meshing", ),  # separator
    (
        "zPolyCombine",
        "Will combine multiple polySets into a single polySet.",
        lambda: cmds.zPolyCombine(),
    ),
    (
        "Extract RestShape",
        "Extracts a new shape from a simulated mesh + sculpted mesh that can be used as a Rest Shape target",
        lambda: cmds.zRestShape(pg=True),
    ),
    ("Mesh Inspection", ),  # separator
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
    ("Proximity Tools", ),  # separator
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
    ("Naming Tools", ),  # separator
    (
        "Rename Ziva Nodes",
        "Rename Ziva nodes in scene.",
        lambda: rename_ziva_nodes(),
    ),
)

_menubar_dict["Help"] = (
    (
        "Ziva Command Help",
        "Print Ziva command help to the Maya script editor.",
        lambda: logger.info(cmds.ziva(h=True)),
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
    (),  # separator
    (
        "About",
        "About the Ziva Maya plug-in.",
        lambda: logger.info(cmds.ziva(z=True)),
    ),
    (
        "Online Resources",
        "Loads Ziva resource library.",
        lambda: cmds.launch(webPage="http://zivadynamics.com/resource-library"),
    ),
)


def _add_menu_actions(zGeo_widget_inst, menu, text, statusbar_text, slot, icon_name=None):
    action = QtWidgets.QAction(menu)
    action.setText(text)
    action.setStatusTip(statusbar_text)
    if callable(slot):  # If it's a normal function, bind it directly
        action.triggered.connect(slot)
    else:
        # If this is a tuple, that means it's a class member function.
        # bind with widget instance first
        action.triggered.connect(partial(slot[0], zGeo_widget_inst))

    if icon_name:
        icon = QtGui.QIcon()
        icon_path = get_icon_path_from_name(icon_name)
        icon.addPixmap(QtGui.QPixmap(icon_path))
        action.setIcon(icon)
    menu.addAction(action)


def _create_menu(zGeo_widget_inst, menubar, menu_name, menu_action_tuple):
    menu = menubar.addMenu(menu_name)
    menu.setToolTipsVisible(True)
    for item in menu_action_tuple:
        if item:
            if isinstance(item, tuple) and len(item) > 1:
                _add_menu_actions(zGeo_widget_inst, menu, *item)
            elif item and isinstance(item, tuple) and len(item) == 1:
                menu.addSection(item[0])
            elif isinstance(item, dict):
                for name, actions in item.items():
                    _create_menu(zGeo_widget_inst, menu, name, actions)
        else:  # empty tuple means a separator
            menu.addSeparator()


def setup_menubar(zGeo_widget_inst):
    """ Entry function to create the toolbar.

    Args:
        parent: parent widget the menu bar belongs to.

    Returns:
        Menubar layout instance.
    """
    menubar = QtWidgets.QMenuBar()
    for name, actions in _menubar_dict.items():
        _create_menu(zGeo_widget_inst, menubar, name, actions)
    # restrict the size of the menubar to prevent uneven expansion
    menubar.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
    lytMenuBar = QtWidgets.QHBoxLayout()
    lytMenuBar.addWidget(menubar)
    lytMenuBar.setAlignment(menubar, QtCore.Qt.AlignRight)
    return lytMenuBar
