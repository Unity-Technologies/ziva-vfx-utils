import maya.OpenMaya as om
import os
import logging
import weakref

from .zGeoWidget import zGeoWidget
from .componentWidget import ComponentWidget
from .menuBar import setup_menubar
from .toolbar import setup_toolbar
from ..uiUtils import dock_window, get_icon_path_from_name
from maya import cmds
from PySide2 import QtWidgets

logger = logging.getLogger(__name__)

DIR_PATH = os.path.dirname(os.path.realpath(__file__)).replace("\\", "/")


class ScenePanel2(QtWidgets.QWidget):
    instances = list()
    CONTROL_NAME = "zfxScenePanel2"
    DOCK_LABEL_NAME = "Ziva VFX Scene Panel 2"

    @staticmethod
    def delete_instances():
        for ins in ScenePanel2.instances:
            try:
                ins.remove_callbacks()
                ins.setParent(None)
                ins.deleteLater()
            except:
                # ignore the fact that the actual parent has already been
                # deleted by Maya...
                pass

            ScenePanel2.instances.remove(ins)
            del ins

    def __init__(self, parent=None):
        super(ScenePanel2, self).__init__(parent)

        # let's keep track of our docks so we only have one at a time.
        ScenePanel2.delete_instances()
        ScenePanel2.instances.append(weakref.proxy(self))
        cmds.workspaceControlState(ScenePanel2.CONTROL_NAME, widthHeight=[500, 600])

        # Register callbacks for scene save/load
        logger.debug("Register Scene Panel callbacks.")
        cmds.scriptJob(event=["PostSceneRead", self.on_post_scene_read])
        cmds.scriptJob(event=["NewSceneOpened", self.on_new_scene_opened])
        self._callback_id_list = []
        self._callback_id_list.append(
            om.MSceneMessage.addCallback(om.MSceneMessage.kBeforeSave, self.on_scene_presave))
        self._callback_id_list.append(
            om.MSceneMessage.addStringArrayCallback(om.MSceneMessage.kBeforePluginUnload,
                                                    self.on_scene_prePluginUnload))

        # member variable declaration and initialization
        self._wgtGeo = zGeoWidget(self)
        self._wgtComponent = ComponentWidget(self)

        self._setup_ui(parent)
        self._wgtGeo.set_component_widget(self._wgtComponent)
        self._is_ziva_vfx_loaded = "ziva" in cmds.pluginInfo(query=True, listPlugins=True)
        if self._is_ziva_vfx_loaded:
            self._wgtGeo.reset_builder(True)
        else:
            logger.warning(
                "Ziva VFX plugin is not loaded. The Scene Panel 2 will not work normally.")

    def _setup_ui(self, parent):
        lytMenuBar = setup_menubar(self._wgtGeo)
        lytToolbar = setup_toolbar(self._wgtGeo)

        # zGeo widget(left panel)
        lytGeo = QtWidgets.QVBoxLayout()
        lytGeo.setSpacing(0)
        lytGeo.setContentsMargins(0, 0, 0, 0)
        lytGeo.addWidget(self._wgtGeo)
        grpGeo = QtWidgets.QGroupBox("Scene View")
        grpGeo.setLayout(lytGeo)

        # component widget(right panel)
        lytComponent = QtWidgets.QVBoxLayout()
        lytComponent.setSpacing(0)
        lytComponent.setContentsMargins(0, 0, 0, 0)
        lytComponent.addWidget(self._wgtComponent)
        grpComponent = QtWidgets.QGroupBox("Component View")
        grpComponent.setLayout(lytComponent)

        splTreeView = QtWidgets.QSplitter(self)
        splTreeView.addWidget(grpGeo)
        splTreeView.addWidget(grpComponent)

        lytTwoPanel = QtWidgets.QVBoxLayout()
        lytTwoPanel.setSpacing(0)
        lytTwoPanel.setContentsMargins(0, 0, 0, 0)
        lytTwoPanel.addLayout(lytMenuBar)
        lytTwoPanel.addLayout(lytToolbar)
        lytTwoPanel.addWidget(splTreeView)

        # Load style sheet and append more
        style_sheet = ""
        with open(os.path.join(DIR_PATH, "style.css"), "r") as f:
            style_sheet = f.read()
        pin_state_stylesheet = """
        QTreeView::indicator:checked
        {{
            image: url({}); 
        }}
        QTreeView::indicator:indeterminate
        {{
            image: url({});
        }}
        """.format(get_icon_path_from_name("pinned"), get_icon_path_from_name("partially_pinned"))
        pin_state_stylesheet = pin_state_stylesheet.replace("\\", "//")
        parent.setStyleSheet(style_sheet + pin_state_stylesheet)

        lytMain = parent.layout()
        lytMain.addLayout(lytTwoPanel)

    def remove_callbacks(self):
        logger.debug("Remove Scene Panel callbacks.")
        for callback_id in reversed(self._callback_id_list):
            om.MMessage.removeCallback(callback_id)
        self._callback_id_list = []

    def on_post_scene_read(self):
        """ Callback invoked after Maya load the scene
        """
        if self._is_ziva_vfx_loaded:
            self._wgtGeo.reset_builder(True)

    def on_new_scene_opened(self):
        """ Callback invoked after Maya create the empty scene
        """
        if self._is_ziva_vfx_loaded:
            self._wgtGeo.reset_builder(False)

    def on_scene_presave(self, client_data):
        """ Callback invoked before Maya save the scene
        """
        if self._is_ziva_vfx_loaded:
            self._wgtGeo.save()

    def on_scene_prePluginUnload(self, unload_plugin_list, client_data):
        """ Callback invoked before Maya unload the plugin
        """
        if "ziva" in unload_plugin_list:
            # The Ziva VFX plugin is going to be unloaded,
            # set the flag to stop any further VFX function invocation.
            self._is_ziva_vfx_loaded = False


# Show window with docking ability
def run():
    return dock_window(ScenePanel2)
