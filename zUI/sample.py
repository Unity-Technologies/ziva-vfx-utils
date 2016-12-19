from shiboken import wrapInstance
from PySide import QtGui, QtCore
from maya import OpenMayaUI as omui
import maya.cmds as mc
import maya.mel as mm


'''
to run in maya:

import zUI.sample as sam
myWin = sam.SampleUi()
myWin.run()

'''


class SampleUi(QtGui.QDialog):
    toolName = 'zivaWidget'
    def __init__(self, parent=None):
        super(SampleUi, self).__init__(parent)

        mayaMainWindowPtr = omui.MQtUtil.mainWindow() 
        self.mayaMainWindow = wrapInstance(long(mayaMainWindowPtr), QtGui.QMainWindow)
        self.setObjectName(self.__class__.toolName) # Make this unique enough if using it to clear previous instance!

        self.setWindowTitle('Sample')  
        self.resize(550, 470)

        self.create_layout()


    def create_layout(self):

        # create a tree widget
        self.treeWidget = QtGui.QTreeWidget()
        self.treeWidget.setColumnCount(1)
        self.treeWidget.header().close()

        # create some buttons
        self.button1 = QtGui.QPushButton('one',self)
        self.button2 = QtGui.QPushButton('two',self)
        self.button3 = QtGui.QPushButton('three',self)

        # a layout to put the stuff in
        main_layout = QtGui.QVBoxLayout()
        main_layout.setContentsMargins(2, 2, 2, 2)
        main_layout.setSpacing(2)
        
        # add widgets to layout
   
        main_layout.addWidget(self.button1)
        main_layout.addWidget(self.button2)
        main_layout.addWidget(self.button3)
        main_layout.addWidget(self.treeWidget)
        
        # need to set layout for window
        self.setLayout(main_layout)

        # connect button action to methods
        self.button1.clicked.connect(self.button_clicked)
        self.button2.clicked.connect(self.button_clicked)
        self.button3.clicked.connect(self.button_clicked)

        # create some tree widget items to fill tree widget
        item = QtGui.QTreeWidgetItem()
        item.setText(0,'tree item')

        # these are children
        c_item = QtGui.QTreeWidgetItem(item)
        c_item.setText(0,'child tree item')

        c_item2 = QtGui.QTreeWidgetItem(item)
        c_item2.setText(0,'child tree item2')

        # add top one to tree widget
        self.treeWidget.addTopLevelItem(item)

    def button_clicked(self):
        print 'button clicked'

    # Show window with docking ability
    def run(self):
        self.show()



