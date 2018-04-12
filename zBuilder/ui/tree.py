import weakref

import maya.cmds as cmds
import maya.OpenMayaUI as omui
from shiboken2 import wrapInstance

from Qt import QtGui, QtWidgets, QtCore # https://github.com/mottosso/Qt.py by Marcus Ottosson 

import zBuilder.ui.model as model

import zPipe.settings as anm
import maya.cmds as mc
import logging

logger = logging.getLogger(__name__)


def dock_window(dialog_class, root_node=None):
    try:
        cmds.deleteUI(dialog_class.CONTROL_NAME)
        # logger.info('removed workspace {}'.format(dialog_class.CONTROL_NAME))

    except:
        pass

    # building the workspace control with maya.cmds
    main_control = cmds.workspaceControl(dialog_class.CONTROL_NAME, ttc=["AttributeEditor", -1],iw=300, mw=100, wp='preferred', label = dialog_class.DOCK_LABEL_NAME)

    # now lets get a C++ pointer to it using OpenMaya
    control_widget = omui.MQtUtil.findControl(dialog_class.CONTROL_NAME)
    # conver the C++ pointer to Qt object we can use
    control_wrap = wrapInstance(long(control_widget), QtWidgets.QWidget)

    # control_wrap is the widget of the docking window and now we can start working with it:
    control_wrap.setAttribute(QtCore.Qt.WA_DeleteOnClose)
    win = dialog_class(control_wrap, root_node=root_node)

    # after maya is ready we should restore the window since it may not be visible
    cmds.evalDeferred(lambda *args: cmds.workspaceControl(main_control, e=True, rs=True))
    # will return the class of the dock content.
    return win.run()


class MyDockingUI(QtWidgets.QWidget):

    instances = list()
    CONTROL_NAME = 'zBuilderView'
    DOCK_LABEL_NAME = 'zBuilderView'

    def __init__(self, parent=None, root_node=None):
        super(MyDockingUI, self).__init__(parent)

        # let's keep track of our docks so we only have one at a time.
        MyDockingUI.delete_instances()
        self.__class__.instances.append(weakref.proxy(self))

        self.window_name = self.CONTROL_NAME
        self.ui = parent
        self.main_layout = parent.layout()
        self.main_layout.setContentsMargins(2, 2, 2, 2)

        self._model = model.SceneGraphModel(root_node)

        self._proxy_model = QtCore.QSortFilterProxyModel()
        self._proxy_model.setSourceModel(self._model)
        self._proxy_model.setDynamicSortFilter(True)
        self._proxy_model.setFilterCaseSensitivity(QtCore.Qt.CaseInsensitive)
        #self._proxy_model.setSortRole(model.SceneGraphModel.sortRole)
        #self._proxy_model.setFilterRole(model.SceneGraphModel.filterRole)


        self.treeView = QtWidgets.QTreeView()
        self.treeView.setModel(self._proxy_model)

        self.filter_line_edit = QtWidgets.QLineEdit(self)

        self.main_layout.addWidget(self.filter_line_edit)
        self.main_layout.addWidget(self.treeView)

        # self.treeView.setSortingEnabled(True)

        self.filter_line_edit.textChanged.connect(self._proxy_model.setFilterRegExp)
        self.treeView.selectionModel().selectionChanged.connect(self.tree_changed)

        sel = mc.ls(sl=True)

    def tree_changed(self):
        index = self.treeView.selectedIndexes()[0]
        name = self._proxy_model.data(index, QtCore.Qt.DisplayRole)
        if mc.objExists(name):
            mc.select(name)

    @staticmethod
    def delete_instances():
        for ins in MyDockingUI.instances:
            # logger.info('Delete {}'.format(ins))
            try:
                ins.setParent(None)
                ins.deleteLater()
            except:
                # ignore the fact that the actual parent has already been deleted by Maya...
                pass

            MyDockingUI.instances.remove(ins)
            del ins

    def run(self):
        return self


def go(root_node=None):
    dock_window(MyDockingUI, root_node=root_node)
