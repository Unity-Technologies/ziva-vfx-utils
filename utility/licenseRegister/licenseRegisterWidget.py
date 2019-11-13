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
import maya.cmds as cmds

from licenseRegister import register_node_based_license, register_floating_license, LICENSE_FILE_NAME
from os import path
import re

mayaMainWindowPtr = omui.MQtUtil.mainWindow()
mayaMainWindow = wrapInstance(long(mayaMainWindowPtr), QWidget)


class LicenseRegisterWidget(MayaQWidgetBaseMixin, QWidget):

    WIDGET_NAME = 'ZivaLicenseRegister'

    DEFAULT_SERVER_PORT = 5053

    MSG_EMPTY_FILE_PATH = 'Empty license file path.'
    MSG_EMPTY_SERVER_ADDR = 'Empty server address.'
    MSG_INVALID_SERVER_ADDR = 'Invalid server address. Should be a computer name or IP address.'
    MSG_INVALID_SERVER_PORT = 'Invalid server port. Should be a number between 0 ~ 65536.'

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
        stsLayout.addStretch()
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
        self.setFixedWidth(350)

        # Setup controls init state and value
        self.rdoNodeBasedLic.setChecked(True)
        self.edtServerAddr.setEnabled(False)
        self.edtServerPort.setEnabled(False)
        self.edtServerPort.setPlaceholderText(str(self.DEFAULT_SERVER_PORT))
        self.lblStatus.setWordWrap(True)
        self.lblStatus.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.licFilePath = ''
        self.srvAddr = ''
        self.srvPort = self.DEFAULT_SERVER_PORT

    def setupSlots(self):
        self.btnRegister.clicked.connect(self.onRegister)
        self.rdoNodeBasedLic.clicked.connect(self.onLicenseTypeChange)
        self.rdoFloatingLic.clicked.connect(self.onLicenseTypeChange)

    def onRegister(self):
        isNodeBasedMode = self.rdoNodeBasedLic.isChecked()
        if self._validateInputs(isNodeBasedMode):
            modulePath = cmds.getModulePath(moduleName='ZivaVFX')
            try:
                if isNodeBasedMode:
                    register_node_based_license(modulePath, self.licFilePath)
                else:
                    register_floating_license(modulePath, self.srvAddr, 'ANY', self.srvPort)
            except Exception as e:
                self.lblStatus.setText(str(e))
                return

            if isNodeBasedMode:
                fileName = path.basename(self.licFilePath)
                self.lblStatus.setText('License file copies to {} successfully.'.format(
                    path.join(modulePath, fileName)))
            else:
                self.lblStatus.setText('License server info adds to {} successfully.'.format(
                    path.join(modulePath, LICENSE_FILE_NAME)))

    def onLicenseTypeChange(self):
        isNodeBasedMode = self.rdoNodeBasedLic.isChecked()
        self.edtFilePath.setEnabled(isNodeBasedMode)
        self.edtServerAddr.setEnabled(not isNodeBasedMode)
        self.edtServerPort.setEnabled(not isNodeBasedMode)

    def _validateInputs(self, isNodeBasedMode):
        '''
        Validate user inputs and show error message through status label.
        
        isNodeBasedMode (bool): Which license type to validate

        Returns: bool
            True for valid inputs to proceed, False otherwise.
        '''
        if isNodeBasedMode:
            self.licFilePath = self.edtFilePath.text()
            if not self.licFilePath:
                self.lblStatus.setText(self.MSG_EMPTY_FILE_PATH)
                return False
            # Delegate node based license input validation to backend,
            # it throws when file operation failed.
            return True

        # Validate floating license server inputs
        self.srvAddr = self.edtServerAddr.text()
        if not self.srvAddr:
            self.lblStatus.setText(self.MSG_EMPTY_SERVER_ADDR)
            return False

        validHostName = self._validateHostName(self.srvAddr)
        if not validHostName:
            self.lblStatus.setText(self.MSG_INVALID_SERVER_ADDR)
            return False

        strSrvPort = self.edtServerPort.text()
        if not strSrvPort:
            self.srvPort = self.DEFAULT_SERVER_PORT
            return True

        try:
            self.srvPort = int(strSrvPort)
            validSrvPort = (0 <= self.srvPort < 65536)
            if not validSrvPort:
                self.lblStatus.setText(self.MSG_INVALID_SERVER_PORT)
                return False
        except:
            self.lblStatus.setText(self.MSG_INVALID_SERVER_PORT)
            return False

        return True

    def _validateHostName(self, hostname):
        '''
        Refer to following links,
            http://man7.org/linux/man-pages/man7/hostname.7.html
            https://stackoverflow.com/questions/2532053/validate-a-hostname-string
        '''
        if len(hostname) > 255:
            return False
        if hostname[-1] == ".":
            hostname = hostname[:-1]  # strip exactly one dot from the right, if present
        allowed = re.compile(r"(?!-)[A-Z\d-]{1,63}(?<!-)$", re.IGNORECASE)
        return all(allowed.match(x) for x in hostname.split("."))


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
