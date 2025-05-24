# -*- coding: utf-8 -*-

from PyQt5 import QtWidgets


class ProgressDialog(QtWidgets.QDialog):
    def __init__(self, min, max, parent=None):
        QtWidgets.QDialog.__init__(self, parent)

        # self.setWindowFlags(Qt.SplashScreen | Qt.FramelessWindowHint)
        # self.setWindowFlags(
        #     Qt.SplashScreen | Qt.WindowStaysOnTopHint | Qt.WindowTitleHint)
        # self.setWindowFlags(Qt.WindowTitleHint | Qt.WindowCloseButtonHint)

        self.progressLabel = QtWidgets.QLabel()

        self.progressBar = QtWidgets.QProgressBar()
        self.progressBar.setMinimum(min)
        self.setMaximum(max)

        self.cancelButton = QtWidgets.QPushButton()
        self.cancelButton.clicked.connect(self.reject)

        progressWidget = QtWidgets.QWidget()
        progressWidget.setLayout(QtWidgets.QHBoxLayout())
        progressWidget.layout().setContentsMargins(0, 0, 0, 0)
        progressWidget.layout().addWidget(self.progressBar)
        progressWidget.layout().addWidget(self.cancelButton)

        self.extraFrame = QtWidgets.QFrame()
        self.extraFrame.setFrameStyle(QtWidgets.QFrame.StyledPanel)
        self.extraFrame.setFrameShadow(QtWidgets.QFrame.Sunken)
        self.extraFrame.setLayout(QtWidgets.QVBoxLayout())
        self.extraFrame.layout().setContentsMargins(0, 0, 0, 0)
        self.extraFrame.setVisible(False)

        self.setLayout(QtWidgets.QVBoxLayout())
        self.layout().addWidget(self.progressLabel)
        self.layout().addWidget(progressWidget)
        self.layout().addWidget(self.extraFrame)

        self.reset()

        self.rejected.connect(self.rejectedSlot)

    def rejectedSlot(self):
        self.cancelFlag = True

    def reset(self):
        self.cancelFlag = False
        self.progressLabel.setText("")
        self.progressBar.setValue(0)
        self.setVisible(False)

    def wasCanceled(self):
        return self.cancelFlag

    def setCancelText(self, string):
        self.cancelButton.setText(string)

    def setCancellable(self, val):
        self.cancelButton.setVisible(val)

    def setMaximum(self, val):
        self.progressBar.setMaximum(val)

    def setProgressLabel(self, string):
        self.progressLabel.setText(string)

    def setProgressValue(self, val):
        self.progressBar.setValue(val)

    def maximum(self):
        return self.progressBar.maximum()
