from .model import SceneGraphModel, zGeoFilterProxyModel, SelectedGeoListModel
from .zGeoView import zGeoTreeView
from maya import cmds
from PySide2 import QtGui, QtWidgets, QtCore
import zBuilder.builders.ziva as zva
from zBuilder.uiUtils import nodeRole, longNameRole, dock_window, get_icon_path_from_name
import os
import weakref
import logging

####for collapse widget###
#from PySide2 import QScrollArea 

logger = logging.getLogger(__name__)

DIR_PATH = os.path.dirname(os.path.realpath(__file__)).replace("\\", "/")

class ScenePanel2(QtWidgets.QWidget):
    instances = list()
    CONTROL_NAME = 'zfxScenePanel2'
    DOCK_LABEL_NAME = 'Ziva VFX Scene Panel 2'

    @staticmethod
    def delete_instances():
        for ins in ScenePanel2.instances:
            try:
                ins.setParent(None)
                ins.deleteLater()
            except:
                # ignore the fact that the actual parent has already been
                # deleted by Maya...
                pass

            ScenePanel2.instances.remove(ins)
            del ins

    def __init__(self, parent=None, builder=None):
        super(ScenePanel2, self).__init__(parent)

        # let's keep track of our docks so we only have one at a time.
        ScenePanel2.delete_instances()
        ScenePanel2.instances.append(weakref.proxy(self))
        cmds.workspaceControlState(ScenePanel2.CONTROL_NAME, widthHeight=[500, 600])

        self._setup_ui(parent)
        self._setup_model(builder)
        # must be after _setup_model() because assigning model resets item expansion
        self._set_builder(self._builder)
        self._setup_actions()

    def _setup_model(self, builder):
        self._builder = builder or zva.Ziva()
        self._builder.retrieve_connections()

        self._sceneGraphModel = SceneGraphModel(self._builder, self)
        self._proxy_model = zGeoFilterProxyModel()
        self._proxy_model.setSourceModel(self._sceneGraphModel)
        self._proxy_model.setDynamicSortFilter(True)
        self._proxy_model.setFilterCaseSensitivity(QtCore.Qt.CaseInsensitive)
        self._tvGeo.setModel(self._proxy_model)

        self._selectedGeoModel = SelectedGeoListModel(self)
        self._lvComponent.setModel(self._selectedGeoModel)

    def _set_builder(self, builder):
        """
        This builds and/or resets the tree given a builder.
        The builder is a zBuilder object that the tree is built from.
        If None is passed it uses the scene selection to build a new builder.
        This forces a complete redraw of the ui tree.

        Args:
            builder (:obj:`obj`): The zBuilder builder to build tree from.
        """

        if not builder:
            # reset builder
            self._builder = zva.Ziva()
            self._builder.retrieve_connections()
            builder = self._builder

        self._sceneGraphModel.beginResetModel()
        self._sceneGraphModel.builder = builder
        self._sceneGraphModel.endResetModel()

    def _setup_ui(self, parent):
        self.toolbar = QtWidgets.QToolBar(self)
        self.toolbar.setIconSize(QtCore.QSize(27, 27))
        self.toolbar.setObjectName("toolBar")
        lytToolbar = QtWidgets.QHBoxLayout()
        lytToolbar.addWidget(self.toolbar)

        self._tvGeo = zGeoTreeView(self)
        self._tvGeo.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        self._tvGeo.setIndentation(15)
        # changing header size
        # this used to create some space between left/top side of the tree view and it items
        # "razzle dazzle" but the only way I could handle that
        # height - defines padding from top
        # offset - defines padding from left
        # opposite value of offset should be applied in view.py in drawBranches method
        header = self._tvGeo.header()
        header.setOffset(-zGeoTreeView.offset)
        header.setFixedHeight(10)

        lytGeo = QtWidgets.QVBoxLayout()
        lytGeo.addWidget(self._tvGeo)
        grpGeo = QtWidgets.QGroupBox("Scene Panel")
        grpGeo.setLayout(lytGeo)
        
        self._lvComponent = QtWidgets.QListView(self)
        self._lvComponent.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
        lytComponent = QtWidgets.QVBoxLayout()
        lytComponent.addWidget(self._lvComponent)
        grpComponent = QtWidgets.QGroupBox("Component")
        grpComponent.setLayout(lytComponent)

        splTreeView = QtWidgets.QSplitter(self)
        splTreeView.addWidget(grpGeo)
        splTreeView.addWidget(grpComponent)
        

        lytTwoPanel = QtWidgets.QVBoxLayout()
        lytTwoPanel.addLayout(lytToolbar)
        lytTwoPanel.addWidget(splTreeView)
        self.collapseWidget =  CollapsibleDialog()#CollapseWidget()  
        lytTwoPanel.addWidget(self.collapseWidget)
        with open(os.path.join(DIR_PATH, "style.css"), "r") as f:
            style_sheet = f.read()
            parent.setStyleSheet(style_sheet)

        lytMain = parent.layout()
        lytMain.addLayout(lytTwoPanel)

    def _setup_actions(self):
        refresh_path = get_icon_path_from_name('refresh')
        refresh_icon = QtGui.QIcon()
        refresh_icon.addPixmap(QtGui.QPixmap(refresh_path), QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.actionRefresh = QtWidgets.QAction(self)
        self.actionRefresh.setText('Refresh')
        self.actionRefresh.setIcon(refresh_icon)
        self.actionRefresh.setObjectName("actionRefresh")
        self.actionRefresh.triggered.connect(self._set_builder)
        self.toolbar.addAction(self.actionRefresh)

        self._tvGeo.selectionModel().selectionChanged.connect(self.on__tvGeo_selectionChanged)

    def on__tvGeo_selectionChanged(self, selected, deselected):
        """
        When the tree selection changes this gets executed to select
        corresponding item in Maya scene.
        """
        selectedIndexList = selected.indexes()
        self._selectedGeoModel.beginResetModel()
        #self._selectedGeoModel.setNewSelection(selectedIndexList)
        self._selectedGeoModel.endResetModel()
        for selectedItem in selectedIndexList:
            logger.info("selectedItem = {}".format(selectedItem))

        if selectedIndexList:
            nodes = [x.data(nodeRole) for x in selectedIndexList]
            node_names = [x.long_name for x in nodes]
            # find nodes that exist in the scene
            scene_nodes = cmds.ls(node_names, l=True)
            if scene_nodes:
                cmds.select(scene_nodes)

            not_found_nodes = [name for name in node_names if name not in scene_nodes]
            if not_found_nodes:
                cmds.warning(
                    "Nodes {} not found. Try to press refresh button.".format(not_found_nodes))

    def get_expanded(self):
        """
        Returns: array of item names that are currently expanded in zGeoTreeView
        """
        # store currently expanded items
        expanded = []
        for index in self._proxy_model.persistentIndexList():
            if self._tvGeo.isExpanded(index):
                expanded.append(index.data(longNameRole))

        return expanded

    def expand(self, names):
        """
        Args:
            names (list): names to expand in zGeoTreeView
        """
        # collapseAll added in case refreshing of zGeoTreeView needed
        # otherwise new items might not be displayed ( Qt bug )
        self._tvGeo.collapseAll()
        for name in names:
            indexes = self._proxy_model.match(self._proxy_model.index(0, 0),
                                              longNameRole, name, -1,
                                              QtCore.Qt.MatchExactly | QtCore.Qt.MatchRecursive)
            for index in indexes:
                self._tvGeo.expand(index)

class SectionExpandButton(QtWidgets.QToolButton):
    """a QPushbutton that can expand or collapse its section
    """
    def __init__(self, item, title, icon_path, parent = None):
        super().__init__(parent)
        self.section = item
        self.setToolButtonStyle(QtCore.Qt.ToolButtonTextBesideIcon)
        self.setArrowType(QtCore.Qt.RightArrow)
        self.setCheckable(True)
        act = QtWidgets.QAction();
        act.setIcon(QtGui.QIcon(icon_path))
        act.setText(title)
        self.setDefaultAction(act)

        self.setChecked(False)
        self.clicked.connect(self.on_clicked)

    def on_clicked(self):
        """toggle expand/collapse of section by clicking
        """
        if self.section.isExpanded():
            self.section.setExpanded(False)
        else:
            self.section.setExpanded(True)
        #arrow_type = QtCore.Qt.DownArrow if checked else QtCore.Qt.RightArrow
        #direction = QtCore.QAbstractAnimation.Forward if checked else QtCore.QAbstractAnimation.Backward
        #toggleButton.setArrowType(arrow_type)
        #self.toggleAnimation.setDirection(direction)
        #self.toggleAnimation.start()

class CollapsibleDialog(QtWidgets.QDialog):
    """a dialog to which collapsible sections can be added;
    subclass and reimplement define_sections() to define sections and
        add them as (title, widget) tuples to self.sections
    """
    def __init__(self):
        super().__init__()
        self.tree = QtWidgets.QTreeWidget()
        self.tree.setHeaderHidden(True)
        self.main_layout = QtWidgets.QVBoxLayout()
        self.main_layout.addWidget(self.tree)
        self.setLayout(self.main_layout)
        self.tree.setIndentation(0)
        self.sections = []
        self.define_sections()
        self.add_sections()

    def add_sections(self):
        """adds a collapsible sections for every 
        (title, widget) tuple in self.sections
        """
        for (title, widget) in self.sections:
            button = self.add_button(title)
            section = self.add_widget(button, widget)
            button.addChild(section)

    def define_sections(self):
        """reimplement this to define all your sections
        and add them as (title, widget) tuples to self.sections
        """
        widget1 = QtWidgets.QFrame(self.tree)
        layout1 = QtWidgets.QVBoxLayout(widget1)
        layout1.addWidget(QtWidgets.QLabel("material1"))
        layout1.addWidget(QtWidgets.QLabel("material2"))
        title1 = "materials"
        self.sections.append((title1, widget1))

        widget2 = QtWidgets.QFrame(self.tree)
        layout2 = QtWidgets.QVBoxLayout(widget2)

        # add splitter
        #splitter = QtWidgets.QSplitter(QtCore.Qt.Horizontal)
        #splitter.setSizes([100, 200])
        #self.add_widget(splitter)

        layout2.addWidget(QtWidgets.QLabel("attachment1"))
        layout2.addWidget(QtWidgets.QLabel("attachment2"))
        title2 = "attachments"
        self.sections.append((title2, widget2))

    def add_button(self, title):
        """creates a QTreeWidgetItem containing a button 
        to expand or collapse its section
        """
        item = QtWidgets.QTreeWidgetItem()
        self.tree.addTopLevelItem(item)
        icon_path = get_icon_path_from_name('vline')
        self.tree.setItemWidget(item, 0, SectionExpandButton(item, title, icon_path))
        return item

    def add_widget(self, button, widget):
        """creates a QWidgetItem containing the widget,
        as child of the button-QWidgetItem
        """
        section = QtWidgets.QTreeWidgetItem(button)
        section.setDisabled(True)
        self.tree.setItemWidget(section, 0, widget)
        return section


# Show window with docking ability
def run():
    return dock_window(ScenePanel2)
