""" Helper functions to setup Scene Panel 2 toolbar widget.
"""
from .zGeoWidget import zGeoWidget
from ..uiUtils import get_icon_path_from_name
from PySide2 import QtGui, QtWidgets, QtCore
from maya import cmds
from functools import partial

# Toolbar QAction data structure, include following items:
# - Icon name
# - Title text
# - Tooltip text, pass None if not available
# - slot function
_create_section_tuple = (
    ("zSolver", "Create zSolver", None, lambda: cmds.ziva(s=True)),
    ("zTissue", "Create zTissue", None, lambda: cmds.ziva(t=True)),
    ("zBone", "Create zBone", None, lambda: cmds.ziva(b=True)),
    ("zCloth", "Create zCloth", None, lambda: cmds.ziva(c=True)),
    ("zAttachment", "Create zAttachment",
     "Create zAttachment: select source vertices and target object", lambda: cmds.ziva(a=True)),
    ("zCache", "Add zCache", None, lambda: cmds.ziva(acn=True)),
    ("create-group-plus", "Create Group", "Create Group: select tree view items",
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
    ("curve", "Add Fiber Curve", "Add Fiber Curve: select zFiber", cmds.zLineOfActionUtil),
    ("zRivetToBone", "Add zRivetToBone",
     "Add zRivetToBone: select target curve vertex and bone mesh", cmds.zRivetToBone),
)

_edit_section_tuple = (("Refresh", "Refresh the Scene Panel tree view", None,
                        (zGeoWidget.reset_builder, )), )


def _setup_toolbar_action(zGeo_widget_inst, toolbar, name, text, tooltip, slot):
    icon_path = get_icon_path_from_name(name)
    icon = QtGui.QIcon()
    icon.addPixmap(QtGui.QPixmap(icon_path))
    action = QtWidgets.QAction(toolbar)
    action.setText(text)
    action.setIcon(icon)
    if tooltip:
        action.setToolTip(tooltip)

    if callable(slot):  # If it's a normal function, bind it directly
        action.triggered.connect(slot)
    else:
        # If this is a tuple, that means it's a class member function.
        # bind with widget instance first
        action.triggered.connect(partial(slot[0], zGeo_widget_inst))
    return action


def _create_toolbar(zGeo_widget_inst, title, action_tuple):
    """ Create the toolbar and label combo.
    Return the layout that contain both widgets.
    """
    toolbar = QtWidgets.QToolBar()
    toolbar.setIconSize(QtCore.QSize(27, 27))
    toolbar.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
    for item in action_tuple:
        toolbar.addAction(_setup_toolbar_action(zGeo_widget_inst, toolbar, *item))

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
    """
    lytToolbar = QtWidgets.QHBoxLayout()
    lytToolbar.setAlignment(QtCore.Qt.AlignLeft)
    lytToolbar.addLayout(_create_toolbar(zGeo_widget_inst, "Create", _create_section_tuple))
    lytToolbar.addLayout(_create_toolbar(zGeo_widget_inst, "Add", _add_section_tuple))
    lytToolbar.addLayout(_create_toolbar(zGeo_widget_inst, "Edit", _edit_section_tuple))
    return lytToolbar
