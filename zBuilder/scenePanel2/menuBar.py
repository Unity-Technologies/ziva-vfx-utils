from PySide2 import QtWidgets, QtGui
import maya.mel as mel
import zBuilder.utils as utility
from zBuilder.uiUtils import get_icon_path_from_name


class ScenePanel2MenuBar(QtWidgets.QMenuBar):
    def __init__(self, parent=None):
        super(ScenePanel2MenuBar, self).__init__(parent)

        self.setup_menu_items()

    def setup_menu_items(self):
        self.file_menu = self.addMenu("File")
        self.cache_menu = self.addMenu("Cache")
        self.tool_menu = self.addMenu("Tool")
        self.help_menu = self.addMenu("Help")

        # restrict the size of the menubar to prevent uneven expansion
        self.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)

        self.add_file_menu_actions()
        self.add_cache_menu_actions()

    def add_menu_actions(self, menu, action_name, statusbar_text, action_slot):
        action = QtWidgets.QAction(self)
        action.setText(action_name)
        action.setStatusTip(statusbar_text)
        action.triggered.connect(action_slot)
        menu.addAction(action)

    def add_menu_actions_with_icons(self, menu, action_name, statusbar_text, action_slot,
                                    icon_name):
        icon_path = get_icon_path_from_name(icon_name)
        icon = QtGui.QIcon()
        icon.addPixmap(QtGui.QPixmap(icon_path))
        action = QtWidgets.QAction(self)
        action.setText(action_name)
        action.setIcon(icon)
        action.setStatusTip(statusbar_text)
        action.triggered.connect(action_slot)
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

    def add_cache_menu_actions(self):
        self.add_menu_actions_with_icons(
            self.cache_menu, "Create",
            "Adds a cache node to the selected solver. Once a cache node is added, simulations are cached automatically.",
            run_create_cache, "zCache")
        self.add_menu_actions_with_icons(
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


def run_create_cache():
    mel.eval('zica -acn')


def run_clear_cache():
    mel.eval('zCache -c')


def run_load_cache():
    mel.eval('ZivaLoadCache')


def run_save_cache():
    mel.eval('ZivaSaveCache')


def run_select_cache():
    mel.eval("select -r `zQuery -t zCacheTransform`")