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
from PySide2 import QtWidgets, QtCore

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
        self._scene_presave_callback_id = om.MSceneMessage.addCallback(
            om.MSceneMessage.kBeforeSave, self.on_scene_presave)

        # member variable declaration and initialization
        self._wgtGeo = zGeoWidget(self)
        self._wgtComponent = ComponentWidget(self)

        self._setup_ui(parent)
        self._wgtGeo.set_component_widget(self._wgtComponent)
        self._wgtGeo.reset_builder()

    def _setup_ui(self, parent):
        lytMenuBar = setup_menubar(self)
        lytToolbar = setup_toolbar(self._wgtGeo)

        # zGeo widget(left panel)
        lytGeo = QtWidgets.QVBoxLayout()
        lytGeo.addWidget(self._wgtGeo)
        grpGeo = QtWidgets.QGroupBox("Scene Panel")
        grpGeo.setLayout(lytGeo)

        # component widget(right panel)
        lytComponent = QtWidgets.QVBoxLayout()
        lytComponent.addWidget(self._wgtComponent)
        grpComponent = QtWidgets.QGroupBox("Component")
        grpComponent.setLayout(lytComponent)

        splTreeView = QtWidgets.QSplitter(self)
        splTreeView.addWidget(grpGeo)
        splTreeView.addWidget(grpComponent)

        lytTwoPanel = QtWidgets.QVBoxLayout()
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
        QTreeView::indicator:unchecked
        {{
            image: url({});
        }}
        QTreeView::indicator:indeterminate
        {{
            image: url({});
        }}
        """.format(get_icon_path_from_name("pinned"), get_icon_path_from_name("unpinned"),
                   get_icon_path_from_name("partially_pinned"))
        pin_state_stylesheet = pin_state_stylesheet.replace("\\", "//")
        parent.setStyleSheet(style_sheet + pin_state_stylesheet)

        lytMain = parent.layout()
        lytMain.addLayout(lytTwoPanel)

    def remove_callbacks(self):
        logger.debug("Remove Scene Panel callbacks.")
        om.MMessage.removeCallback(self._scene_presave_callback_id)

    def on_post_scene_read(self):
        """ Callback invoked after Maya load the scene
        """
        solver_nodes = cmds.ls(type="zSolver")
        solver_serialized_data_tuple_list = []
        attr = "scenePanelSerializedData"
        for node in solver_nodes:
            attr_exists = cmds.attributeQuery(attr, node=node, exists=True)
            if attr_exists:
                serialized_data = cmds.getAttr("{}.{}".format(node, attr))
                if serialized_data:
                    solver_serialized_data_tuple_list.append(("{}".format(node), serialized_data))
        self._wgtGeo.reset_builder()
        # TODO: resolve conflict

    def on_new_scene_opened(self):
        """ Callback invoked after Maya create the empty scene
        """
        self._wgtGeo.reset_builder()

    def on_scene_presave(self, client_data):
        """ Callback invoked before Maya save the scene
        """
        self._wgtGeo.save()


# Show window with docking ability
def run():
    return dock_window(ScenePanel2)
