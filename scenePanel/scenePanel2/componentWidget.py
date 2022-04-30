import logging

from collections import OrderedDict
from maya import cmds
from PySide2 import QtCore, QtGui, QtWidgets
from zBuilder.utils.commonUtils import is_sequence
from ..uiUtils import get_icon_path_from_name, nodeRole
from .componentContextMenu import create_attr_context_menu, create_attr_map_context_menu
from .componentContextMenu import create_fiber_context_menu, create_attachment_context_menu
from .componentTreeModel import ComponentTreeModel
from .zTreeView import zTreeView
from .treeItem import TreeItem, build_scene_panel_tree

logger = logging.getLogger(__name__)

# global dictionary for storing component widget heights
component_height_dict = {}

# global dictionary for storing component folding state
component_fold_state_dict = {}


class ComponentSectionWidget(QtWidgets.QWidget):
    """ Widget contains component tree view and affiliated title bar
    """

    def __init__(self, component_type, tree_model, parent=None):
        super(ComponentSectionWidget, self).__init__(parent)
        self._parent = parent
        self._component_type = component_type
        # The following UI layout refer to
        # https://stackoverflow.com/questions/32476006/how-to-make-an-expandable-collapsable-section-widget-in-qt

        # Title
        # Concantenate type list and exclude those start with "ui_"
        title = "/".join(filter(lambda t: not t.startswith("ui_"),
                                self._component_type)) if is_sequence(
                                    self._component_type) else self._component_type
        self._btnFold = QtWidgets.QToolButton()
        self._btnFold.setStyleSheet("QToolButton { border: none; }")
        self._btnFold.setToolButtonStyle(QtCore.Qt.ToolButtonTextBesideIcon)
        self._btnFold.setArrowType(QtCore.Qt.DownArrow)
        self._btnFold.setText(title)
        self._btnFold.setCheckable(True)
        # set fold value according to saved value, if any
        if self._component_type in component_fold_state_dict:
            self._btnFold.setChecked(component_fold_state_dict[self._component_type])
        else:
            self._btnFold.setChecked(False)  # expanded by default

        headerLine = QtWidgets.QFrame()
        headerLine.setFrameShape(QtWidgets.QFrame.HLine)
        headerLine.setFrameShadow(QtWidgets.QFrame.Sunken)
        headerLine.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Maximum)

        # Icons
        def create_icon(component_name, parent_layout):
            lblIcon = QtWidgets.QLabel()
            comp_img = QtGui.QPixmap(get_icon_path_from_name(component_name)).scaled(
                16, 16, QtCore.Qt.KeepAspectRatio, QtCore.Qt.SmoothTransformation)
            lblIcon.setPixmap(comp_img)
            lblIcon.setSizePolicy(QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Fixed)
            parent_layout.addWidget(lblIcon)
            parent_layout.setAlignment(lblIcon, QtCore.Qt.AlignRight)

        lytIcons = QtWidgets.QHBoxLayout()
        lytIcons.setSpacing(0)
        lytIcons.setContentsMargins(0, 0, 0, 0)
        if is_sequence(self._component_type):
            for component in self._component_type:
                create_icon(component, lytIcons)
        else:
            create_icon(self._component_type, lytIcons)

        lytTitle = QtWidgets.QHBoxLayout()
        lytTitle.setSpacing(0)
        lytTitle.setContentsMargins(0, 0, 0, 0)
        lytTitle.addWidget(self._btnFold)
        lytTitle.addWidget(headerLine)
        lytTitle.addLayout(lytIcons)

        # Tree view
        self._tvComponent = zTreeView()
        self._tvComponent.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self._tvComponent.customContextMenuRequested.connect(self._create_context_menu)
        self._tvComponent.setModel(tree_model)
        self._tvComponent.expandAll()
        self._tvComponent.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)

        lytSection = QtWidgets.QVBoxLayout()
        lytSection.setSpacing(0)
        lytSection.setContentsMargins(0, 0, 0, 0)
        lytSection.addLayout(lytTitle)
        lytSection.addWidget(self._tvComponent)
        self.setLayout(lytSection)

        self._setup_actions()

    def _create_context_menu(self, position):
        indexes = self._tvComponent.selectedIndexes()
        # TODO: Support multiple selection context menu
        if len(indexes) != 1:
            return

        menu_dict = {
            "zTissue": create_attr_context_menu,
            "zBone": create_attr_context_menu,
            "zLineOfAction": create_attr_context_menu,
            "zRestShape": create_attr_context_menu,
            "zTet": create_attr_map_context_menu,
            "zFiber": create_fiber_context_menu,
            "zMaterial": create_attr_map_context_menu,
            "zAttachment": create_attachment_context_menu,
        }

        node = indexes[0].data(nodeRole)
        if node.type in menu_dict:
            method = menu_dict[node.type]
            menu = method(self, node)
            menu.exec_(self._tvComponent.viewport().mapToGlobal(position))

    def _on_tvComponent_selectionChanged(self, selected, deselected):
        """
        When the tree selection changes this gets executed to select
        corresponding item in Maya scene.
        """
        selection_list = self._tvComponent.selectedIndexes()
        if selection_list:
            nodes = [x.data(nodeRole) for x in selection_list]
            node_names = [x.long_name for x in nodes]
            # find nodes that exist in the scene
            scene_nodes = cmds.ls(node_names, l=True)
            if scene_nodes:
                cmds.select(scene_nodes)

            not_found_nodes = [name for name in node_names if name not in scene_nodes]
            if not_found_nodes:
                cmds.warning(
                    "Nodes {} not found. Try to press refresh button.".format(not_found_nodes))

    def _setup_actions(self):
        self._btnFold.clicked.connect(self._on_btnFold_toggled)
        self._tvComponent.selectionModel().selectionChanged.connect(
            self._on_tvComponent_selectionChanged)
        self._tvComponent.installEventFilter(self)

    def _on_btnFold_toggled(self):
        """ Hide the tree view widget when checked is False, True otherwise
        and adjusts widget heights.
        """
        self.update_widget_visibility(self._btnFold.isChecked())
        # Ask parent to update the whole layout height
        self._parent.on_section_toggled()

    def update_widget_visibility(self, checked):
        """ Hide the tree view widget when checked is False, True otherwise.
        """
        self._btnFold.setArrowType(QtCore.Qt.RightArrow if checked else QtCore.Qt.DownArrow)
        self._tvComponent.setVisible(not checked)

    # Public functions
    def select_source_and_target(self):
        indexes = self._tvComponent.selectedIndexes()[0]
        node = indexes.data(nodeRole)
        cmds.select(node.nice_association)

    def get_height(self):
        """ Return widget height according to fold button state.
        This is for compute the ComponentWidget's place holder control height.
        """
        if self._btnFold.isChecked():
            return self._btnFold.height()
        return self._btnFold.height() + self._tvComponent.height()

    # Override
    def eventFilter(self, obj, event):
        """ Handle key press event for TreeViews
        """
        if event.type() == QtCore.QEvent.KeyPress:
            if (obj is self._tvComponent) and (event.key() == QtCore.Qt.Key_Delete):
                # Mute delete key event on component tree view
                # TODO: handle component-wise deletion
                return True

        # standard event processing
        return QtCore.QObject.eventFilter(self, obj, event)

    def resizeEvent(self, event):
        """Detect a resize event only when an exiting item has been changed in length.
        """
        if not event.oldSize().isEmpty() and event.oldSize().width() == event.size().width(
        ) and event.oldSize().height() != event.size().height():
            component_height_dict[self._component_type] = event.size().height()


# Component for each zGeo node
component_type_dict = {
    "ui_zBone_body": ["zAttachment", "zBone"],
    "ui_zTissue_body": [
        ("zTet", "zTissue", "zRestShape", "ui_target_body"),
        "zMaterial",
        "zAttachment",
        ("zFiber", "zLineOfAction", "zRivetToBone", "ui_curve_body"),
    ],
    "ui_zCloth_body": ["zCloth", "zMaterial", "zAttachment"]
}


class ComponentWidget(QtWidgets.QWidget):
    """ The Component tree view widget.
    It contains a ComponentSectionWidget list, which include each component of current selected nodes.
    """

    def __init__(self, parent=None):
        super(ComponentWidget, self).__init__(parent)
        # setup data
        self._component_nodes_dict = OrderedDict()
        self._component_tree_model_dict = OrderedDict()
        # setup ui
        self._lytAllSections = QtWidgets.QVBoxLayout(self)
        self.setLayout(self._lytAllSections)

    def reset_model(self, builder, new_selection):
        self._component_nodes_dict.clear()
        self._component_tree_model_dict.clear()
        while self._lytAllSections.count() > 0:
            lytItem = self._lytAllSections.takeAt(0)
            lytItem.widget().deleteLater()

        if len(new_selection) == 0:
            return  # Early return if nothing to show

        for node in new_selection:
            for component in component_type_dict[node.type]:
                self._component_nodes_dict.setdefault(component, []).append(node)

        for component_type, node_list in self._component_nodes_dict.items():
            root_node = TreeItem()
            has_data = False
            for node in node_list:
                child_nodes = build_scene_panel_tree(
                    node, component_type if is_sequence(component_type) else [component_type])
                if child_nodes:
                    zGeo_node = TreeItem(root_node, node)
                    zGeo_node.append_children(child_nodes)
                    has_data = True
            if has_data:
                self._component_tree_model_dict[component_type] = ComponentTreeModel(
                    builder, root_node)

        self._splitter = QtWidgets.QSplitter(QtCore.Qt.Vertical)
        self._splitter.setChildrenCollapsible(False)
        self._splitter.setHandleWidth(2)
        for component_type, tree_model in self._component_tree_model_dict.items():
            wgtSection = ComponentSectionWidget(component_type, tree_model, self)
            self._splitter.addWidget(wgtSection)

        # Append the extra place holder control at the end to compact free space
        # when ComponentSectionWidget are folded.
        place_holder = QtWidgets.QFrame()
        place_holder.setFrameShape(QtWidgets.QFrame.NoFrame)
        place_holder.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
        self._splitter.addWidget(place_holder)

        # restore widgets to saved height and folding state
        self._restore_comopnent_widget_state()

        self._lytAllSections.addWidget(self._splitter)

    def on_section_toggled(self):
        """ Update each section widget height according to fold state,
        to make their space compact.
        """
        new_widget_heights = []
        for i in range(self._splitter.count() - 1):
            # Add extra padding to prevent section widget height creeping
            # when clicking the fold button repeatedly.
            # This is an empirical value by trial-and-error.
            new_height = self._splitter.widget(i).get_height() + self._splitter.handleWidth()
            new_widget_heights.append(new_height)

        place_holder_height = self.height() - sum(new_widget_heights)
        new_widget_heights.append(place_holder_height)
        self._splitter.setSizes(new_widget_heights)
        self._store_comopnent_widget_state()

    def _store_comopnent_widget_state(self):
        """ Store widget height and folding state in corresponding
        global dictionaries.
        """
        # We use two seperate dictionaries for height and folding state,
        # because while folding activity has effect on widget height, resizing
        # of widget height has no effect on folding. By keeping these separate,
        # we can identify only modified widget for each of these states.
        for i in range(self._splitter.count() - 1):
            widget = self._splitter.widget(i)
            component_fold_state_dict[widget._component_type] = widget._btnFold.isChecked()
            # update height after fold
            if widget._btnFold.isChecked():
                component_height_dict[widget._component_type] = widget.get_height()

    def _restore_comopnent_widget_state(self):
        """ Restore widget height and folding state as recorded in corresponding
        global dictionaries.
        """
        heights = self._splitter.sizes()

        # the size of 'self._component_nodes_dict' should match with the length of items
        # in the splitter minus one (tail splitter). If not, something went wrong. But we
        # don't report an error because QtWidgets.QSplitter.setSizes() can robustly tackle
        # such case.
        if len(heights) == 0 or len(self._component_nodes_dict) != len(heights) - 1:
            self._splitter.setSizes(heights)
            return

        for idx, key in enumerate(self._component_nodes_dict):
            if isinstance(self._splitter.widget(idx), ComponentSectionWidget):
                # update height list if item in global dictionary
                if key in component_height_dict:
                    heights[idx] = component_height_dict[key]
                # update widget folding state if a stored value is available
                if key in component_fold_state_dict:
                    self._splitter.widget(idx).update_widget_visibility(
                        component_fold_state_dict[key])

        # suggest end splitter height based on rest of the widgets
        place_holder_height = self.height() - sum(heights)
        heights.append(place_holder_height)

        # update height of all widgets in the splitter
        self._splitter.setSizes(heights)
