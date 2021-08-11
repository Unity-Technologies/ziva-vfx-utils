import zBuilder.utils as utility
import maya.mel as mel
import zBuilder.utils as utility

from PySide2 import QtWidgets, QtGui
from maya import cmds, mel
from utility.licenseRegister import licenseRegisterWidget
from zBuilder.uiUtils import get_icon_path_from_name





class ScenePanel2MenuBar(QtWidgets.QMenuBar):
    def __init__(self, parent=None):
        super(ScenePanel2MenuBar, self).__init__(parent)

        self.setup_menu_items()

    def setup_menu_items(self):
        self.file_menu = self.addMenu("File")
        self.cache_menu = self.addMenu("Cache")
        self.tool_menu = self.addMenu("Tools")
        self.help_menu = self.addMenu("Help")

        # restrict the size of the menubar to prevent uneven expansion
        self.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)

        self.add_file_menu_actions()

        self.add_tool_menu_actions()

        self.add_cache_menu_actions()
        self.add_help_menu_actions()

    def add_menu_actions(self, menu, action_name, statusbar_text, action_slot, icon_name=None):
        action = QtWidgets.QAction(self)
        action.setText(action_name)
        action.setStatusTip(statusbar_text)
        action.triggered.connect(action_slot)
        if icon_name:
            icon_path = get_icon_path_from_name(icon_name)
            icon = QtGui.QIcon()
            icon.addPixmap(QtGui.QPixmap(icon_path))
            action.setIcon(icon)
        menu.addAction(action)

    def add_file_menu_actions(self):
        self.add_menu_actions(
            self.file_menu, "Load...",
            "Load a Ziva rig from a file, into a new solver, or a specified existing solver. Geometry must already be present in the scene.",
            run_load_rig_options)
        self.add_menu_actions(
            self.file_menu, "Save...",
            "Save a Ziva rig for the selected solver to a file. If multiple solvers are selected, only the first solver is saved",
            run_save_rig_options)
        self.add_menu_actions(
            self.file_menu, "Cut",
            "Cut the Ziva rig in selected objects to the Ziva clipboard. Selected objects must come from exactly one solver. Selected objects may contain a solver node.",
            run_rig_cut)
        self.add_menu_actions(
            self.file_menu, "Copy",
            "Copy the Ziva rig in selected objects to the Ziva clipboard. Selected objects must come from exactly one solver. Selected objects may contain a solver node.",
            run_rig_copy)
        self.add_menu_actions(
            self.file_menu, "Paste",
            "Paste the Ziva rig from the Ziva clipboard onto scene geometry, into the solver stored in the Ziva clipboard. If such a solver does not exist in the scene, it is created.",
            run_rig_paste)
        self.file_menu.addSeparator()
        self.add_menu_actions(
            self.file_menu, "Copy/Paste With Name Substitution...",
            "Copy/pastes Ziva rig items using a name substitution (defined via regular expressions). Useful for mirroring the Ziva rig from one side of a character onto the other. Select the objects whose Ziva rig is to be copy/pasted. Selected objects should come from exactly one solver.",
            run_rig_copy_paste_with_name_substitution_options)
        self.add_menu_actions(
            self.file_menu, "Update",
            "Update Ziva rig in the selected solver to use the current geometry. Useful if you modified geometry after converting it to Ziva bodies. This updates the solver to use the new geometry.",
            run_rig_update)
        self.add_menu_actions(
            self.file_menu, "Transfer...",
            "Transfer Ziva rig from one solver into another. Two copies of geometries must exist in the scene; the target copies must be prefixed with a specified prefix.",
            run_rig_transfer_options)

    def add_help_menu_actions(self):
        self.add_menu_actions(self.help_menu, "Ziva Command Help",
                              "Print Ziva command help to the Maya script editor.",
                              run_ziva_command_help)

        self.run_demo_sub_menu = self.help_menu.addMenu("Run Demo")
        self.add_menu_actions(self.run_demo_sub_menu, "Anatomical Arm",
                              "Demonstrates an anatomical human arm.", run_anatomical_arm_demo)
        self.add_menu_actions(
            self.run_demo_sub_menu,
            "Goaling, Self-Collisions, Ziva Cache and Spatially Varying Materials",
            "Demonstrates goaling, self-collisions, Ziva caching, and spatially varying materials, on a Maya-rigged fish example.",
            run_goaling_self_collisions_demo)
        self.add_menu_actions(
            self.run_demo_sub_menu, "Self-Collisions, Ziva Cache and Delaunay Tet Mesher",
            "Demonstrates self-collisions, Ziva cache and the Delaunay tet mesher.",
            run_self_collisions_demo)
        self.add_menu_actions(self.run_demo_sub_menu, "Attachments", "Demonstrates attachments.",
                              run_attachments_demo)
        self.add_menu_actions(self.run_demo_sub_menu, "Collisions", "Demonstrates collisions",
                              run_collisions_demo)
        self.add_menu_actions(self.run_demo_sub_menu, "One Of Each Attachments",
                              "Demonstrates one of each of the four attachment types.",
                              run_one_of_each_attachments_demo)
        self.add_menu_actions(self.run_demo_sub_menu, "One Of Each Collision Types",
                              "Demonstrates one of each of the four collision types.",
                              run_one_of_each_collisions_demo)
        self.add_menu_actions(self.run_demo_sub_menu, "Spatially Varying Materials",
                              "Demonstrates spatially varying materials.",
                              run_spatially_varying_materials_demo)
        self.add_menu_actions(self.run_demo_sub_menu, "Cloth",
                              "Demonstrates cloth and cloth-object collisions.", run_cloth_demo)
        self.add_menu_actions(self.run_demo_sub_menu, "Cloth Rest Scale and Pressure",
                              "Demonstrates cloth rest scale and pressure.",
                              run_rest_scale_and_pressure_demo)
        self.add_menu_actions(self.run_demo_sub_menu, "Isomesher",
                              "Demonstrates the Ziva isomesher.", run_isomesher_demo)
        self.add_menu_actions(self.help_menu, "Register License...", "Register Ziva VFX license.",
                              run_register_license)
        self.add_menu_actions(self.help_menu, "About", "About the Ziva Maya plug-in.", run_about)
        self.add_menu_actions(self.help_menu, "Online Resources", "Loads Ziva resource library.",
                              run_online_resources)

    def add_tool_menu_actions(self):
        self.add_menu_actions(self.tool_menu, "Merge Solvers", "Merges selected solvers into one.",
                              run_merge_solvers)
        self.add_menu_actions(self.tool_menu, "Toggle Enabled Bodies",
                              "Toggles the active state of the selected Ziva objects.",
                              run_toggle_enabled_bodies)
        self.tool_menu.addSeparator()
        self.add_menu_actions(self.tool_menu, "zPolyCombine",
                              "Will combine multiple polySets into a single polySet.",
                              run_z_poly_combine)
        self.add_menu_actions(self.tool_menu, "Create Line-Of-Action Curve",
                              "Create simple curves from the selected tissues/fibers.",
                              run_create_line_of_action_curve)
        self.add_menu_actions(
            self.tool_menu, "Extract RestShape",
            "Extracts a new shape from a simulated mesh + sculpted mesh that can be used as a Rest Shape target",
            run_extract_rest_shape)
        self.tool_menu.addSeparator()
        self.add_menu_actions(self.tool_menu, "Run Mesh Analysis",
                              "Quality-check the selected mesh(es).", run_mesh_analysis)
        self.add_menu_actions(self.tool_menu, "Find Intersections",
                              "Find intersections between Maya meshes.", run_find_intersections)
        self.add_menu_actions(self.tool_menu, "Find Self Intersections",
                              "Find self-intersections (self-collisions) on a Maya mesh.",
                              run_find_self_intersections)
        self.tool_menu.addSeparator()
        self.add_menu_actions(
            self.tool_menu, "Select Vertices",
            "Selects vertices on the first Maya mesh based on their distance to the second selected Maya mesh.",
            run_select_vertices)
        self.add_menu_actions(
            self.tool_menu, "Paint Attachments By Proximity",
            "For a selected existing attachment, choose new source vertices (and repaint the source attachment map accordingly), by selecting the vertices that are within the specified distance threshold to the attachment target object.",
            run_paint_attachments_by_proximity)

    def add_cache_menu_actions(self):
        self.add_menu_actions(
            self.cache_menu, "Add",
            "Adds a cache node to the selected solver. Once a cache node is added, simulations are cached automatically.",
            run_create_cache, "zCache")
        self.add_menu_actions(
            self.cache_menu, "Clear",
            "Clears the solver's simulation cache. Do this each time before re-running a simulation that was previously cached.",
            run_clear_cache, "clear_zCache")
        self.add_menu_actions(
            self.cache_menu, "Load",
            "Loads a simulation cache from a .zcache disk file and applies it to the current solver.",
            run_load_cache)
        self.add_menu_actions(self.cache_menu, "Save",
                              "Saves the solver's simulation cache to a .zcache file.",
                              run_save_cache)
        self.add_menu_actions(self.cache_menu, "Select",
                              "Select the solver's simulation cache node.", run_select_cache)



def run_load_rig_options():
    mel.eval('zLoadRigOptions()')


def run_save_rig_options():
    mel.eval('zSaveRigOptions()')


def run_rig_cut():
    utility.rig_cut()


def run_rig_copy():
    utility.rig_copy()


def run_rig_paste():
    utility.rig_paste()


def run_rig_copy_paste_with_name_substitution_options():
    mel.eval('zRigCopyPasteWithNameSubstitutionOptions()')


def run_rig_update():
    utility.rig_update()


def run_rig_transfer_options():
    mel.eval('zRigTransferOptions()')


def run_ziva_command_help():
    mel.eval('ziva -h')


def run_register_license():
    licenseRegisterWidget.main()


def run_about():
    mel.eval('ziva -z')


def run_online_resources():
    mel.eval("launch -webPage \"http://zivadynamics.com/resource-library\"")


def run_anatomical_arm_demo():
    mel.eval("ziva_main_anatomicalArmDemo(1)")


def run_goaling_self_collisions_demo():
    mel.eval('ziva_main_goalingDemo(1)')


def run_self_collisions_demo():
    mel.eval('ziva_main_selfCollisionsCacheAndDelaunayTetMesherDemo(1)')


def run_attachments_demo():
    mel.eval('ziva_main_attachmentTest(1)')


def run_collisions_demo():
    mel.eval('ziva_main_collisionTest(1)')


def run_one_of_each_attachments_demo():
    mel.eval('ziva_main_oneOfEachAttachments(1)')


def run_one_of_each_collisions_demo():
    mel.eval('ziva_main_oneOfEachCollisionTypes(1)')


def run_spatially_varying_materials_demo():
    mel.eval('ziva_main_spatiallyVaryingMaterials(1)')


def run_cloth_demo():
    mel.eval('ziva_main_clothDemo(1)')


def run_rest_scale_and_pressure_demo():
    mel.eval('ziva_main_restScalePressureDemo(1)')


def run_isomesher_demo():
    mel.eval('ziva_main_isoMesherDemo(1)')


def run_merge_solvers():
    utility.merge_solvers(cmds.ls(sl=True))


def run_toggle_enabled_bodies():
    mel.eval('ZivaToggleEnabled')


def run_z_poly_combine():
    mel.eval('zPolyCombine')


def run_create_line_of_action_curve():
    mel.eval('zLineOfActionUtil')


def run_extract_rest_shape():
    mel.eval('zRestShape -pg')


def run_mesh_analysis():
    mel.eval('zMeshCheck -select')


def run_find_intersections():
    mel.eval('ZivaSelectIntersections')


def run_find_self_intersections():
    mel.eval('ZivaSelectSelfIntersections')


def run_select_vertices():
    mel.eval('zSelectVerticesByProximityRadius $ZivaSelectByProximityRadiusFloat')


def run_paint_attachments_by_proximity():
    mel.eval(
        'zPaintAttachmentsByProximity -min $ZivaPaintByProximityMinFloat -max $ZivaPaintByProximityMaxFloat'
    )

def run_create_cache():
    mel.eval('ziva -acn')


def run_clear_cache():
    mel.eval('zCache -c')


def run_load_cache():
    mel.eval('ZivaLoadCache')


def run_save_cache():
    mel.eval('ZivaSaveCache')


def run_select_cache():
    mel.eval("select -r `zQuery -t zCacheTransform`")
