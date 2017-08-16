from shiboken import wrapInstance
from PySide import QtGui, QtCore
from maya import OpenMayaUI as omui
from maya.app.general.mayaMixin import MayaQWidgetDockableMixin
from maya.OpenMayaUI import MQtUtil
import functools
import os
import maya.cmds as mc
import maya.mel as mm
from maya import OpenMaya as om
import zBuilder.setup.Ziva as zva
import zUI.util as util

import zBuilder.zMaya as mz
import widgets.Properties as prop
import widgets.ButtonLineEdit as line
import zConstants as con

import zBuilder.nodes.base as bse

import logging

logger = logging.getLogger(__name__)


'''
to run in maya:

import zUI.ui as ui
myWin = ui.ZivaUi()
myWin.run()

'''

'''
TODO - allow editing multiple table cells at once
TODO - filter attribute names in table
TODO - copy and paste

'''

icons = {}
icons['zBone'] =            'icons\\zBone.png'
icons['close'] =            'icons\\Fileclose.png'
icons['zTissue'] =          'icons\\zTissue.png'
icons['zTet'] =             'icons\\zTet.png'
icons['zAttachment'] =      'icons\\zAttachment.png'
icons['zAttachment_s'] =      'icons\\zAttachment.png'
icons['zAttachment_t'] =      'icons\\zAttachment.png'
icons['zSolver']=           'icons\\out_zSolver.png'
icons['zSolverTransform']=  'icons\\out_zSolver.png'
icons['zMaterial']=         'icons\\zMaterial.png'
icons['zFiber']=            'icons\\zFiber.png'
icons['zEmbedder']=            'icons\\out_zSolver.png'
icons['zCache']=            'icons\\zFiber.png'
icons['zCacheTransform']=            'icons\\zFiber.png'
icons['zCloth']=            'icons\\zFiber.png'

#Ken Added
icons['zImport']=         'icons\\zivaImport.png'
icons['zExport']=            'icons\\zivaExport.png'

# todo share resource for zNodeCapture
maplist = {}
maplist['zTet'] = ['weightList[0].weights']
maplist['zMaterial'] = ['weightList[0].weights']
maplist['zFiber'] = ['weightList[0].weights','endPoints']
maplist['zAttachment'] = ['weightList[0].weights','weightList[1].weights']

niceMaplist = {}
niceMaplist['zTet'] = ['weights']
niceMaplist['zMaterial'] = ['weights']
niceMaplist['zFiber'] = ['weights','endPoints']
niceMaplist['zAttachment'] = ['source','target']


ss_line = os.path.normcase(os.path.join((os.path.split(__file__)[0]+"/icons/line.png"))).replace('\\','/')
ss_cross = os.path.normcase(os.path.join((os.path.split(__file__)[0]+"/icons/cross.png"))).replace('\\','/')
ss_end = os.path.normcase(os.path.join((os.path.split(__file__)[0]+"/icons/stylesheet-branch-end.png"))).replace('\\','/')
ss_more = os.path.normcase(os.path.join((os.path.split(__file__)[0]+"/icons/stylesheet-branch-more.png"))).replace('\\','/')
ss_vline = os.path.normcase(os.path.join((os.path.split(__file__)[0]+"/icons/stylesheet-vline.png"))).replace('\\','/')


tree_style ='''
QTreeView::branch:has-siblings:!adjoins-item {
    border-image: url("'''+ss_vline+'''") 0;
}

QTreeView::branch:has-siblings:adjoins-item {
    border-image: url("'''+ss_more+'''") 0;
}

QTreeView::branch:!has-children:!has-siblings:adjoins-item {
    border-image: url("'''+ss_end+'''") 0;
}

QTreeView::branch:has-children:!has-siblings:closed,
QTreeView::branch:closed:has-children:has-siblings {
        border-image: none;
        image: url("'''+ss_cross+'''");
}

QTreeView::branch:open:has-children:!has-siblings,
QTreeView::branch:open:has-children:has-siblings  {
        border-image: none;
        image: url("'''+ss_line+'''");
}
'''
class MCallbackIdWrapper(object):
    '''Wrapper class to handle cleaning up of MCallbackIds from registered MMessage
    '''
    def __init__(self, callbackId):
        super(MCallbackIdWrapper, self).__init__()
        self.callbackId = callbackId
        #print 'creating ',self.callbackId

    def __del__(self):
        om.MMessage.removeCallback(self.callbackId)
        #print 'deleting ',self.callbackId

    def __repr__(self):
        return 'MCallbackIdWrapper(%r)'%self.callbackId


class ZivaUi( MayaQWidgetDockableMixin,QtGui.QMainWindow):
    toolName = 'zivaWidget'

    def __init__(self, parent=None):
        super(ZivaUi, self).__init__(parent)
        mayaMainWindowPtr = omui.MQtUtil.mainWindow() 

        self.nodeCallbacks = {}            # Node callbacks for handling attr value changes
        self.attrWidgets = {}              # Dict key=attrName, value=widget
        self._deferredUpdateRequest = {}   # Dict of widgets to update

        self._convert_icon_path()
        #self.deleteInstances()

        self.settings = QtCore.QSettings("Ziva Dynamics", "zUi")


        self.mayaMainWindow = wrapInstance(long(mayaMainWindowPtr), QtGui.QMainWindow)
        self.setObjectName(self.__class__.toolName) # Make this unique enough if using it to clear previous instance!

        # Setup window's properties
        self.setWindowFlags(QtCore.Qt.Window)
        self.setWindowTitle('Ziva VFX')
        self.setWindowIcon(QtGui.QIcon(icons['close']))      

        # Delete UI on close to avoid winEvent error
        #self.setAttribute(QtCore.Qt.WA_DeleteOnClose)
        
        self.progressBar = QtGui.QProgressBar()
        self.progressBar.setRange(0, 100)
        self.progressBar.setValue(0)
        self.progressBar.hide()

        self.setup_actions()

        self.create_layout()
        self.setup_toolbars()
        self.statusBar().addPermanentWidget(self.progressBar)
        
        self.create_popup_menu()
        self._populate()
        
        self.script_job()
        mc.select(cl=True)
        #mc.select(sel,r=True)

        # restore settings------------------------------------------------------
        self.resize(self.settings.value('mw:size', QtCore.QSize(550, 470)))
        self.move(self.settings.value('mw:pos', QtCore.QPoint(250, 250)))
        self.restoreState(self.settings.value( "mw:state", self.saveState()))

    def save_settings(self):
        self.settings.setValue('mw:size', self.size())
        self.settings.setValue('mw:pos', self.mapToGlobal(self.pos()))
        self.settings.setValue('mw:state', self.saveState())
        self.settings.setValue('splitter:state', self.splitter1.saveState())


    def _convert_icon_path(self):
        path = os.path.dirname(os.path.realpath(__file__))
        for zNode in icons:
            icons[zNode] = os.path.join(path,icons[zNode])
        #print icons
        
    def create_layout(self):



        self.line_edit = line.ButtonLineEdit(icons['close'])


        self.treeWidget = QtGui.QTreeWidget()
        self.treeWidget.setColumnCount(1)
        self.treeWidget.setSelectionMode(QtGui.QAbstractItemView.ExtendedSelection)
        self.treeWidget.header().close()
        self.treeWidget.setAutoFillBackground(True)

        self.treeWidget.setStyleSheet(tree_style)
        #self.treeWidget.setStyleSheet("QTreeView::branch { border-image: none; }")
        #self.treeWidget.setStyleSheet("background-color:black;")
        #self.treeWidget.setStyleSheet("QTreeView::item:has-children{background: palette(base);}")
        #self.treeWidget.setStyleSheet("QTreeView::item:has-children{background: palette(base);}")
        #self.treeWidget.setStyleSheet("QTreeView::item:hover {background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1, stop: 0 #e7effd, stop: 1 #cbdaf1);border: 1px solid #bfcde4;}")


        #self.treeWidget.setStyleSheet("QTreeView::branch:open:has-children:!has-siblings,QTreeView::branch:open:has-children:has-siblings  {border-image: none;image: url(branch-open.png);}")
        #=self.treeWidget.setStyleSheet("QTreeWidget::item:has-children:selected {background: cyan;}")

        self.treeWidget.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)

        main_layout = QtGui.QVBoxLayout()
        main_layout.setContentsMargins(2, 2, 2, 2)
        main_layout.setSpacing(2)
        
        # tool------------------------------------------------------------------\
        h_layout = QtGui.QHBoxLayout()
        h_layout.setStretch(0,True)


        self.prop = prop.Properties(self)
        #-----------------------------------------------------------------------
        #main_layout.addWidget(self.line_edit)
        #main_layout.addLayout(tool_layout)
        main_layout.addLayout(h_layout)
        

        self.cw = QtGui.QWidget()
        self.setCentralWidget(self.cw)
        self.cw.setLayout(main_layout)


        self.splitter1 = QtGui.QSplitter(self.cw)
        self.splitter1.addWidget(self.treeWidget)
        self.splitter1.addWidget(self.prop)
        h_layout.addWidget(self.splitter1)

        self.splitter1.restoreState(self.settings.value('splitter:state',self.splitter1.saveState()))
        # connect treewidget
        self.treeWidget.itemSelectionChanged.connect(self.tree_changed)

        
        #self.treeWidget.itemSelectionChanged.connect(self.update_properties)
        self.line_edit.textChanged.connect(self.search_tree)

        



        self.setup_menuBar()

    def setup_menuBar(self):
        menubar = self.menuBar()

        fileMenu = menubar.addMenu('&File')
        fileMenu.setTearOffEnabled(True)
        fileMenu.addAction(self.ziva_import_ac)
        fileMenu.addAction(self.ziva_save_ac)



        editMenu = menubar.addMenu('&Edit')
        editMenu.setTearOffEnabled(True)
        editMenu.addAction(self.delete_ac)
        editMenu.addAction(self.enable_toggle_ac)


        createMenu = menubar.addMenu('&Create')
        createMenu.setTearOffEnabled(True)
        createMenu.addSeparator().setText(("One"))
        createMenu.addAction(self.c_solver_ac)
        createMenu.addAction(self.c_tissue_ac)
        createMenu.addAction(self.c_bone_ac)
        createMenu.addAction(self.c_att_ac)
        createMenu.addSeparator().setText(("Testing"))
        createMenu.addAction(self.c_material_ac)
        createMenu.addAction(self.c_fiber_ac)

        viewMenu = menubar.addMenu('&View')
        viewMenu.setTearOffEnabled(True)
        viewMenu.addAction(self.refresh_ac)
        viewMenu.addAction(self.find_ac)


    def setup_actions(self):

        self.ziva_save_ac = QtGui.QAction(QtGui.QIcon(icons['zExport']), 'Export Ziva Setup...', self)
        #self.ziva_save_ac.setShortcut('s')
        self.ziva_save_ac.setStatusTip('Export Ziva Setup')
        self.ziva_save_ac.triggered.connect(self._save_solver)

        self.ziva_import_ac = QtGui.QAction(QtGui.QIcon(icons['zImport']), 'Import Ziva Setup...', self)
        #self.ziva_save_ac.setShortcut('s')
        self.ziva_import_ac.setStatusTip('Import Ziva Setup')
        self.ziva_import_ac.triggered.connect(self._import_solver)


        self.c_solver_ac = QtGui.QAction(QtGui.QIcon(icons['zSolver']), 'Solver', self)
        self.c_solver_ac.setShortcut('s')
        self.c_solver_ac.setStatusTip('Create Solver')
        self.c_solver_ac.triggered.connect(self._create_solver)

        self.c_tissue_ac = QtGui.QAction(QtGui.QIcon(icons['zTissue']), 'Tissue', self)
        self.c_tissue_ac.setShortcut('t')
        self.c_tissue_ac.setStatusTip('Create Tissue')
        self.c_tissue_ac.triggered.connect(self._create_tissue)

        self.c_bone_ac = QtGui.QAction(QtGui.QIcon(icons['zBone']), 'Bone', self)
        self.c_bone_ac.setShortcut('b')
        self.c_bone_ac.setStatusTip('Create Bone')
        self.c_bone_ac.triggered.connect(self._create_bone)

        self.c_material_ac = QtGui.QAction(QtGui.QIcon(icons['zMaterial']), 'Material', self)
        self.c_material_ac.setShortcut('m')
        self.c_material_ac.setStatusTip('Create material')
        self.c_material_ac.triggered.connect(self._create_material)

        self.c_fiber_ac = QtGui.QAction(QtGui.QIcon(icons['zFiber']), 'Fiber', self)
        #self.c_fiber_ac.setShortcut('F5')
        self.c_fiber_ac.setStatusTip('Create Fiber')
        self.c_fiber_ac.triggered.connect(self._create_fiber)

        self.c_att_ac = QtGui.QAction(QtGui.QIcon(icons['zFiber']), 'Attachment', self)
        self.c_att_ac.setShortcut('a')
        self.c_att_ac.setStatusTip('Create Attachment')
        self.c_att_ac.triggered.connect(self._create_attachment)



        self.delete_ac = QtGui.QAction( 'Remove Ziva Node', self)
        shortcuts = [
            QtGui.QKeySequence(QtCore.Qt.Key_Delete),
            QtGui.QKeySequence(QtCore.Qt.Key_Backspace)
                    ]
        self.delete_ac.setShortcuts(shortcuts)
        self.delete_ac.setStatusTip('Remove Ziva Node')
        self.delete_ac.triggered.connect(self._delete_nodes)


        self.refresh_ac = QtGui.QAction(QtGui.QIcon(icons['zSolver']), 'Refresh', self)
        self.refresh_ac.setShortcut('F5')
        self.refresh_ac.setStatusTip('Refresh Ui')
        self.refresh_ac.triggered.connect(self._refresh_ui)

        self.solvers_ac = QtGui.QAction(QtGui.QIcon(icons['zSolver']), 'Solvers', self)

        self.solvers_ac.setShortcut('1')
        #self.solvers_ac.setShortcutContext(QtCore.Qt.WidgetWithChildrenShortcut)
        self.solvers_ac.setStatusTip('Toggle Solver Visibility')
        self.solvers_ac.setCheckable(True)
        self.solvers_ac.setChecked(False)
        self.solvers_ac.triggered.connect(self.tool_button_clicked)

        self.tissue_ac = QtGui.QAction(QtGui.QIcon(icons['zTissue']), 'Tissues', self)
        self.tissue_ac.setShortcut('2')
        self.tissue_ac.setStatusTip('Toggle Tissue Visibility')
        self.tissue_ac.setCheckable(True)
        self.tissue_ac.setChecked(False)
        self.tissue_ac.triggered.connect(self.tool_button_clicked)

        self.tet_ac = QtGui.QAction(QtGui.QIcon(icons['zTet']), 'Tets', self)
        self.tet_ac.setShortcut('3')
        self.tet_ac.setStatusTip('Toggle Tet Visibility')
        self.tet_ac.setCheckable(True)
        self.tet_ac.setChecked(False)
        self.tet_ac.triggered.connect(self.tool_button_clicked)

        self.bone_ac = QtGui.QAction(QtGui.QIcon(icons['zBone']), 'Bones', self)
        self.bone_ac.setShortcut('4')
        self.bone_ac.setStatusTip('Toggle Bone Visibility')
        self.bone_ac.setCheckable(True)
        self.bone_ac.setChecked(False)
        self.bone_ac.triggered.connect(self.tool_button_clicked)

        self.attachment_ac = QtGui.QAction(QtGui.QIcon(icons['zAttachment']), 'Attachment', self)
        self.attachment_ac.setShortcut('5')
        self.attachment_ac.setStatusTip('Toggle Attachment Visibility')
        self.attachment_ac.setCheckable(True)
        self.attachment_ac.setChecked(False)
        self.attachment_ac.triggered.connect(self.tool_button_clicked)

        self.material_ac = QtGui.QAction(QtGui.QIcon(icons['zMaterial']), 'Material', self)
        self.material_ac.setShortcut('6')
        self.material_ac.setStatusTip('Toggle Material Visibility')
        self.material_ac.setCheckable(True)
        self.material_ac.setChecked(False)
        self.material_ac.triggered.connect(self.tool_button_clicked)

        self.fiber_ac = QtGui.QAction(QtGui.QIcon(icons['zFiber']), 'Fiber', self)
        self.fiber_ac.setShortcut('7')
        self.fiber_ac.setStatusTip('Toggle Fiber Visibility')
        self.fiber_ac.setCheckable(True)
        self.fiber_ac.setChecked(False)
        self.fiber_ac.triggered.connect(self.tool_button_clicked)
		
		#not sure what self.paint_ac does KC
        self.paint_ac = QtGui.QAction(QtGui.QIcon(icons['zFiber']), 'Fiber', self)

        self.find_ac = QtGui.QAction(QtGui.QIcon(), 'Find', self)
        self.find_ac.setShortcut('f')
        self.find_ac.setStatusTip('find')
        self.find_ac.triggered.connect(self._find_items)

        self.enable_toggle_ac = QtGui.QAction(QtGui.QIcon(), 'Enable Toggle', self)
        self.enable_toggle_ac.setShortcut('e')
        self.enable_toggle_ac.setStatusTip('Toggle enable status of selected items')
        self.enable_toggle_ac.triggered.connect(self._enable_items)


    def setup_toolbars(self):
        # vis toolbar-----------------------------------------------------------
        self.toolbar = self.addToolBar('Vis')
        self.toolbar.setIconSize(QtCore.QSize(16, 16))
        self.toolbar.addAction(self.solvers_ac)
        self.toolbar.addAction(self.tissue_ac)
        self.toolbar.addAction(self.tet_ac)
        self.toolbar.addAction(self.bone_ac)
        self.toolbar.addAction(self.attachment_ac)
        self.toolbar.addAction(self.material_ac)
        self.toolbar.addAction(self.fiber_ac)

        self.toolbar.addSeparator()
        
        #self.addToolBarBreak()
        # # tools-----------------------------------------------------------------
        # self.tool_toolbar = self.addToolBar('Tools')
        # self.tool_toolbar.setIconSize(QtCore.QSize(16, 16))
        # self.tool_toolbar.addAction(self.material_ac)
        # self.tool_toolbar.addAction(self.fiber_ac)
       


        # serach toolbar--------------------------------------------------------
        self.search_toolbar = self.addToolBar('Search')

        self.search_toolbar.addWidget(self.line_edit)


    def _enable_items(self):
        can_enable = ['zSolverTransform','zTissue','zBone']
        can_env = ['zFiber','zAttachment','zMaterial']

        items = []
        getSelected = self.treeWidget.selectedItems()
        for selected in getSelected:
            tissue = self._get_child_item_of_type(selected,'zTissue')

            if tissue:
                items.append(tissue[0])
            bone = self._get_child_item_of_type(selected,'zBone')
            if bone:
                items.append(bone[0])

            #if not selected in items:
            items.append(selected)


        tmp={}
        for selected in items:
            name = self._get_name_from_item_data(selected,fullPath=False)
            _type = mc.objectType(name)
            if _type in can_enable:
                try:
                    val = mc.getAttr(name+'.enable')
                    if val:
                        mc.setAttr(name+'.enable',0)
                    else:
                        mc.setAttr(name+'.enable',1)
                except:
                    pass
            if _type in can_env:
                if not name in tmp:
                    tmp[name] = mc.getAttr(name+'.envelope')
                try:
                    if tmp[name]:
                        mc.setAttr(name+'.envelope',0)
                        #print 'sett:',name,0
                    else:
                        mc.setAttr(name+'.envelope',1)
                        #print 'sett:',name,1
                except:
                    pass

        self._foreground_item_enable_color()

    def _save_solver(self):
        #getSelected = self.treeWidget.selectedItems()
        #name = self._get_name_from_item_data(selected,fullPath=True)
        solver = mm.eval('zQuery -t zSolverTransform')[0]

        if solver:
            self.progressBar.setValue(0)
            self.progressBar.setFormat('saving...')
            self.progressBar.show()
            

            fileName = QtGui.QFileDialog.getSaveFileName(self, 'Save Ziva Setup', 'c:\\Temp\\', filter='*.ziva')
            if fileName[0]:

                z = zva.ZivaSetup()
                z.retrieve_from_scene(solver)
                self.progressBar.setValue(50)
                z.write(fileName[0])
                self.progressBar.setValue(100)
                self.progressBar.setFormat('finished saving')
        else:
            print 'no solver found in scene'

    def _import_solver(self):

        fileName = QtGui.QFileDialog.getOpenFileName(self, 'Import Ziva Setup', 'c:\\Temp\\', filter='*.ziva')
        if fileName[0]:
            self.progressBar.setValue(0)
            self.progressBar.setFormat('loading...')
            self.progressBar.show()
            
            sel = mc.ls(sl=True)

            z = zva.ZivaSetup()
            z.retrieve_from_file(fileName[0])

            z.apply_solver()
            #turn off solver to speed up build
            zSolverTransform = z.get_nodes(_type='zSolverTransform')[0]
            sn = zSolverTransform.get_name()
            solver_value = zSolverTransform.get_attr_value('enable')
            mc.setAttr(sn+'.enable',0)
            self.progressBar.setValue(20)
            z.apply_bones()
            self.progressBar.setValue(40)
            z.apply_tissues(interp_maps='auto')
            self.progressBar.setValue(60)
            z.apply_attachments(interp_maps='auto')
            self.progressBar.setValue(80)
            z.apply_materials(interp_maps='auto')
            self.progressBar.setValue(90)
            z.apply_fibers(interp_maps='auto')
            self.progressBar.setValue(100)
            z.apply_embedded()
            self.progressBar.setFormat('finished importing')
            # set solver back to whatever it was in data
            mc.setAttr(sn+'.enable',solver_value)
            mc.select(sel,r=True)

            self._refresh_ui()



    def _get_child_item_of_type(self,item,_type):
        childs = []
        for i in range(0,item.childCount()):

            name = self._get_name_from_item_data(item.child(i),fullPath=False)
            _t = mc.objectType(name)
            if _t == _type:
                childs.append(item.child(i))
        return childs

    def _create_solver(self):
        mm.eval('ziva -s')

    def _create_tissue(self):
        mm.eval('ziva -t')

    def _create_attachment(self):
        mm.eval('ziva -a')

    def _create_bone(self):
        mm.eval('ziva -b')

    def _create_material(self):
        mm.eval('ziva -m')

    def _create_fiber(self):
        mm.eval('ziva -f')

    def update_properties(self):
        #print 'ui:update_properties'
        self.prop.blockSignals(True)
        tmp = []
        items = self.treeWidget.selectedItems()
        for item in items:
            #if item.type():
            tmp.append(item)
            if not item.isHidden():
                if item.childCount() > 0:
                    tmp.extend(self._get_child_properties(item))


        # remove duplicates before we load UI
        # attachments can be in Ui twice, thus removing dup from prop window
        comp = []
        tmp2 = []
        for t in tmp:
            if t.text(0) not in comp:
                comp.append(t.text(0))
                tmp2.append(t)

        #print tmp2
        self.prop.update_properties(tmp2)
        self.prop.blockSignals(False)


    def _get_child_properties(self,item):
        tmp = []
        for i in range(0,item.childCount()):
            child = item.child(i)
            if not child.isHidden():
                if not child.isSelected():
                    tmp.append(child)
        return tmp

    def create_popup_menu(self):
		'''
		the pop-up menu for the tree widget
		'''
		
		self.popup_menu = QtGui.QMenu()
		# menu item
		self.item_add_act = QtGui.QAction("Open in Attribute Spread Sheet", self)
		
		self.item_add_paintBoth = QtGui.QAction("Both maps", self)
		self.item_add_act.triggered.connect(self.open_spreadsheet)
		self.item_add_act.setShortcut("s")
				
		#paint sel object Menu
		self.item_add_paintBoth.triggered.connect(self.createPopupLables)
		
		self.popup_menu.addAction(self.item_add_act)
		self.popup_menu.addSeparator().setText(("Paintable Objects"))
		self.popup_menu.addAction(self.item_add_paintBoth)
		
		
		self.treeWidget.customContextMenuRequested.connect(self._ctx_menu_cb)
    
    def createPopupLables(self):
		treeSelection =  self.treeWidget.selectedItems()[0]
		treeSelectionNiceName = treeSelection.text(0)
		treeSelected = treeSelectionNiceName
		treeSelectedType = mc.objectType(treeSelected)
		extractMeshData = mz.get_association(treeSelected)
		if len(extractMeshData) == 2:
			mc.select(extractMeshData)
			mm.eval( 'artSetToolAndSelectAttr( "artAttrCtx", "' + treeSelectedType + "." + treeSelected + '.weights")')
		

    def open_spreadsheet(self):
        '''
        opens a spreadsheet view
        '''
        window = mc.window( widthHeight=(1000, 300) )
        mc.paneLayout()
        activeList = mc.selectionConnection( activeList=True )
        mc.spreadSheetEditor( ko=False,mainListConnection=activeList )
        mc.showWindow( window )

    def _ctx_menu_cb(self, pos):
        point = self.mapToGlobal(pos)
        self.popup_menu.exec_(point)


    def tool_button_clicked(self):
        attachments = self.attachment_ac.isChecked()
        solver = self.solvers_ac.isChecked()
        muscles = self.tissue_ac.isChecked()
        tets = self.tet_ac.isChecked()
        bones = self.bone_ac.isChecked()
        fiber = self.fiber_ac.isChecked()
        material = self.material_ac.isChecked()

        iterator = QtGui.QTreeWidgetItemIterator(self.treeWidget)
        while iterator.value():
            item = iterator.value()

            try:
                _type = item.node_type
            except:
                _type = None

            if 'zSolver' == _type:
                item.setHidden(solver)

            if 'zTissue' ==  _type:
                item.setHidden(muscles)

            if 'zTet' == _type:
                item.setHidden(tets)

            if 'zBone' == _type:
                item.setHidden(bones)

            if 'zAttachment' == _type:
                item.setHidden(attachments)

            if 'zFiber' == _type:
                item.setHidden(fiber)

            if 'zMaterial' == _type:
                item.setHidden(material)

            iterator += 1

        self.update_properties()

    def _find_items(self):
        ''' find selected items and expand a parent if found
        '''
        getSelected = self.treeWidget.selectedItems()

        for selected in getSelected:
            name = self._get_name_from_item_data(selected,fullPath=False)

            iterator = QtGui.QTreeWidgetItemIterator(self.treeWidget)
            while iterator.value():
                item = iterator.value()
                other = self._get_name_from_item_data(item,fullPath=False)
                if name == other:
                    if item:
                        if item.parent():
                            item.parent().setExpanded(True)

                iterator += 1

    def _populate(self):
        logger.info( 'populate: {}'.format(self) ) 
        nodes_to_cb = []  # storing nodes to add a delete callback
        sel = mc.ls(sl=True)
        mc.select(cl=True)
        #self.nodeCallbacks.clear()
        self.attrWidgets.clear()
        #self._deferredUpdateRequest.clear()

        #cb2 = om.MDGMessage.addNodeAddedCallback( self._node_created )
        #self.nodeCallbacks['__createCB'] =MCallbackIdWrapper(cb2)

        solvers = None
        try:
            solvers = mm.eval('zQuery -t zSolver')
        except:
            pass
        
        if solvers:
            for solver in solvers:
                solverTransform = mm.eval('zQuery -t zSolverTransform '+solver)[0]
                embedder = mm.eval('zQuery -t zEmbedder '+solver)[0]
                cacheTransform = mm.eval('zQuery -t zCacheTransform '+solver)
                if cacheTransform:
                    cacheTransform = cacheTransform[0]



                s_item = QtGui.QTreeWidgetItem(1)
                s_item.setText(0,solverTransform)
                s_item.setIcon(0,QtGui.QIcon(icons['zSolver']))

                s_item.setData(0,QtCore.Qt.UserRole, util.getDependNode(solverTransform))
                attrs = self.get_properties_wrapper(solverTransform)
                s_item.attrs = attrs[0]
                s_item.attr_order = attrs[1]
                
                
                for zNode in [solver,embedder,cacheTransform]:
                    if zNode:
                        _type = mc.objectType(zNode)

                        st_item = QtGui.QTreeWidgetItem(s_item,1)
                        st_item.setText(0,zNode)
                        st_item.setIcon(0,QtGui.QIcon(icons[_type]))
                        st_item.setData(0,QtCore.Qt.UserRole, util.getDependNode(zNode))
                        attrs = self.get_properties_wrapper(zNode)
                        st_item.attrs = attrs[0]
                        st_item.attr_order = attrs[1]
                        st_item.node_type = _type
                        #nodes_to_cb.append(zNode)

                self.treeWidget.addTopLevelItem(s_item)
                s_item.setExpanded(True)

                #color = QtGui.QColor(168, 34, 3)
                tissue_meshes = self.get_tissue_meshes(solver)
                tissue_items = []
                if tissue_meshes:
                    for mesh in tissue_meshes:
                        item = QtGui.QTreeWidgetItem(s_item,0)
                        item.setText(0,mesh)
                        item.setIcon(0,QtGui.QIcon(icons['zTissue']))
                        item.setData(0,QtCore.Qt.UserRole, util.getDependNode(mesh))
                        item.attrs = []
                        item.attr_order = []
                        # tet---------------------------------------------------------------
                        zNodes = ['zTet','zTissue','zAttachment','zMaterial','zFiber']
                        for zNode in zNodes:
                            nodes = mm.eval('zQuery -t %s %s' % (zNode,mesh))
                            if nodes:
                                for node in nodes:
                                    c_item = QtGui.QTreeWidgetItem(item,1)
                                    c_item.setText(0,node)
                                    c_item.setIcon(0,QtGui.QIcon(icons[zNode]))
                                    c_item.setData(0,QtCore.Qt.UserRole, util.getDependNode(node))
                                    c_item.name = node
                                    c_item.node_type = zNode
                                    attrs = self.get_properties_wrapper(node)
                                    c_item.attrs = attrs[0]
                                    c_item.attr_order = attrs[1]
                                    c_item.node_type = zNode
                                    #nodes_to_cb.append(node)

                        #self.treeWidget.addTopLevelItem(item)

                #---------------------------------------------------------------
                # BONES --------------------------------------------------------
                #---------------------------------------------------------------
                bone_meshes = self.get_bone_meshes(solver)
                if bone_meshes:
                    for mesh in bone_meshes:
                        item3 = QtGui.QTreeWidgetItem(s_item,0)
                        item3.setText(0,mesh)
                        item3.setIcon(0,QtGui.QIcon(icons['zBone']))
                        item3.setData(0,QtCore.Qt.UserRole, util.getDependNode(mesh))
                        item3.attrs = []
                        item3.attr_order = []

                        zBone = mm.eval('zQuery -t zBone '+mesh)[0]
                        b_item = QtGui.QTreeWidgetItem(item3,1)
                        b_item.setText(0,zBone)
                        b_item.setIcon(0,QtGui.QIcon(icons['zBone']))
                        b_item.setData(0,QtCore.Qt.UserRole, util.getDependNode(zBone))
                        attrs = self.get_properties_wrapper(zBone)
                        b_item.attrs = attrs[0]
                        b_item.attr_order = attrs[1]
                        b_item.node_type = 'zBone'
                        #nodes_to_cb.append(zBone)

                        zNodes = ['zAttachment']
                        for zNode in zNodes:

                            nodes = mm.eval('zQuery -t %s %s' % (zNode,zBone))
                            if nodes:
                                for node in nodes:
                                    c_item = QtGui.QTreeWidgetItem(item3,1)
                                    c_item.setText(0,node)
                                    if zNode == 'zAttachment':
                                        source = mm.eval('zQuery -as %s' % node)[0]
                                        #print source,mesh
                                        if source == mesh:
                                            c_item.setIcon(0,QtGui.QIcon(icons['zAttachment_s']))
                                        else:
                                            c_item.setIcon(0,QtGui.QIcon(icons['zAttachment_t']))

                                    c_item.setData(0,QtCore.Qt.UserRole, util.getDependNode(node))
                                    attrs = self.get_properties_wrapper(node)
                                    c_item.attrs = attrs[0]
                                    c_item.attr_order = attrs[1]
                                    c_item.node_type = zNode
                                    #nodes_to_cb.append(node)

                #---------------------------------------------------------------
                # BCLOTH --------------------------------------------------------
                #---------------------------------------------------------------
                cloth_meshes = self.get_cloth_meshes(solver)
                cloth_items = []
                if cloth_meshes:
                    for mesh in cloth_meshes:
                        item = QtGui.QTreeWidgetItem(s_item,0)
                        item.setText(0,mesh)
                        item.setIcon(0,QtGui.QIcon(icons['zTissue']))
                        item.setData(0,QtCore.Qt.UserRole, util.getDependNode(mesh))
                        item.attrs = []
                        item.attr_order = []
                        # tet---------------------------------------------------------------
                        zNodes = ['zCloth','zAttachment','zMaterial','zFiber']
                        for zNode in zNodes:
                            nodes = mm.eval('zQuery -t %s %s' % (zNode,mesh))
                            if nodes:
                                for node in nodes:
                                    c_item = QtGui.QTreeWidgetItem(item,1)
                                    c_item.setText(0,node)
                                    c_item.setIcon(0,QtGui.QIcon(icons[zNode]))
                                    c_item.setData(0,QtCore.Qt.UserRole, util.getDependNode(node))
                                    c_item.name = node
                                    c_item.node_type = zNode
                                    attrs = self.get_properties_wrapper(node)
                                    c_item.attrs = attrs[0]
                                    c_item.attr_order = attrs[1]
                                    c_item.node_type = zNode

                        #self.treeWidget.addTopLevelItem(item3)


            # for node in nodes_to_cb:
            #     #print node
            #     nodeObj = util.getDependNode(node)
            #     cb = om.MNodeMessage.addNodeAboutToDeleteCallback(nodeObj, self.onDirtyPlug, None)

                
            #     #cb.setRegisteringCallableScript()
            #     self.nodeCallbacks[node] =MCallbackIdWrapper(cb)


            self._foreground_item_enable_color()



    # def _node_created(self,*args,**kwargs):
    #     #print 'node created: ',args,kwargs
    #     #print mc.ls(sl=True),'what what'
    #     mobject = args[0]
    #     if mobject.hasFn(om.MFn.kDagNode):
    #         dagpath = om.MDagPath()
    #         om.MFnDagNode(mobject).getPath(dagpath)
    #         name = dagpath.fullPathName()
    #     else:
    #         name = om.MFnDependencyNode(mobject).name()
    #     print 'created:',name
    #     if mc.objectType(name) in con.ZNODES:
    #         #print 'found a match',mc.objectType(name)
    #         mc.select(name)

    #         refreshFunc = functools.partial(
    #                 self._refresh_ui,
    #                 type='nodeCreated')
    #         mc.evalDeferred(refreshFunc,low=True)


            
    def _foreground_item_enable_color(self):
        iterator = QtGui.QTreeWidgetItemIterator(self.treeWidget)
        while iterator.value():
            item = iterator.value()
            name = self._get_name_from_item_data(item)

            if mc.objExists(name+'.enable'):
                if mc.getAttr(name+'.enable') == 1:
                    item.setForeground(0,QtGui.QBrush(QtGui.QColor("#C8C8C8")))
                else:
                    item.setForeground(0,QtGui.QBrush(QtGui.QColor("grey")))
            if mc.objExists(name+'.envelope'):
                if mc.getAttr(name+'.envelope') == 1:
                    item.setForeground(0,QtGui.QBrush(QtGui.QColor("#C8C8C8")))
                else:
                    item.setForeground(0,QtGui.QBrush(QtGui.QColor("grey")))

            iterator += 1




    def _refresh_ui(self,*args,**kwargs):
        logger.info( 'refresh: {} {}'.format(args,kwargs) ) 

        #TODO do a more selective refresh rather then brute force
        sel = mc.ls(sl=True)
        self.treeWidget.clear()
        self._populate()
        mc.select(sel,r=True)
        self.update_properties()
        self._selection_changed()
        self._highlight_parent()
        self._find_items()


    def _delete_nodes(self):
        sel = mc.ls(sl=True)
        non_isolate_delete = ('zTissue','zTet','zCloth','zBone')
        ziva_rm = ('transform','mesh')
        delete_me = ('zAttachment','zFiber','zMaterial')
        for s in sel:
            _type = mc.objectType(s)
            if _type in non_isolate_delete:
                mc.warning('selected nodes cannot be deleted in isolation ',s)
                continue

            if _type in ziva_rm:
                mc.select(s)
                body = mm.eval('zQuery -m')
                mc.select(body,r=True)
                mm.eval('ziva -rm')
                #mc.delete()   
                continue
            if _type in delete_me:
                mc.delete(s)    

        mc.evalDeferred(self._refresh_ui,low=True)

    def get_properties_wrapper(self,zNode):

        # get base attributes and values for nodes------------------------------
        attrList = bse.build_attr_list(zNode)
        attrs = bse.build_attr_key_values(zNode,attrList)

        #add maps if needed-----------------------------------------------------
        maps = maplist.get(mc.objectType(zNode),[])
        niceMaps = niceMaplist.get(mc.objectType(zNode),[])
        for m,n in zip(maps,niceMaps):
            attrs[m] = {}
            attrs[m]['type'] = 'weight'
            attrs[m]['value'] = ''
            attrs[m]['locked'] = False
            attrs[m]['niceName'] = n
        
        # find order of attributes to display-----------------------------------
        all_attrs = mc.listAttr(zNode)
        all_attrs.extend(maps)
        order = []
        for o in all_attrs:
            if o in attrs:
                order.append(o)

        #print order
        return attrs,order


    def search_tree(self):
        search_text = self.line_edit.text()

        iterator = QtGui.QTreeWidgetItemIterator(self.treeWidget)
        while iterator.value():
            item = iterator.value()
            item_text = item.text(0)
            if search_text in item_text:
                item.setHidden(False)
                if item.parent():
                    item.parent().setHidden(False)
                    #item.parent().setExpanded(True)
            else:
                item.setHidden(True)

            iterator += 1


    def _selection_changed(self,*args, **kwargs):
        logger.info( 'SJ: refresh deferred: ' ) 
        self.treeWidget.blockSignals(True)
        self.treeWidget.clearSelection()

        sel = mc.ls(sl=True)

        for s in sel:
            items = self.treeWidget.findItems(s, QtCore.Qt.MatchExactly | QtCore.Qt.MatchRecursive, 0)
            for item in items:
                item.setSelected(True)


        self.treeWidget.blockSignals(False)
        self.update_properties()



    def tree_changed(self):
        #print 'ui:tree_changed'
        self.blockSignals(True)
        self.prop.blockSignals(True)

        mc.select(cl=True)
        new = []
        getSelected = self.treeWidget.selectedItems()
        for selected in getSelected:
            name = self._get_name_from_item_data(selected)
            if name:
                mc.select(name,add=True)

        self._highlight_parent()
        self.progressBar.hide()
        self.prop.blockSignals(False)
        self.blockSignals(False)
        
        #print 'ui:tree_changed-finished'

    def _highlight_parent(self):
        '''
        This looks what items are selected in tree widget.  If item selected has
        a parent it highlights it a lighter shade of blue then the selection 
        highlighting.  Similiar to maya's outliner functionality
        '''

        getSelected = self.treeWidget.selectedItems()
        # color back to original
        iterator = QtGui.QTreeWidgetItemIterator(self.treeWidget)
        while iterator.value():
            item = iterator.value()
            item.setBackground(0,QtGui.QBrush(QtGui.QColor("#2C2B2B")))
            iterator += 1


        # for i in range(0,self.treeWidget.topLevelItemCount()):
        #     top = self.treeWidget.topLevelItem(i)
        #     top.setBackground(0,QtGui.QBrush(QtGui.QColor("#2C2B2B")))

        # color if child is selected
        #parents = _get_parent_items
        names = []
        for selected in getSelected:
            names.append(self._get_name_from_item_data(selected,fullPath=True))

        iterator = QtGui.QTreeWidgetItemIterator(self.treeWidget)
        while iterator.value():
            item = iterator.value()
            other = self._get_name_from_item_data(item,fullPath=True)
            if other in names:
                for parent in self._get_parent_items(item):
                    parent.setBackground(0,QtGui.QBrush(QtGui.QColor("#414D5A")))
            iterator += 1

    def _get_parent_items(self,item):
        #TODO this hack
        tmp = []
        if item.parent():
            tmp.append(item.parent())
            if item.parent().parent():
                tmp.append(item.parent().parent())
        return tmp

    def _get_name_from_item_data(self,item,fullPath=True):
        mobject = item.data(0,QtCore.Qt.UserRole)
        if mobject:
            if mobject.hasFn(om.MFn.kDagNode):
                dagpath = om.MDagPath()
                om.MFnDagNode(mobject).getPath(dagpath)
                if fullPath:
                    return dagpath.fullPathName()
                else:
                    return dagpath.partialPathName()
            else:
                return om.MFnDependencyNode(mobject).name()
        else:
            return None



    def get_cloth_meshes(self,solver):
        meshes = mm.eval('zQuery -t zCloth -m ' + solver)
        return meshes

    def get_tissue_meshes(self,solver):
        meshes = mm.eval('zQuery -t zTissue -m '+ solver)
        return meshes

    def get_bone_meshes(self,solver):
        meshes = mm.eval('zQuery -t zBone -m ' + solver)
        return meshes


    def script_job(self):
        self.jobNum = []
        self.jobNum.append(mc.scriptJob( event= ["SelectionChanged",self._selection_changed], protected=True))
        self.jobNum.append(mc.scriptJob( event= ["NameChanged",self._name_changed], protected=True))
        self.jobNum.append(mc.scriptJob( event= ["deleteAll",self._refresh_ui_deferred], protected=True))
        self.jobNum.append(mc.scriptJob( event= ["Undo",self._refresh_ui_deferred], protected=True))
        self.jobNum.append(mc.scriptJob( event= ["Redo",self._refresh_ui_deferred], protected=True))
        #self.jobNum.append(mc.scriptJob( event= ["NewSceneOpened",self._refresh_ui_deferred], protected=True))
        #self.jobNum.append(mc.scriptJob( event= ["PostSceneRead",self._refresh_ui_deferred], protected=True))
        self.jobNum.append(mc.scriptJob( event= ["SceneOpened",self._refresh_ui_deferred], protected=True))

    def _refresh_ui_deferred(self,*args,**kwargs):
        logger.info( 'SJ: refresh deferred: ' ) 
        mc.evalDeferred(self._refresh_ui, low=True)



    def _name_changed(self,*args, **kwargs):
        logger.info( 'SJ: name changed: ' ) 
        #print 'ui:_name_changed'
        self.treeWidget.blockSignals(True)
        #iterate through all items in tree
        iterator = QtGui.QTreeWidgetItemIterator(self.treeWidget)
        while iterator.value():
            item = iterator.value()
            name = self._get_name_from_item_data(item,fullPath=False)
            if name:
                item.setText(0,name)

            iterator += 1

        #I am being lazy here, I am just redrawing whole property widget
        #self.update_properties()

        self.treeWidget.blockSignals(False)



    # If it's floating or docked, this will run and delete it self when it closes.
    # You can choose not to delete it here so that you can still re-open it through the right-click menu, but do disable any callbacks/timers that will eat memory
    def dockCloseEventTriggered(self):
        self.deleteInstances()
        self._clear_callbacks()
        for job in self.jobNum:
            mc.scriptJob( kill=job, force=True)

        self.prop._clear_callbacks()
        self.save_settings()


        #when ever you finish doing your stuff
        #import maya.OpenMaya as OpenMaya
        #OpenMaya.MMessage.removeCallback(self.idx)

    # Delete any instances of this class
    def deleteInstances(self):
        mayaMainWindowPtr = omui.MQtUtil.mainWindow() 
        mayaMainWindow = wrapInstance(long(mayaMainWindowPtr), QtGui.QMainWindow) # Important that it's QMainWindow, and not QWidget/QDialog

        # Go through main window's children to find any previous instances
        for obj in mayaMainWindow.children():
            #print  str(type(obj))
            #if type( obj ) == "<class 'maya.app.general.mayaMixin.MayaQDockWidget'>":
            #print 'DFDDDDDDDDDDDDDDDDDDD'
            #if obj.widget().__class__ == self.__class__: # Alternatively we can check with this, but it will fail if we re-evaluate the class
            try:
                #print 'on ',obj.widget().objectName() 
                if obj.widget().objectName() == self.__class__.toolName: # Compare object names
                    # If they share the same name then remove it
                    # print 'Deleting instance {0}'.format(obj)
                    mayaMainWindow.removeDockWidget(obj) # This will remove from right-click menu, but won't actually delete it! ( still under mainWindow.children() )
                    # Delete it for good
                    obj.setParent(None)
                    obj.deleteLater() 
            except:
                pass


    def onDirtyPlug(self, node, plug, *args, **kwargs):
        '''Add to the self._deferredUpdateRequest member variable that is then 
        deferred processed by self._processDeferredUpdateRequest(). 
        '''
        self._deferredUpdateRequest = {}
        iterator = QtGui.QTreeWidgetItemIterator(self.treeWidget)
        while iterator.value():
            item = iterator.value()
            mobject = item.data(0,QtCore.Qt.UserRole)
            if mobject:
                if node == mobject:
                    #print 'FOUND',self._get_name_from_item_data(item),item
                    #self._deferredUpdateRequest.append(item)

                    parent = item.parent()
                    idx = parent.indexOfChild(item)
                    parent.takeChild(idx)

                
        
            iterator += 1
        refreshFunc = functools.partial(
                self._refresh_ui,
                type='onDirtyPlug')
        mc.evalDeferred(refreshFunc,low=True)

        #if len(self._deferredUpdateRequest) > 0:
        #mc.evalDeferred(self._processDeferredUpdateRequest, low=True)




    def _processDeferredUpdateRequest(self):
        '''Retrieve the attr value and set the widget value
        '''
        #print 'doing stuff'   
        self.blockSignals(True)
        for item in self._deferredUpdateRequest:
            parent = item.parent()
            idx = parent.indexOfChild(item)
            parent.takeChild(idx)
        self._deferredUpdateRequest.clear()
        self.blockSignals(False)

    def _clear_callbacks(self):
        self.nodeCallbacks.clear()

        
    # Show window with docking ability
    def run(self):
        mayaMainWindowPtr = omui.MQtUtil.mainWindow() 
        mayaMainWindow = wrapInstance(long(mayaMainWindowPtr), QtGui.QMainWindow) # Important that it's QMainWindow, and not QWidget/QDialog
        test = True
        for obj in mayaMainWindow.children():
            try:
                if obj.widget().objectName() == self.__class__.toolName: # Compare object names
                    test=False
                    continue
            except:
                pass
        if test:
            self.show(dockable = True)
        
        #self.show()



