# -*- coding: utf-8; Mode: Python; indent-tabs-mode: nil; tab-width: 4 -*-
#
# Copyright (C) 2013 Canonical Ltd.
#
# Author:
#   Aurélien Gâteau <agateau@kde.org>
#
# This file is part of Ubiquity.
#
# Ubiquity is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free
# Software Foundation; either version 2 of the License, or at your option)
# any later version.
#
# Ubiquity is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE. See the GNU General Public License for
# more details.
#
# You should have received a copy of the GNU General Public License along
# with Ubiquity; if not, write to the Free Software Foundation, Inc., 51
# Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

from PyQt5 import QtWidgets
from PyQt5 import QtCore
from PyQt5.QtCore import Qt

from ubiquity.frontend.kde_components import qssutils

__all__ = ["Breadcrumb"]


# HACK! Breadcrumb should not have to inherit from QLabel! Inheriting from
# QFrame should be enough, but right now (Trusty) if I change Breadcrumb to
# inherit from QFrame then _mainLabel is not given enough vertical space and
# its text gets cropped at the bottom.
class Breadcrumb(QtWidgets.QLabel):
    TODO = 0
    CURRENT = 1
    DONE = 2

    def __init__(self, parent=None):
        super(Breadcrumb, self).__init__(parent)
        self.setProperty("isBreadcrumb", True)

        self._tickLabel = QtWidgets.QLabel()
        fm = self._tickLabel.fontMetrics()
        self._tickLabel.setFixedWidth(fm.width(" M "))
        self._tickLabel.setAlignment(Qt.AlignTop | Qt.AlignRight)

        self._mainLabel = QtWidgets.QLabel()
        self._mainLabel.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        self._mainLabel.setWordWrap(True)

        layout = QtWidgets.QHBoxLayout(self)
        layout.addWidget(self._tickLabel)
        layout.addWidget(self._mainLabel)

        self._state = None
        self.setState(Breadcrumb.TODO)

    def setState(self, state):
        if self._state == state:
            return
        self._state = state
        self._updateFromState()

    def setText(self, text):
        self._mainLabel.setText(text)

    def text(self):
        return self._mainLabel.text()

    def event(self, event):
        if event.type() == QtCore.QEvent.LayoutDirectionChange:
            self._updateFromState()
        return super(Breadcrumb, self).event(event)

    def _updateFromState(self):
        _initDicts()
        if QtWidgets.QApplication.isLeftToRight():
            tickDict = _TICK_DICT_LTR
            qssDict = _QSS_DICT_LTR
        else:
            tickDict = _TICK_DICT_RTL
            qssDict = _QSS_DICT_RTL
        self._tickLabel.setText(tickDict[self._state])
        self.setStyleSheet(qssDict[self._state])


_TICK_DICT_RTL = {}
_TICK_DICT_LTR = {}
_QSS_DICT_RTL = {}
_QSS_DICT_LTR = {}


def _initDicts():
    # Postpone initialization until we need them: reading and processing text
    # files at import time is rude.
    global _TICK_DICT_LTR, _TICK_DICT_RTL, _QSS_DICT_RTL, _QSS_DICT_LTR
    if _TICK_DICT_LTR:
        return
    _TICK_DICT_LTR = {
        Breadcrumb.TODO: "•",
        Breadcrumb.CURRENT: "▸",
        Breadcrumb.DONE: "✓",
    }

    _TICK_DICT_RTL = {
        Breadcrumb.TODO: "•",
        Breadcrumb.CURRENT: "◂",
        Breadcrumb.DONE: "✓",
    }

    _QSS_DICT_LTR = {
        Breadcrumb.TODO: "",
        Breadcrumb.CURRENT: qssutils.load("breadcrumb_current.qss", ltr=True),
        Breadcrumb.DONE: "",
    }

    _QSS_DICT_RTL = {
        Breadcrumb.TODO: "",
        Breadcrumb.CURRENT: qssutils.load("breadcrumb_current.qss", ltr=False),
        Breadcrumb.DONE: "",
    }
