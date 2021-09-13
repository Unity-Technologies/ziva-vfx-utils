""" Helper functions to setup Scene Panel 2 toolbar widget.
"""
from ..uiUtils import get_icon_path_from_name
from PySide2 import QtGui, QtWidgets, QtCore
from maya import cmds

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
    ("create-group-plus", "Create Group", "Create Group: select tree view items", None),
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

_edit_section_tuple = (("Refresh", "Refresh the Scene Panel tree view", None, None), )


def _setup_toolbar_action(parent, name, text, tooltip, slot):
    icon_path = get_icon_path_from_name(name)
    icon = QtGui.QIcon()
    icon.addPixmap(QtGui.QPixmap(icon_path))
    action = QtWidgets.QAction(parent)
    action.setText(text)
    action.setIcon(icon)
    if tooltip:
        action.setToolTip(tooltip)
    action.triggered.connect(slot)
    return action


def _create_toolbar(title, action_tuple):
    """ Create the toolbar and label combo.
    Return the layout that contain both widgets.
    """
    toolbar = QtWidgets.QToolBar()
    toolbar.setIconSize(QtCore.QSize(27, 27))
    toolbar.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)
    for item in action_tuple:
        toolbar.addAction(_setup_toolbar_action(toolbar, *item))

    lblTitle = QtWidgets.QLabel(title)
    lblTitle.setSizePolicy(QtWidgets.QSizePolicy.Fixed, QtWidgets.QSizePolicy.Fixed)

    lytContainer = QtWidgets.QVBoxLayout()
    lytContainer.addWidget(lblTitle)
    lytContainer.addWidget(toolbar)
    return lytContainer


def setup_toolbar():
    lytToolbar = QtWidgets.QHBoxLayout()
    lytToolbar.setAlignment(QtCore.Qt.AlignLeft)
    lytToolbar.addLayout(_create_toolbar("Create", _create_section_tuple))
    lytToolbar.addLayout(_create_toolbar("Add", _add_section_tuple))
    lytToolbar.addLayout(_create_toolbar("Edit", _edit_section_tuple))
    return lytToolbar
