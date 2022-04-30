import weakref

from maya import cmds
from PySide2 import QtWidgets, QtCore
from ..uiUtils import dock_window
from . import model


class MyDockingUI(QtWidgets.QWidget):
    instances = list()
    CONTROL_NAME = 'zBuilderView'
    DOCK_LABEL_NAME = 'zBuilder View'

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

        self._proxy_model = QtCore.QSortFilterProxyModel()
        self.root_node = root_node
        self.set_root_node(root_node=self.root_node)

        self.main_layout.addWidget(self.treeView)

    def set_root_node(self, root_node=None):
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
            node = index.data(QtCore.Qt.UserRole + 2)
            if node.type == 'zSolverTransform':
                self.treeView.expand(index)

        sel = cmds.ls(sl=True)
        # select item in treeview that is selected in maya to begin with and
        # expand item in view.
        if sel:
            checked = proxy_model.match(proxy_model.index(0, 0), QtCore.Qt.DisplayRole, sel[0], -1,
                                        QtCore.Qt.MatchExactly | QtCore.Qt.MatchRecursive)
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


def view(root_node=None):
    dock_window(MyDockingUI, root_node=root_node)
