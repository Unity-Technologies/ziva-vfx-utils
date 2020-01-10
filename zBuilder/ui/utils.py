from maya import cmds
from maya import OpenMayaUI as mui
from shiboken2 import wrapInstance
from PySide2 import QtGui, QtWidgets, QtCore
import logging

logger = logging.getLogger(__name__)


def dock_window(dialog_class, *args, **kwargs):
    try:
        cmds.deleteUI(dialog_class.CONTROL_NAME)
        logger.info('removed workspace {}'.format(dialog_class.CONTROL_NAME))
    except:
        pass

    # building the workspace control with maya.cmds
    main_control = cmds.workspaceControl(dialog_class.CONTROL_NAME,
                                         ttc=["AttributeEditor", -1],
                                         iw=300,
                                         mw=100,
                                         wp='preferred',
                                         label=dialog_class.DOCK_LABEL_NAME)

    # after maya is ready we should restore the window since it may not be visible
    cmds.evalDeferred(lambda *args: cmds.workspaceControl(main_control, e=True, rs=True))

    # now lets get a C++ pointer to it using OpenMaya
    control_widget = mui.MQtUtil.findControl(dialog_class.CONTROL_NAME)
    # conver the C++ pointer to Qt object we can use
    control_wrap = wrapInstance(long(control_widget), QtWidgets.QWidget)

    # control_wrap is the widget of the docking window and now we can start working with it:
    control_wrap.setAttribute(QtCore.Qt.WA_DeleteOnClose)

    return dialog_class(control_wrap, *args, **kwargs)
