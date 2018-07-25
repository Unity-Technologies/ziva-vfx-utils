import weakref

import maya.cmds as mc
import maya.mel as mm
import maya.OpenMayaUI as omui
from shiboken2 import wrapInstance
from PySide2 import QtGui, QtWidgets, QtCore

import zBuilder.ui.model as model
import zBuilder.ui.icons as icons
import logging

logger = logging.getLogger(__name__)


def dock_window(dialog_class, root_node=None):
    try:
        mc.deleteUI(dialog_class.CONTROL_NAME)
        logger.info('removed workspace {}'.format(dialog_class.CONTROL_NAME))
    except:
        pass

    # building the workspace control with maya.cmds
    main_control = mc.workspaceControl(dialog_class.CONTROL_NAME, ttc=["AttributeEditor", -1], iw=300, mw=100,
                                       wp='preferred', label=dialog_class.DOCK_LABEL_NAME)

    # now lets get a C++ pointer to it using OpenMaya
    control_widget = omui.MQtUtil.findControl(dialog_class.CONTROL_NAME)
    # conver the C++ pointer to Qt object we can use
    control_wrap = wrapInstance(long(control_widget), QtWidgets.QWidget)

    # control_wrap is the widget of the docking window and now we can start working with it:
    control_wrap.setAttribute(QtCore.Qt.WA_DeleteOnClose)

    win = dialog_class(control_wrap, root_node=root_node)
    # after maya is ready we should restore the window since it may not be visible
    mc.evalDeferred(lambda *args: mc.workspaceControl(main_control, e=True, rs=True))

    win.run()


class MyDockingUI(QtWidgets.QWidget):
    instances = list()
    CONTROL_NAME = 'zivaVfxView'
    DOCK_LABEL_NAME = 'Ziva VFX'

    def __init__(self, parent=None, root_node=None):
        super(MyDockingUI, self).__init__(parent)

        self.__copy_buffer = None
        # let's keep track of our docks so we only have one at a time.
        MyDockingUI.delete_instances()
        self.__class__.instances.append(weakref.proxy(self))

        self.window_name = self.CONTROL_NAME
        self.ui = parent
        self.main_layout = parent.layout()
        self.main_layout.setContentsMargins(2, 2, 2, 2)

        self.treeView = QtWidgets.QTreeView()
        self.treeView.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.treeView.customContextMenuRequested.connect(self.open_menu)

        self._proxy_model = QtCore.QSortFilterProxyModel()

        self.reset_tree(root_node=root_node)
        # self.treeView.setSortingEnabled(True)

        # self.filter_line_edit = QtWidgets.QLineEdit(self)

        self.tool_bar = QtWidgets.QToolBar(self)
        self.tool_bar.setIconSize(QtCore.QSize(32, 32));
        # self.tool_bar.setContentsMargins(0,0,0,0)
        self.tool_bar.setObjectName("toolBar")

        # self.main_layout.addWidget(self.filter_line_edit)
        self.main_layout.addWidget(self.tool_bar)
        self.main_layout.addWidget(self.treeView)

        # self.filter_line_edit.textChanged.connect(self._proxy_model.setFilterRegExp)
        self.treeView.selectionModel().selectionChanged.connect(self.tree_changed)

        self._setup_actions()

        self.tool_bar.addAction(self.actionRefresh)

    def _setup_actions(self):

        refresh_path = icons.get_icon_path_from_name('refresh')
        refresh_icon = QtGui.QIcon()
        refresh_icon.addPixmap(QtGui.QPixmap(refresh_path),
                               QtGui.QIcon.Normal, QtGui.QIcon.Off)
        self.actionRefresh = QtWidgets.QAction(self)
        self.actionRefresh.setText('Refresh')
        self.actionRefresh.setIcon(refresh_icon)
        self.actionRefresh.setObjectName("actionUndo")
        self.actionRefresh.triggered.connect(self.reset_tree)

        self.actionCopy = QtWidgets.QAction(self)
        self.actionCopy.setText('Copy')
        self.actionCopy.setObjectName("actionCopy")
        self.actionCopy.triggered.connect(self.copy)

        self.actionPaste = QtWidgets.QAction(self)
        self.actionPaste.setText('Paste')
        self.actionPaste.setObjectName("actionPaste")
        self.actionPaste.triggered.connect(self.paste)

        self.actionPasteSansMaps = QtWidgets.QAction(self)
        self.actionPasteSansMaps.setText('Paste without maps')
        self.actionPasteSansMaps.setObjectName("actionPasteSansMaps")
        self.actionPasteSansMaps.triggered.connect(self.paste_sans_maps)
        
        self.actionRemoveSolver = QtWidgets.QAction(self)
        self.actionRemoveSolver.setText('Remove Solver')
        self.actionRemoveSolver.setObjectName("actionRemove")
        self.actionRemoveSolver.triggered.connect(self.reset_tree)

        self.actionPaintByProx = QtWidgets.QAction(self)
        self.actionPaintByProx.setText('Paint By Proximity')
        self.actionPaintByProx.setObjectName("actionPaint")
        self.actionPaintByProx.triggered.connect(paint_by_prox)

    def copy(self):
        indexes = self.treeView.selectedIndexes()[0]
        name = indexes.data(QtCore.Qt.DisplayRole)

        
        import zBuilder.builders.ziva as zva
        z = zva.Ziva()
        z.retrieve_from_scene_selection(name,connections=False)
        #z.string_replace(selection[0].split('|')[-1], selection[1].split('|')[-1])
        z.stats()
        # z.build(**kwargs)
        self.__copy_buffer = {}
        self.__copy_buffer[name] = z
        # mc.select(sel)

    def paste(self):
        indexes = self.treeView.selectedIndexes()[0]
        name = indexes.data(QtCore.Qt.DisplayRole)

        if self.__copy_buffer:
            old_name = self.__copy_buffer.keys()[0]
            z = self.__copy_buffer[old_name]
            for parameter in z.get_scene_items(type_filter='zAttachment'):
                parameter.mobject_reset()
            z.string_replace(old_name, name)
            z.build()

    def paste_sans_maps(self):
        indexes = self.treeView.selectedIndexes()[0]
        name = indexes.data(QtCore.Qt.DisplayRole)

        if self.__copy_buffer:
            old_name = self.__copy_buffer.keys()[0]
            z = self.__copy_buffer[old_name]
            for parameter in z.get_scene_items(type_filter='zAttachment'):
                parameter.mobject_reset()
            z.string_replace(old_name, name)
            z.build()

    def open_menu(self,position):
        indexes = self.treeView.selectedIndexes()[0]
        node = indexes.data(QtCore.Qt.UserRole+2)
        
        menu = QtWidgets.QMenu()
        menu.addAction(self.actionCopy)
        menu.addAction(self.actionPaste)
        menu.addAction(self.actionPasteSansMaps)
        if node.type == 'zSolver' or node.type == 'zSolverTransform':
            menu.addSection(node.type)
            menu.addAction(self.actionRemoveSolver)

        if node.type == 'zAttachment':
            menu.addSection(node.type)
            menu.addAction(self.actionPaintByProx)
        
        menu.exec_(self.treeView.viewport().mapToGlobal(position))

    def tree_changed(self):
        index = self.treeView.selectedIndexes()[0]
        name = self._proxy_model.data(index, QtCore.Qt.DisplayRole)
        if mc.objExists(name):
            mc.select(name)

    def reset_tree(self, root_node=None):
        """This builds and/or resets the tree given a root_node.  The root_node
        is a zBuilder object that the tree is built from.  If None is passed 
        it uses the scene selection to build a new root_node.

        This forces a complete redraw of the ui tree.
        
            root_node (:obj:`obj`, optional): The zBuilder root_node to build 
                tree from.  Defaults to None.
        """

        if not root_node:
            import zBuilder.builders.ziva as zva
            z = zva.Ziva()
            z.retrieve_connections()
            root_node = z.root_node

        self._model = model.SceneGraphModel(root_node)

        self._proxy_model.setSourceModel(self._model)
        self._proxy_model.setDynamicSortFilter(True)
        self._proxy_model.setFilterCaseSensitivity(QtCore.Qt.CaseInsensitive)
        # self._proxy_model.setSortRole(model.SceneGraphModel.sortRole)
        # self._proxy_model.setFilterRole(model.SceneGraphModel.filterRole)

        self.treeView.setModel(self._proxy_model)

        # Expand all zSolverTransform tree items--------------------------------
        proxy_model = self.treeView.model()
        for row in range(proxy_model.rowCount()):
            index = proxy_model.index(row, 0)
            node = index.data(QtCore.Qt.UserRole+2)
            if node.type == 'zSolverTransform':
                self.treeView.expand(index)

        sel = mc.ls(sl=True)
        # select item in treeview that is selected in maya to begin with and 
        # expand item in view.
        if sel:
            checked = proxy_model.match(proxy_model.index(0, 0), QtCore.Qt.DisplayRole, sel[0],
                                -1, QtCore.Qt.MatchExactly | QtCore.Qt.MatchRecursive)
            for index in checked:
                self.treeView.selectionModel().select(index,
                                                      QtCore.QItemSelectionModel.SelectCurrent)

            # this works for a zBuilder view.  This is expanding the item selected
            # and it's parent if any.  This makes it possible if you have a 
            # material or attachment selected, it will become visable in UI
            self.treeView.expand(checked[-1])
            self.treeView.expand(checked[-1].parent())


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


def paint_by_prox():
    mm.eval('ZivaPaintAttachmentsByProximityOptions;')

def go(root_node=None):
    dock_window(MyDockingUI, root_node=root_node)
