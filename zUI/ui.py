import weakref
from functools import partial

import maya.cmds as mc
import maya.mel as mm
try:
    from shiboken2 import wrapInstance
except ImportError:
    raise StandardError("Ziva Scene Panel supported on Maya 2017+")

from PySide2 import QtGui, QtWidgets, QtCore
from zBuilder.ui.utils import dock_window

import zBuilder.ui.model as model
import zBuilder.ui.icons as icons
import zBuilder.builders.ziva as zva



class ZivaUi():

    # Show window with docking ability
    def run(self):
        z = zva.Ziva()
        z.retrieve_connections()

        dock_window(MyDockingUI, root_node=z.root_node)


class MyDockingUI(QtWidgets.QWidget):
    instances = list()
    CONTROL_NAME = 'zivaScenePanel'
    DOCK_LABEL_NAME = 'Ziva Scene Panel'

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
        self.root_node = root_node
        self.reset_tree(root_node=self.root_node)

        self.tool_bar = QtWidgets.QToolBar(self)
        self.tool_bar.setIconSize(QtCore.QSize(32, 32));
        self.tool_bar.setObjectName("toolBar")

        self.main_layout.addWidget(self.tool_bar)
        self.main_layout.addWidget(self.treeView)

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


        self.actionPaste = QtWidgets.QAction(self)
        self.actionPaste.setText('Paste')
        self.actionPaste.setObjectName("actionPaste")


        self.actionPasteSansMaps = QtWidgets.QAction(self)
        self.actionPasteSansMaps.setText('Paste without maps')
        self.actionPasteSansMaps.setObjectName("actionPasteSansMaps")

        
        self.actionRemoveSolver = QtWidgets.QAction(self)
        self.actionRemoveSolver.setText('Remove Solver')
        self.actionRemoveSolver.setObjectName("actionRemove")
        self.actionRemoveSolver.triggered.connect(self.reset_tree)

        self.actionSelectST = QtWidgets.QAction(self)
        self.actionSelectST.setText('Select Source and Target')
        self.actionSelectST.setObjectName("actionSelectST")
        self.actionSelectST.triggered.connect(self.select_source_and_target)

        self.actionSelectFiberCurve = QtWidgets.QAction(self)
        self.actionSelectFiberCurve.setText('Select Curve')
        self.actionSelectFiberCurve.setObjectName("selectCurve")
        self.actionSelectFiberCurve.triggered.connect(self.select_source_and_target)

        self.actionPaintByProx = QtWidgets.QAction(self)
        self.actionPaintByProx.setText('Paint By Proximity UI')
        self.actionPaintByProx.setObjectName("actionPaint")
        self.actionPaintByProx.triggered.connect(paint_by_prox)

        self.actionPaintByProx_1_2 = QtWidgets.QAction(self)
        self.actionPaintByProx_1_2.setText('Paint By Proximity .1 - .2')
        self.actionPaintByProx_1_2.setObjectName("actionPaint12")
        self.actionPaintByProx_1_2.triggered.connect(paint_by_prox_1_2)

        self.actionPaintByProx_1_10 = QtWidgets.QAction(self)
        self.actionPaintByProx_1_10.setText('Paint By Proximity .1 - 1.0')
        self.actionPaintByProx_1_10.setObjectName("actionPaint110")
        self.actionPaintByProx_1_10.triggered.connect(paint_by_prox_1_10)

        self.actionPaintSource = QtWidgets.QAction(self)
        self.actionPaintSource.setText('Paint - source weights')
        self.actionPaintSource.setObjectName("paintSource")
        self.actionPaintSource.triggered.connect(partial(self.paint_weights,0,'weights'))

        self.actionPaintTarget = QtWidgets.QAction(self)
        self.actionPaintTarget.setText('Paint - target weights')
        self.actionPaintTarget.setObjectName("paintTarget")
        self.actionPaintTarget.triggered.connect(partial(self.paint_weights,1,'weights'))


        self.actionPaintWeight = QtWidgets.QAction(self)
        self.actionPaintWeight.setText('Paint - weights')
        self.actionPaintWeight.setObjectName("paintWeight")
        self.actionPaintWeight.triggered.connect(partial(self.paint_weights,0,'weights'))

        self.actionPaintEndPoints = QtWidgets.QAction(self)
        self.actionPaintEndPoints.setText('Paint - endPoints')
        self.actionPaintEndPoints.setObjectName("paintEndPoints")
        self.actionPaintEndPoints.triggered.connect(partial(self.paint_weights,0,'endPoints'))


    def paint_weights(self,association_idx,attribute):
        """Paint weights menu command.
        
        This is checking item selected in treeView to get zBuilder node.
        
        Args:
            association_idx (int): The index of mesh to use in node association.
            attribute (string): The name of the attribute to paint.
        """

        indexes = self.treeView.selectedIndexes()[0]
        node = indexes.data(QtCore.Qt.UserRole+2)
        mesh = node.association[association_idx]
        mc.select(mesh,r=True)
        cmd = 'artSetToolAndSelectAttr( "artAttrCtx", "{}.{}.{}" );'.format(node.type,node.name,attribute)
        mm.eval(cmd)

    def select_source_and_target(self):
        """Selects the source and target mesh of an attachment.  This is a menu 
        command.
        """

        indexes = self.treeView.selectedIndexes()[0]
        node = indexes.data(QtCore.Qt.UserRole+2)
        mc.select(node.association)

    def select_fiber_curve(self):
        """Selects fiber curve based on item selected in tree.  This is a menu 
        command.
        """

        indexes = self.treeView.selectedIndexes()[0]
        node = indexes.data(QtCore.Qt.UserRole+2)
        mc.select(node.curve)

    def open_menu(self,position):
        """Generates menu for tree items

        We are getting the zBuilder node in the tree item and checking type.
        With that we can build a custom menu per type.
        """

        indexes = self.treeView.selectedIndexes()[0]
        node = indexes.data(QtCore.Qt.UserRole+2)
        
        menu = QtWidgets.QMenu()

        if node.type == 'zTet':
            menu.addAction(self.actionPaintWeight)
            menu.addSection('')

        if node.type == 'zFiber':
            menu.addAction(self.actionPaintWeight)
            menu.addAction(self.actionPaintEndPoints)
            menu.addSection('')

        if node.type == 'zMaterial':
            menu.addAction(self.actionPaintWeight)
            menu.addSection('')

        if node.type == 'zEmbedder':
            menu.addAction(self.actionPaintWeight)
            menu.addSection('')

        if node.type == 'zAttachment':
            menu.addAction(self.actionPaintSource)
            menu.addAction(self.actionPaintTarget)
            menu.addSection('')
            menu.addAction(self.actionPaintByProx)
            menu.addAction(self.actionPaintByProx_1_2)
            menu.addAction(self.actionPaintByProx_1_10)
            menu.addAction(self.actionSelectST)

        if node.type == 'zLineOfAction':
            menu.addSection(node.type)
            menu.addAction(self.actionSelectFiberCurve)

        menu.exec_(self.treeView.viewport().mapToGlobal(position))


    def tree_changed(self):
        """When the tree selection changes this gets executed to select
        corrisponding item in Maya scene.
        """
        index = self.treeView.selectedIndexes()[0]
        node = index.data(QtCore.Qt.UserRole+2)
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
    
def paint_by_prox_1_2():
    mm.eval('zPaintAttachmentsByProximity -min .1 -max .2')

def paint_by_prox_1_10():
    mm.eval('zPaintAttachmentsByProximity -min .1 -max 1.0')


