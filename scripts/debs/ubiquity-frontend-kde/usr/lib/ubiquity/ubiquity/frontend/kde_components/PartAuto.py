# -*- coding: utf-8 -*-

import os

from PyQt5 import uic
from PyQt5 import QtGui, QtWidgets

from ubiquity import i18n, misc
from ubiquity.frontend.kde_components.PartitionBar import PartitionsBar


_uidir = "/usr/share/ubiquity/qt/"


def get_string(name, lang=None, prefix=None):
    """Get the string name in the given lang or a default."""
    if lang is None and 'LANG' in os.environ:
        lang = os.environ['LANG']
    return i18n.get_string(name, lang, prefix)


def addBars(parent, before_bar, after_bar):
    frame = QtWidgets.QWidget(parent)
    frame.setLayout(QtWidgets.QVBoxLayout())
    frame.layout().setSpacing(0)

    frame.layout().addWidget(QtWidgets.QLabel(
        get_string('ubiquity/text/partition_layout_before')))
    frame.layout().addWidget(before_bar)
    frame.layout().addWidget(QtWidgets.QLabel(
        get_string('ubiquity/text/partition_layout_after')))
    frame.layout().addWidget(after_bar)

    parent.layout().addWidget(frame)
    return frame


class PartAuto(QtWidgets.QWidget):

    def __init__(self, controller):
        QtWidgets.QWidget.__init__(self)
        self.controller = controller

        uic.loadUi(os.path.join(_uidir, 'stepPartAuto.ui'), self)

        self.diskLayout = None

        self.autopartition_buttongroup = QtWidgets.QButtonGroup(self)
        self.autopartition_buttongroup.buttonClicked[int].connect(
            self.on_button_toggled)
        self.part_auto_disk_box.currentIndexChanged[int].connect(
            self.on_disks_combo_changed)

        self._clearInfo()

    def _clearInfo(self):
        self.bar_frames = []
        self.autopartitionTexts = []

        self.disks = []

        self.resizeSize = None
        self.resizeChoice = None
        self.manualChoice = None
        self.useDeviceChoice = None

    def setDiskLayout(self, diskLayout):
        self.diskLayout = diskLayout

    def setupChoices(self, choices, extra_options, resize_choice,
                     manual_choice, biggest_free_choice, use_device_choice,
                     lvm_choice, crypto_choice):
        self._clearInfo()

        self.resizeChoice = resize_choice
        self.manualChoice = manual_choice
        self.useDeviceChoice = use_device_choice
        self.extra_options = extra_options
        self.lvm_choice = lvm_choice
        self.crypto_choice = crypto_choice

        # remove any previous autopartition selections
        for child in self.autopart_selection_frame.children():
            if isinstance(child, QtWidgets.QWidget):
                child.setParent(None)
                del child

        for child in self.barsFrame.children():
            if isinstance(child, QtWidgets.QWidget):
                self.barsFrame.layout().removeWidget(child)
                child.setParent(None)
                del child

        release_name = misc.get_release().name

        bId = 0
        if 'resize' in extra_options and 'bitlocker' not in extra_options:
            button = QtWidgets.QRadioButton(
                self.resizeChoice, self.autopart_selection_frame)
            self.autopart_selection_frame.layout().addWidget(button)
            self.autopartition_buttongroup.addButton(button, bId)
            self.autopartitionTexts.append(resize_choice)
            button.clicked.connect(self.controller.setNextButtonTextInstallNow)
            bId += 1

            disks = []
            for disk_id in extra_options['resize']:
                # information about what can be resized
                _, min_size, max_size, pref_size, resize_path, _, _ = (
                    extra_options['resize'][disk_id])

                for text, path in extra_options['use_device'][1].items():
                    path = path[0]
                    if path.rsplit('/', 1)[1] == disk_id:
                        bar_frame = QtWidgets.QFrame()
                        bar_frame.setLayout(QtWidgets.QVBoxLayout())
                        bar_frame.setVisible(False)
                        bar_frame.layout().setSpacing(0)
                        self.barsFrame.layout().addWidget(bar_frame)
                        self.bar_frames.append(bar_frame)

                        disks.append((text, bar_frame))
                        self.resizeSize = pref_size
                        dev = self.diskLayout[disk_id]
                        before_bar = PartitionsBar()
                        after_bar = PartitionsBar()

                        for p in dev:
                            before_bar.addPartition(p[0], int(p[1]), p[3])
                            after_bar.addPartition(p[0], int(p[1]), p[3])

                        after_bar.setResizePartition(
                            resize_path, min_size, max_size, pref_size,
                            release_name)
                        after_bar.partitionResized.connect(
                            self.on_partitionResized)
                        addBars(bar_frame, before_bar, after_bar)
            self.disks.append(disks)

        # TODO biggest_free_choice

        # Use entire disk.
        button = QtWidgets.QRadioButton(
            self.useDeviceChoice, self.autopart_selection_frame)
        self.autopartitionTexts.append(self.useDeviceChoice)
        self.autopart_selection_frame.layout().addWidget(button)
        self.autopartition_buttongroup.addButton(button, bId)
        button.clicked.connect(self.controller.setNextButtonTextInstallNow)
        bId += 1

        disks = []
        for text, path in extra_options['use_device'][1].items():
            path = path[0]
            bar_frame = QtWidgets.QFrame()
            bar_frame.setLayout(QtWidgets.QVBoxLayout())
            bar_frame.setVisible(False)
            bar_frame.layout().setSpacing(0)
            self.barsFrame.layout().addWidget(bar_frame)
            self.bar_frames.append(bar_frame)

            disks.append((text, bar_frame))

            dev = self.diskLayout[path.rsplit('/', 1)[1]]
            before_bar = PartitionsBar(controller=self.controller)
            after_bar = PartitionsBar(controller=self.controller)

            for p in dev:
                before_bar.addPartition(p.device, int(p.size), p.filesystem)
            if before_bar.diskSize > 0:
                after_bar.addPartition(
                    '', before_bar.diskSize, 'auto', name=release_name)
            else:
                after_bar.addPartition('', 1, 'auto', name=release_name)

            addBars(bar_frame, before_bar, after_bar)
        self.disks.append(disks)

        # LVM
        button = QtWidgets.QRadioButton(
            self.lvm_choice, self.autopart_selection_frame)
        self.autopartitionTexts.append(self.lvm_choice)
        self.autopart_selection_frame.layout().addWidget(button)
        self.autopartition_buttongroup.addButton(button, bId)
        button.clicked.connect(self.controller.setNextButtonTextInstallNow)
        bId += 1
        # add use entire disk options to combobox again
        self.disks.append(disks)

        # Crypto
        button = QtWidgets.QRadioButton(
            self.crypto_choice, self.autopart_selection_frame)
        self.autopartitionTexts.append(self.crypto_choice)
        self.autopart_selection_frame.layout().addWidget(button)
        self.autopartition_buttongroup.addButton(button, bId)
        button.clicked.connect(self.controller.setNextButtonTextInstallNow)
        self.crypto_button_id = bId
        bId += 1
        # add use entire disk options to combobox again
        self.disks.append(disks)

        box = QtWidgets.QHBoxLayout()
        box.addStretch()
        self.autopart_selection_frame.layout().addLayout(box)

        self.passwordIcon = QtWidgets.QLabel()
        self.passwordIcon.setPixmap(QtGui.QPixmap(
            "/usr/share/icons/oxygen/16x16/status/dialog-password.png"))
        box.addWidget(self.passwordIcon)
        self.password = QtWidgets.QLineEdit()
        self.password.setEchoMode(QtWidgets.QLineEdit.Password)
        self.password.textChanged.connect(self.verify_password)
        box.addWidget(self.password)
        self.verified_password = QtWidgets.QLineEdit()
        self.verified_password.setEchoMode(QtWidgets.QLineEdit.Password)
        self.verified_password.textChanged.connect(self.verify_password)
        box.addWidget(self.verified_password)
        self.show_password = QtWidgets.QToolButton()
        self.show_password.setIcon(QtGui.QIcon.fromTheme("password-show-off"))
        self.show_password.setCheckable(True)
        self.show_password.toggled.connect(self.on_show_password)
        box.addWidget(self.show_password)
        self.badPassword = QtWidgets.QLabel()
        self.badPassword.setPixmap(QtGui.QPixmap(
            "/usr/share/icons/oxygen/16x16/status/dialog-warning.png"))
        self.badPassword.hide()
        box.addWidget(self.badPassword)

        # Manual partitioning.

        button = QtWidgets.QRadioButton(
            manual_choice, self.autopart_selection_frame)
        self.autopartitionTexts.append(manual_choice)
        self.autopart_selection_frame.layout().addWidget(button)
        self.autopartition_buttongroup.addButton(button, bId)
        button.clicked.connect(self.controller.setNextButtonTextNext)
        self.disks.append([])

        # select the first button
        b = self.autopartition_buttongroup.button(0)
        b and b.click()

    def on_show_password(self, state):
        modes = (QtWidgets.QLineEdit.Password, QtWidgets.QLineEdit.Normal)
        icons = ("password-show-off", "password-show-on")
        self.password.setEchoMode(modes[state])
        self.verified_password.setEchoMode(modes[state])
        self.show_password.setIcon(QtGui.QIcon.fromTheme(icons[state]))

    # slot for when partition is resized on the bar
    def on_partitionResized(self, unused, size):
        self.resizeSize = size

    def getChoice(self):
        bId = self.autopartition_buttongroup.checkedId()
        if bId > -1:
            choice = str(self.autopartitionTexts[bId])
        else:
            raise AssertionError("no active autopartitioning choice")

        if choice == self.resizeChoice:
            # resize choice should have been hidden otherwise
            assert self.resizeSize is not None
            comboText = str(self.part_auto_disk_box.currentText())
            disk_id = self.extra_options['use_device'][1][comboText][0]
            disk_id = disk_id.rsplit('/', 1)[1]
            option = self.extra_options['resize'][disk_id][0]
            return option, '%d B' % self.resizeSize, 'resize_use_free'
        elif choice == self.useDeviceChoice:
            return (self.extra_options['use_device'][0],
                    str(self.part_auto_disk_box.currentText()), 'use_device')
        elif choice == self.lvm_choice:
            return (choice,
                    str(self.part_auto_disk_box.currentText()), 'use_lvm')
        elif choice == self.crypto_choice:
            return (choice,
                    str(self.part_auto_disk_box.currentText()), 'use_crypto')
        elif choice == self.manualChoice:
            return choice, None, 'manual'
        else:
            return choice, None, 'unknown'

    def on_disks_combo_changed(self, index):
        for e in self.bar_frames:
            e.setVisible(False)
        button_id = self.autopartition_buttongroup.checkedId()
        length = len(self.disks[button_id])
        if index < length and length > 0:
            self.disks[button_id][index][1].setVisible(True)

    def on_button_toggled(self, unused):
        button_id = self.autopartition_buttongroup.checkedId()
        self.part_auto_disk_box.clear()
        if not [self.part_auto_disk_box.addItem(disk[0])
                for disk in self.disks[button_id]]:
            self.part_auto_disk_box.hide()
        else:
            # If we haven't added any items to the disk combobox, hide it.
            self.part_auto_disk_box.show()
        # enable the crypto password fields
        if button_id == self.crypto_button_id:
            self.passwordIcon.setEnabled(True)
            self.password.setEnabled(True)
            self.verified_password.setEnabled(True)
            self.badPassword.setEnabled(True)
            self.verify_password()
        else:
            self.passwordIcon.setEnabled(False)
            self.password.setEnabled(False)
            self.verified_password.setEnabled(False)
            self.badPassword.setEnabled(False)
            self.controller.allow_go_forward(True)

    # show warning if passwords do not match
    def verify_password(self):
        complete = False

        if self.password.text() == self.verified_password.text():
            self.badPassword.hide()
            complete = True
        else:
            self.badPassword.show()

        if not self.password.text():
            complete = False

        self.controller.allow_go_forward(complete)
