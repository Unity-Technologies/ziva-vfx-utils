# from PySide import QtGui, QtCore
from Qt import QtGui, QtWidgets, QtCore  # https://github.com/mottosso/Qt.py by Marcus Ottosson

import logging

logger = logging.getLogger(__name__)


class ButtonLineEdit(QtWidgets.QLineEdit):
    # buttonClicked = QtCore.pyqtSignal(bool)

    def __init__(self, icon_file, parent=None):
        super(ButtonLineEdit, self).__init__(parent)

        logger.debug('instantiated: {}'.format(self))
        self.button = QtWidgets.QToolButton(self)
        self.button.setIcon(QtGui.QIcon(icon_file))
        self.button.setStyleSheet('border: 0px; padding: 0px;')
        self.button.setCursor(QtCore.Qt.PointingHandCursor)
        self.button.hide()

        # connections------------------------------------------------------------
        self.button.clicked.connect(self.button_clicked)
        self.textChanged.connect(self.update_button)

        frameWidth = self.style().pixelMetric(QtWidgets.QStyle.PM_DefaultFrameWidth)
        buttonSize = self.button.sizeHint()

        self.setStyleSheet('QLineEdit {padding-right: %dpx; }' % (
        buttonSize.width() + frameWidth + 1))
        self.setMinimumSize(max(self.minimumSizeHint().width(),
                                buttonSize.width() + frameWidth * 2 + 2),
                            max(self.minimumSizeHint().height(),
                                buttonSize.height() + frameWidth * 2 + 2))

    def resizeEvent(self, event):
        buttonSize = self.button.sizeHint()
        frameWidth = self.style().pixelMetric(QtWidgets.QStyle.PM_DefaultFrameWidth)
        self.button.move(self.rect().right() - frameWidth - buttonSize.width(),
                         (self.rect().bottom() - buttonSize.height() + 1) / 2)
        super(ButtonLineEdit, self).resizeEvent(event)

    def button_clicked(self):
        self.clear()

    def update_button(self):
        if self.text():
            self.button.setVisible(True)
        else:
            self.button.setVisible(False)
