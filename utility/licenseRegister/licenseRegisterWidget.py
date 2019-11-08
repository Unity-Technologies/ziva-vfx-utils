try:
    from PySide2.QtCore import * 
    from PySide2.QtGui import * 
    from PySide2.QtWidgets import *
    from PySide2 import __version__
    from shiboken2 import wrapInstance 
except ImportError:
    from PySide.QtCore import * 
    from PySide.QtGui import * 
    from PySide import __version__
    from shiboken import wrapInstance 

from maya import OpenMayaUI as omui
from maya.app.general.mayaMixin import MayaQWidgetBaseMixin


mayaMainWindowPtr = omui.MQtUtil.mainWindow()
mayaMainWindow = wrapInstance(long(mayaMainWindowPtr), QWidget)

class LicenseRegisterWidget(MayaQWidgetBaseMixin, QWidget):

    WIDGET_NAME = 'ZivaLicenseRegister'

    def __init__(self, *args, **kwargs):
        super(LicenseRegisterWidget, self).__init__(*args, **kwargs)
        self.setObjectName(self.WIDGET_NAME)
        self.setupControls()
        self.setupSlots()


    def setupControls(self):
        # Node-based license group
        self.rdoNodeBasedLic = QRadioButton('Node-based License')
        self.edtFilePath = QLineEdit()
        nbFormLayout = QFormLayout()
        nbFormLayout.addRow('License File Path:', self.edtFilePath)
        nbLayout = QVBoxLayout()
        nbLayout.addWidget(self.rdoNodeBasedLic)
        nbLayout.addLayout(nbFormLayout)
        nbGroup = QGroupBox()
        nbGroup.setLayout(nbLayout)
        
        # Floating license group
        self.rdoFloatingLic = QRadioButton('Floating License')
        self.edtServerAddr = QLineEdit()
        self.edtServerPort = QLineEdit()
        fltFormLayout = QFormLayout()
        fltFormLayout.addRow('Server Address:', self.edtServerAddr)
        fltFormLayout.addRow('Server Port:', self.edtServerPort)

        fltLayout = QVBoxLayout()
        fltLayout.addWidget(self.rdoFloatingLic)
        fltLayout.addLayout(fltFormLayout)
        fltGroup = QGroupBox()
        fltGroup.setLayout(fltLayout)
        
        # RadioButton exclusive group
        rdoLicType = QButtonGroup(self)
        rdoLicType.addButton(self.rdoNodeBasedLic)
        rdoLicType.addButton(self.rdoFloatingLic)
        rdoLicType.setExclusive(True)

        # Status group
        self.lblStatus = QLabel()
        stsGroup = QGroupBox('Status')
        stsLayout = QVBoxLayout()
        stsLayout.addWidget(self.lblStatus)
        stsGroup.setLayout(stsLayout)

        # Widget
        layout = QVBoxLayout()
        layout.addWidget(nbGroup)
        layout.addWidget(fltGroup)
        layout.addWidget(stsGroup)
        self.btnRegister = QPushButton('Register')
        layout.addWidget(self.btnRegister)
        self.setLayout(layout)
        self.setWindowTitle('Register Ziva VFX License')
        self.setFixedSize(350, 300)

        # Setup controls init state and value
        self.rdoNodeBasedLic.setChecked(True)
        self.edtServerAddr.setEnabled(False)
        self.edtServerPort.setEnabled(False)
        self.edtServerPort.setText('5053')


    def setupSlots(self):
        self.btnRegister.clicked.connect(self.onRegister)
        self.rdoNodeBasedLic.clicked.connect(self.onLicenseTypeChange)
        self.rdoFloatingLic.clicked.connect(self.onLicenseTypeChange)

    
    def onRegister(self):
        self.lblStatus.setText('register')


    def onLicenseTypeChange(self):
        if self.rdoNodeBasedLic.isChecked():
            self.lblStatus.setText('node-based license')
        else:
            self.lblStatus.setText('floating license')


def main():
    # Check and prevent multiple instances.
    # See https://stackoverflow.com/questions/33563031/dockable-window-in-maya-with-pyside-clean-up for details.
    for obj in mayaMainWindow.children():
        if issubclass(type(obj), MayaQWidgetBaseMixin):
            if (obj.objectName() == LicenseRegisterWidget.WIDGET_NAME):
                obj.setParent(None)
                obj.deleteLater()

    instance = LicenseRegisterWidget()
    instance.show()
