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

import string
import syslog

from PyQt5 import QtCore
from PyQt5 import QtGui, QtWidgets

from ubiquity import nm
from ubiquity.nm import QueuedCaller, NetworkStore, NetworkManager
from ubiquity.frontend.kde_components.Spinner import Spinner

ICON_SIZE = 22


class QtQueuedCaller(QueuedCaller):
    def __init__(self, *args):
        QueuedCaller.__init__(self, *args)
        self.timer = QtCore.QTimer()
        self.timer.setSingleShot(True)
        self.timer.setInterval(self.timeout)
        self.timer.timeout.connect(self.callback)

    def start(self):
        self.timer.start()


def is_passphrase_valid(passphrase):
    if not passphrase:
        return False
    if len(passphrase) >= 8 and len(passphrase) < 64:
        return True
    if len(passphrase) > 64:
        return False

    for c in passphrase:
        if c not in string.hexdigits:
            return False
    return True


# Our wireless icons are unreadable over a white background, so...
# let's generate them.
def draw_level_pix(wanted_level):
    pix = QtGui.QPixmap(ICON_SIZE, ICON_SIZE)
    pix.fill(QtCore.Qt.transparent)
    painter = QtGui.QPainter(pix)
    color = QtWidgets.QApplication.palette().color(QtGui.QPalette.Text)
    painter.translate(0, -2)
    painter.setPen(QtGui.QPen(color, 2))
    painter.setRenderHint(QtGui.QPainter.Antialiasing)

    right = pix.width()
    bottom = pix.height()
    middle = bottom // 2 + 1

    center = QtCore.QPointF(right / 2., bottom - 1)
    for level in range(4):
        radius = 1 + level * 4
        if level <= wanted_level - 1:
            painter.setOpacity(0.8)
        else:
            painter.setOpacity(0.3)
        painter.drawEllipse(center, radius, radius)

    painter.setCompositionMode(QtGui.QPainter.CompositionMode_Clear)
    painter.setBrush(QtCore.Qt.black)
    painter.drawPolygon(QtGui.QPolygon(
        [QtCore.QPoint(int(center.x()), bottom),
         QtCore.QPoint(0, middle),
         QtCore.QPoint(0, bottom)]))
    painter.drawPolygon(QtGui.QPolygon(
        [QtCore.QPoint(int(center.x()), bottom),
         QtCore.QPoint(right, middle),
         QtCore.QPoint(right, bottom)]))
    painter.translate(0, 2)
    painter.drawRect(0, pix.height() - 2, pix.width(), 2)
    painter.end()
    return pix


class QtNetworkStore(QtGui.QStandardItemModel, NetworkStore):
    IsSecureRole = QtCore.Qt.UserRole + 1
    StrengthRole = QtCore.Qt.UserRole + 2
    SsidRole = QtCore.Qt.UserRole + 3

    def __init__(self, parent=None):
        QtGui.QStandardItemModel.__init__(self, parent)
        self._init_icons()

    def get_device_ids(self):
        return [self.item(x).id for x in range(self.rowCount())]

    def add_device(self, devid, vendor, model):
        item = QtGui.QStandardItem("%s %s" % (vendor, model))
        item.setIcon(QtGui.QIcon.fromTheme("network-wireless"))
        item.setSelectable(False)
        # devid is a dbus.ObjectPath, so we can't store it as a QVariant using
        # setData().
        # That's why we keep it as item attribute.
        item.id = devid
        self.appendRow(item)

    def has_device(self, devid):
        return self._item_for_device(devid) is not None

    def remove_devices_not_in(self, devids):
        self._remove_rows_not_in(None, devids)

    def add_ap(self, devid, ssid, secure, strength):
        dev_item = self._item_for_device(devid)
        assert dev_item
        item = QtGui.QStandardItem(str(ssid))
        item.id = ssid
        item.setData(secure, self.IsSecureRole)
        item.setData(strength, self.StrengthRole)
        item.setData(ssid, self.SsidRole)
        self._update_item_icon(item)
        dev_item.appendRow(item)

    def has_ap(self, devid, ssid):
        return self._item_for_ap(devid, ssid) is not None

    def set_ap_strength(self, devid, ssid, strength):
        item = self._item_for_ap(devid, ssid)
        assert item
        item.setData(self.StrengthRole, strength)
        self._update_item_icon(item)

    def remove_aps_not_in(self, devid, ssids):
        dev_item = self._item_for_device(devid)
        if not dev_item:
            return
        self._remove_rows_not_in(dev_item, ssids)

    def _remove_rows_not_in(self, parent_item, ids):
        row = 0
        if parent_item is None:
            parent_item = self.invisibleRootItem()

        while row < parent_item.rowCount():
            if parent_item.child(row).id in ids:
                row += 1
            else:
                parent_item.removeRow(row)

    def _item_for_device(self, devid):
        for row in range(self.rowCount()):
            item = self.item(row)
            if item.id == devid:
                return item
        return None

    def _item_for_ap(self, devid, ssid):
        dev_item = self._item_for_device(devid)
        if not dev_item:
            return None
        for row in range(dev_item.rowCount()):
            item = dev_item.child(row)
            if item.id == ssid:
                return item
        return None

    def _update_item_icon(self, item):
        secure = item.data(QtNetworkStore.IsSecureRole)
        strength = item.data(QtNetworkStore.StrengthRole)
        if strength < 30:
            icon = 0
        elif strength < 50:
            icon = 1
        elif strength < 70:
            icon = 2
        elif strength < 90:
            icon = 3
        else:
            icon = 4
        if secure:
            icon += 5
        item.setIcon(self._icons[icon])

    def _init_icons(self):
        pixes = []
        for level in range(5):
            pixes.append(draw_level_pix(level))

        secure_icon = QtGui.QIcon.fromTheme("emblem-locked")
        secure_pix = secure_icon.pixmap(ICON_SIZE // 2, ICON_SIZE // 2)
        for level in range(5):
            pix2 = QtGui.QPixmap(pixes[level])
            painter = QtGui.QPainter(pix2)
            painter.drawPixmap(ICON_SIZE - secure_pix.width(),
                               ICON_SIZE - secure_pix.height(),
                               secure_pix)
            painter.end()
            pixes.append(pix2)

        self._icons = [QtGui.QIcon(x) for x in pixes]


class NetworkManagerTreeView(QtWidgets.QTreeView):
    def __init__(self, state_changed=None):
        QtWidgets.QTreeView.__init__(self)
        model = QtNetworkStore(self)

        self.wifi_model = NetworkManager(model, QtQueuedCaller, state_changed)
        self.setModel(model)
        self.setHeaderHidden(True)
        self.setIconSize(QtCore.QSize(ICON_SIZE, ICON_SIZE))

    def rowsInserted(self, parent, start, end):
        QtWidgets.QTreeView.rowsInserted(self, parent, start, end)
        if not parent.isValid():
            return
        self.setExpanded(parent, True)

    def showEvent(self, event):
        QtWidgets.QTreeView.showEvent(self, event)
        for row in range(self.model().rowCount()):
            index = self.model().index(row, 0)
            self.setExpanded(index, True)

    def is_row_an_ap(self):
        index = self.currentIndex()
        if not index.isValid():
            return False
        return index.parent().isValid()

    def _get_selected_row_ids(self):
        """
        For device rows, returns (devid, None)
        For AP rows, returns (devid, ssid)
        """
        index = self.currentIndex()
        parent_index = index.parent()
        if not parent_index.isValid():
            # device row
            devid = self.model().itemFromIndex(parent_index).id
            return devid, None

        # AP row
        ssid = index.data(QtNetworkStore.SsidRole)
        devid = self.model().itemFromIndex(parent_index).id

        return devid, ssid

    def connect_to_selection(self, passphrase):
        devid, ssid = self._get_selected_row_ids()
        try:
            self.wifi_model.connect_to_ap(devid, ssid, passphrase)
        except Exception as e:
            dialog = QtWidgets.QMessageBox()
            dialog.setWindowTitle("Failed to connect to wireless network")
            dialog.setText("{}".format(e))
            dialog.exec_()

    def get_cached_passphrase(self):
        index = self.currentIndex()
        secure = index.data(QtNetworkStore.IsSecureRole)
        if not secure:
            return ''
        ssid = index.data(QtNetworkStore.SsidRole)
        return self.wifi_model.passphrases_cache.get(ssid, '')

    def is_row_a_secure_ap(self):
        current = self.currentIndex()
        if not current.parent().isValid():
            return False
        return current.data(QtNetworkStore.IsSecureRole)

    def get_state(self):
        return self.wifi_model.get_state()


class ProgressIndicator(QtWidgets.QWidget):
    def __init__(self, parent=None):
        QtWidgets.QWidget.__init__(self, parent)

        self.iconLabel = QtWidgets.QLabel()

        self.label = QtWidgets.QLabel()

        self.spinner = Spinner()

        layout = QtWidgets.QHBoxLayout(self)
        layout.addStretch()
        layout.addWidget(self.spinner)
        layout.addWidget(self.iconLabel)
        layout.addWidget(self.label)
        layout.addStretch()

        self.setSpinnerVisible(False)

    def setIcon(self, icon):
        if icon:
            pix = icon.pixmap(ICON_SIZE)
            self.iconLabel.setPixmap(pix)
            self.iconLabel.show()
        else:
            self.iconLabel.hide()

    def setText(self, text):
        self.label.setText(text)

    def setSpinnerVisible(self, visible):
        self.spinner.setVisible(visible)
        self.spinner.setRunning(visible)


class NetworkManagerWidget(QtWidgets.QWidget):
    state_changed = QtCore.pyqtSignal(int)

    def __init__(self, parent=None):
        QtWidgets.QWidget.__init__(self, parent)
        self.tr_dict = {
            'wireless_password_label': 'Password:',
            'wireless_display_password': 'Display Password',
            'connect': 'Connect',
            'connecting_label': 'Connecting...',
            'connection_failed_label': 'Connection failed.',
            'connected_label': 'Connected.',
        }

        self.password_entry = QtWidgets.QLineEdit()
        self.password_entry.textChanged.connect(self._update_ui)

        self.password_label = QtWidgets.QLabel()
        self.password_label.setBuddy(self.password_entry)

        self.display_password = QtWidgets.QCheckBox()
        self.display_password.toggled.connect(self._update_password_entry)

        self.connect_button = QtWidgets.QPushButton()
        self.connect_button.clicked.connect(self._connect_to_ap)
        self.password_entry.returnPressed.connect(
            self.connect_button.animateClick)

        self.progress_indicator = ProgressIndicator()
        self.progress_indicator.hide()

        hlayout = QtWidgets.QHBoxLayout()
        hlayout.addWidget(self.password_label)
        hlayout.addWidget(self.password_entry)
        hlayout.addWidget(self.display_password)
        hlayout.addWidget(self.connect_button)

        self.view = NetworkManagerTreeView(self._on_state_changed)
        self.view.selectionModel().currentChanged.connect(
            self._on_current_changed)

        layout = QtWidgets.QVBoxLayout(self)
        layout.addWidget(self.view)
        layout.addWidget(self.progress_indicator)
        layout.addLayout(hlayout)

        self.nm_state = self.view.get_state()
        self._update_password_entry()
        self._update_ui()

    def _update_password_entry(self):
        if self.display_password.isChecked():
            self.password_entry.setEchoMode(QtWidgets.QLineEdit.Normal)
        else:
            self.password_entry.setEchoMode(QtWidgets.QLineEdit.Password)

    def get_state(self):
        return self.nm_state

    def get_translation_keys(self):
        return self.tr_dict.keys()

    def translate(self, dct):
        self.tr_dict.update(dct)
        self.password_label.setText(
            self.tr_dict['wireless_password_label'])
        self.display_password.setText(
            self.tr_dict['wireless_display_password'])
        self.connect_button.setText(
            self.tr_dict['connect'])

    def _on_state_changed(self, state):
        old_state = self.nm_state
        self.nm_state = state

        try:
            if state == nm.NM_STATE_CONNECTING:
                self.progress_indicator.setText(
                    self.tr_dict['connecting_label'])
                self.progress_indicator.show()
                self.progress_indicator.setIcon(None)
                self.progress_indicator.setSpinnerVisible(True)
                return

            if state == nm.NM_STATE_DISCONNECTED \
                    and old_state == nm.NM_STATE_CONNECTING:
                self.progress_indicator.setText(
                    self.tr_dict['connection_failed_label'])
                self.progress_indicator.show()
                self.progress_indicator.setIcon(
                    QtGui.QIcon.fromTheme('dialog-error'))
                self.progress_indicator.setSpinnerVisible(False)
                return

            if state == nm.NM_STATE_CONNECTED_GLOBAL:
                self.progress_indicator.setText(
                    self.tr_dict['connected_label'])
                self.progress_indicator.show()
                self.progress_indicator.setIcon(
                    QtGui.QIcon.fromTheme('dialog-ok-apply'))
                self.progress_indicator.setSpinnerVisible(False)
                return

            syslog.syslog('NetworkManagerWidget._on_state_changed:'
                          ' unhandled combination of nm states'
                          ' old_state={} state={}'.format(old_state, state))
        finally:
            self.state_changed.emit(state)

    def _connect_to_ap(self):
        passphrase = self.password_entry.text()
        self.view.connect_to_selection(passphrase)

    def _on_current_changed(self):
        if not self.view.is_row_an_ap():
            return
        passphrase = self.view.get_cached_passphrase()
        self.password_entry.setText(passphrase)
        self._update_ui()

    def _update_ui(self):
        if not self.view.is_row_an_ap():
            self._set_secure_widgets_enabled(False)
            self.connect_button.setEnabled(False)
            return

        secure = self.view.is_row_a_secure_ap()
        self._set_secure_widgets_enabled(secure)
        if secure:
            passphrase = self.password_entry.text()
            self.connect_button.setEnabled(
                len(passphrase) > 0 and is_passphrase_valid(passphrase))
        else:
            self.connect_button.setEnabled(True)

    def _set_secure_widgets_enabled(self, enabled):
        for widget in (self.password_label,
                       self.password_entry,
                       self.display_password):
            widget.setEnabled(enabled)
        if not enabled:
            self.password_entry.setText('')


def main():
    import sys
    from PyQt5.QtWidgets import QApplication

    from dbus.mainloop.glib import DBusGMainLoop
    DBusGMainLoop(set_as_default=True)

    def on_state_changed(state):
        print('on_state_changed: state={}'.format(state))

    app = QApplication(sys.argv)
    QtGui.QIcon.setThemeName("oxygen")
    nm = NetworkManagerWidget()
    nm.translate({})
    nm.state_changed.connect(on_state_changed)
    nm.show()
    app.exec_()


if __name__ == '__main__':
    main()
