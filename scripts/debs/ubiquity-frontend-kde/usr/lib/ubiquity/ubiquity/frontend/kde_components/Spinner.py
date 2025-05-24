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

from PyQt5 import QtCore, QtGui, QtWidgets


class Spinner(QtWidgets.QLabel):
    """
    Home-made spinner widget, because we can't use kdelibs classes
    """
    def __init__(self, parent=None):
        QtWidgets.QLabel.__init__(self, parent)
        size = 22
        self.setFixedSize(size, size)

        # XXX: pixmap() needs specification of the size of the pixmap to be
        # exported and, per documentation, the resulting returned pixmap will
        # have dimentions smaller or equal (but never bigger) to those values.
        # Since this pixmap is a set of images we don't want to hard-code
        # the number of frames (as this comes from an external theme), so to
        # make sure we fit all of them we select some big number as the
        # height.
        pixmap = QtGui.QIcon.fromTheme('process-working').pixmap(size, 512)
        self.pixes = []
        for y in range(0, pixmap.height(), size):
            pix = pixmap.copy(0, y, size, size)
            self.pixes.append(pix)
        self.idx = 0
        self.setPixmap(self.pixes[0])

        self.timer = QtCore.QTimer(self)
        self.timer.setInterval(150)
        self.timer.setSingleShot(False)
        self.timer.timeout.connect(self._showNextFrame)

    def setRunning(self, running):
        if running:
            self.timer.start()
        else:
            self.timer.stop()

    def _showNextFrame(self):
        self.idx = (self.idx + 1) % len(self.pixes)
        self.setPixmap(self.pixes[self.idx])
