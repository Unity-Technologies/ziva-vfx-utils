from PySide2.QtCore import *
from PySide2.QtGui import *
from PySide2.QtWidgets import *
from PySide2 import __version__
from shiboken2 import wrapInstance
from maya import OpenMayaUI as mui
from maya.app.general.mayaMixin import MayaQWidgetBaseMixin
from maya import cmds

from .licenseRegister import register_node_locked_license, register_floating_license, LICENSE_FILE_NAME
from os import path
import re

mayaMainWindowPtr = mui.MQtUtil.mainWindow()
mayaMainWindow = wrapInstance(int(mayaMainWindowPtr), QWidget)


class LicenseRegisterWidget(MayaQWidgetBaseMixin, QWidget):

    WIDGET_NAME = 'ZivaLicenseRegister'

    DEFAULT_SERVER_PORT = 5053

    MSG_EMPTY_FILE_PATH = 'Empty license file path.'
    MSG_EMPTY_SERVER_ADDR = 'Empty server address.'
    MSG_INVALID_SERVER_ADDR = 'Invalid server address. Should be a computer name or IP address.'
    MSG_INVALID_SERVER_PORT = 'Invalid server port. Should be a number between 0 ~ 65535.'
    MSG_SUCCEED_REGISTER_NODE_LOCKED_LIC = 'Success: license file copied to {}.'
    MSG_SUCCEED_REGISTER_FLOATING_LIC = 'Success: license server info added to {}.'
    MSG_RESTART_MAYA = '\n\nPlease restart Maya to make the license take effect.'
    MSG_NEED_ADMIN_PRIVILEGE = '''\n\nNeed administrator privilege to access destination path.
Try launching Maya as administrator, and retry.'''

    ACCESS_DENY_KEYWORD = 'Permission denied'

    def __init__(self, *args, **kwargs):
        super(LicenseRegisterWidget, self).__init__(*args, **kwargs)
        self.setObjectName(self.WIDGET_NAME)
        try:
            self.modulePath = cmds.getModulePath(moduleName='ZivaVFX')
        except:
            # Ziva VFX module path is not set, resort to Ziva VFX plugin path
            pluginPath = cmds.pluginInfo("ziva", query=True, path=True)
            self.modulePath = path.dirname(pluginPath)

        self.setupControls()
        self.setupSlots()

    def setupControls(self):
        # Node-locked license group
        self.rdoNodeLockedLic = QRadioButton('Node-locked License')
        self.edtFilePath = QLineEdit()
        self.btnBrowse = QPushButton('Browse')
        filePathLayout = QHBoxLayout()
        filePathLayout.addWidget(QLabel('License File Path:'))
        filePathLayout.addWidget(self.edtFilePath)
        filePathLayout.addWidget(self.btnBrowse)
        nbLayout = QVBoxLayout()
        nbLayout.addWidget(self.rdoNodeLockedLic)
        nbLayout.addLayout(filePathLayout)
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
        rdoLicType.addButton(self.rdoNodeLockedLic)
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
        self.setFixedWidth(400)

        # Setup controls init state and value
        self.rdoNodeLockedLic.setChecked(True)
        self.edtServerAddr.setEnabled(False)
        self.edtServerPort.setEnabled(False)
        self.edtServerPort.setPlaceholderText(str(self.DEFAULT_SERVER_PORT))
        self.lblStatus.setWordWrap(True)
        self.lblStatus.setTextInteractionFlags(Qt.TextSelectableByMouse)
        self.licFilePath = ''
        self.srvAddr = ''
        self.srvPort = self.DEFAULT_SERVER_PORT

    def setupSlots(self):
        self.btnBrowse.clicked.connect(self.onBrowse)
        self.btnRegister.clicked.connect(self.onRegister)
        self.rdoNodeLockedLic.clicked.connect(self.onLicenseTypeChange)
        self.rdoFloatingLic.clicked.connect(self.onLicenseTypeChange)

    def onBrowse(self):
        retVal = QFileDialog.getOpenFileName(self, 'Locate RLM License File', self.modulePath,
                                             'RLM License File (*.lic)')
        self.edtFilePath.setText(retVal[0])

    def onRegister(self):
        isNodeLockedMode = self.rdoNodeLockedLic.isChecked()
        if self._validateInputs(isNodeLockedMode):
            try:
                if isNodeLockedMode:
                    register_node_locked_license(self.modulePath, self.licFilePath)
                else:
                    register_floating_license(self.modulePath, self.srvAddr, 'ANY', self.srvPort)
            except Exception as e:
                errorMsg = str(e)
                if self.ACCESS_DENY_KEYWORD in errorMsg:
                    errorMsg += self.MSG_NEED_ADMIN_PRIVILEGE
                self.lblStatus.setText(errorMsg)
                return

            if isNodeLockedMode:
                fileName = path.basename(self.licFilePath)
                self.lblStatus.setText(
                    self.MSG_SUCCEED_REGISTER_NODE_LOCKED_LIC.format(
                        path.join(self.modulePath, fileName)) + self.MSG_RESTART_MAYA)
            else:
                self.lblStatus.setText(
                    self.MSG_SUCCEED_REGISTER_FLOATING_LIC.format(
                        path.join(self.modulePath, LICENSE_FILE_NAME)) + self.MSG_RESTART_MAYA)

    def onLicenseTypeChange(self):
        isNodeLockedMode = self.rdoNodeLockedLic.isChecked()
        self.edtFilePath.setEnabled(isNodeLockedMode)
        self.btnBrowse.setEnabled(isNodeLockedMode)
        self.edtServerAddr.setEnabled(not isNodeLockedMode)
        self.edtServerPort.setEnabled(not isNodeLockedMode)

    def _validateInputs(self, isNodeLockedMode):
        '''
        Validate user inputs and show error message through status label.
        
        isNodeLockedMode (bool): Which license type to validate

        Returns: bool
            True for valid inputs to proceed, False otherwise.
        '''
        if isNodeLockedMode:
            self.licFilePath = self.edtFilePath.text()
            if not self.licFilePath:
                self.lblStatus.setText(self.MSG_EMPTY_FILE_PATH)
                return False
            # Delegate node-locked license input validation to backend,
            # it throws when file operation failed.
            return True

        # Validate floating license server inputs
        self.srvAddr = self.edtServerAddr.text()
        validHostName, errMsg = self._validateHostName(self.srvAddr)
        if not validHostName:
            self.lblStatus.setText(errMsg if errMsg else self.MSG_INVALID_SERVER_ADDR)
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
        Validate input hostname string, refer to following links for the implementation details,
            http://man7.org/linux/man-pages/man7/hostname.7.html
            https://stackoverflow.com/questions/2532053/validate-a-hostname-string

        hostname (str): Input hostname, can be a computer name or IP address

        Returns: bool, str(optional)
            True for valid inputs to proceed, False otherwise.
            An optional error message string may come with the result.
        '''
        if not hostname:
            return False, self.MSG_EMPTY_SERVER_ADDR

        if len(hostname) > 255:
            return False, ''

        if hostname[-1] == '.':
            hostname = hostname[:-1]  # strip exactly one dot from the right, if present
        allowed = re.compile(r'(?!-)[A-Z\d-]{1,63}(?<!-)$', re.IGNORECASE)
        return all(allowed.match(x) for x in hostname.split('.')), ''


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
