# -*- coding: utf-8 -*-

import os

from PyQt5 import uic
from PyQt5 import QtWidgets

from ubiquity.frontend.kde_components.PartitionBar import PartitionsBar
from ubiquity.frontend.kde_components.PartitionModel import PartitionModel

_uidir = "/usr/share/ubiquity/qt/"

# FIXME: Taken from ubi-partman, needs to be moved somewhere.
PARTITION_TYPE_PRIMARY = 0
PARTITION_TYPE_LOGICAL = 1

PARTITION_PLACE_BEGINNING = 0
PARTITION_PLACE_END = 1


class PartMan(QtWidgets.QWidget):

    def __init__(self, controller):
        QtWidgets.QWidget.__init__(self)
        self.ctrlr = controller

        self.edit_use_method_names = {}
        self.create_dialog = None
        self.edit_dialog = None

        # currently visible partition bar
        self.active_bar = None

        uic.loadUi(os.path.join(_uidir, 'stepPartMan.ui'), self)
        self.part_advanced_warning_hbox.setVisible(False)
        self.part_advanced_bootloader_frame.setVisible(False)

        self.partition_tree_model = PartitionModel(
            self.ctrlr, self.partition_list_treeview)
        self.partition_list_treeview.setModel(self.partition_tree_model)
        self.partition_list_treeview.selectionModel().selectionChanged.connect(
            self.on_treeviewSelectionChanged)
        self.partition_button_new_label.clicked[bool].connect(
            self.on_new_table_clicked)

        self.partition_button_new.clicked[bool].connect(self.on_new_clicked)
        self.partition_button_edit.clicked[bool].connect(self.on_edit_clicked)
        self.partition_button_delete.clicked[bool].connect(
            self.on_delete_clicked)
        self.undo_everything.clicked[bool].connect(self.on_undo_clicked)

    def update(self, disk_cache, partition_cache, cache_order):
        self.partition_tree_model.clear()

        for child in self.part_advanced_bar_frame.children():
            if isinstance(child, QtWidgets.QWidget):
                child.setParent(None)
                del child

        self.active_bar = None
        partition_bar = None
        indexCount = -1
        for item in cache_order:
            if item in disk_cache:
                # the item is a disk
                indexCount += 1
                partition_bar = PartitionsBar(
                    self.part_advanced_bar_frame,
                    controller=self.ctrlr)
                self.part_advanced_bar_frame.layout().addWidget(partition_bar)

                # hide all the other bars at first
                if self.active_bar:
                    partition_bar.setVisible(False)
                else:
                    self.active_bar = partition_bar

                self.partition_tree_model.append(
                    [item, disk_cache[item], partition_bar], self.ctrlr)
            else:
                # the item is a partition, add it to the current bar
                partition = partition_cache[item]

                # add the new partition to our tree display
                self.partition_tree_model.append(
                    [item, partition, partition_bar], self.ctrlr)
                indexCount += 1

                # data for bar display
                size = int(partition['parted']['size'])
                fs = partition['parted']['fs']
                path = partition['parted']['path']
                partition_bar.addPartition(path, size, fs)

        self.partition_list_treeview.reset()

    def on_treeviewSelectionChanged(self, unused, deselected):

        # by default disable editing the partition
        self.partition_button_new_label.setEnabled(False)
        self.partition_button_new.setEnabled(False)
        self.partition_button_edit.setEnabled(False)
        self.partition_button_delete.setEnabled(False)
        self.undo_everything.setEnabled(False)

        if self.active_bar:
            self.active_bar.setVisible(False)

        indexes = self.partition_list_treeview.selectedIndexes()
        if indexes:
            index = indexes[0]

            item = index.internalPointer()
            devpart = item.itemData[0]
            partition = item.itemData[1]

            self.active_bar = item.itemData[2]
            if self.active_bar:
                self.active_bar.setVisible(True)
        else:
            devpart = None
            partition = None

        if not self.ctrlr:
            return

        for action in self.ctrlr.dbfilter.get_actions(devpart, partition):
            if action == 'new_label':
                self.partition_button_new_label.setEnabled(True)
            elif action == 'new':
                self.partition_button_new.setEnabled(True)
            elif action == 'edit':
                self.partition_button_edit.setEnabled(True)
            elif action == 'delete':
                self.partition_button_delete.setEnabled(True)

        self.undo_everything.setEnabled(True)

    def partman_create_dialog(self, devpart, partition):
        if not self.ctrlr.allowed_change_step():
            return

        # lazy initialization
        dialog = self.create_dialog
        if not dialog:
            self.create_dialog = QtWidgets.QDialog(self)
            dialog = self.create_dialog
            uic.loadUi("%s/partition_create_dialog.ui" % _uidir, dialog)
            dialog.partition_create_use_combo.currentIndexChanged[int].connect(
                self.on_partition_create_use_combo_changed)

            self.ctrlr._wizard.translate_widget_children(dialog)

        # TODO cjwatson 2006-11-01: Because partman doesn't use a question
        # group for these, we have to figure out in advance whether each
        # question is going to be asked.

        if partition['parted']['type'] == 'pri/log':
            # Is there already a primary partition?
            for child in self.partition_tree_model.children():
                data = child.itemData
                otherpart = data[1]
                if (otherpart['dev'] == partition['dev'] and
                        'id' in otherpart and
                        otherpart['parted']['type'] == 'primary'):
                    dialog.partition_create_type_logical.setChecked(True)
                    break
            else:
                dialog.partition_create_type_primary.setChecked(True)
        else:
            dialog.partition_create_type_label.hide()
            dialog.partition_create_type_widget.hide()
        # Yes, I know, 1000000 bytes is annoying. Sorry. This is what
        # partman expects.
        max_size_mb = int(partition['parted']['size']) // 1000000
        dialog.partition_create_size_spinbutton.setMaximum(max_size_mb)
        dialog.partition_create_size_spinbutton.setValue(max_size_mb)

        dialog.partition_create_place_beginning.setChecked(True)

        self.create_use_method_names = {}

        # Remove any previous entries
        dialog.partition_create_use_combo.clear()

        for method, name, description in (
                self.ctrlr.dbfilter.use_as(devpart, True)):
            self.create_use_method_names[description] = name
            dialog.partition_create_use_combo.addItem(description)
        if dialog.partition_create_use_combo.count() == 0:
            dialog.partition_create_use_combo.setEnabled(False)

        dialog.partition_create_mount_combo.clear()
        for mp, choice_c, choice in (
                self.ctrlr.dbfilter.default_mountpoint_choices()):
            # FIXME gtk frontend has a nifty way of showing the user readable
            # 'choice' text in the drop down, but only selecting the 'mp' text
            dialog.partition_create_mount_combo.addItem(mp)
        dialog.partition_create_mount_combo.clearEditText()

        if dialog.exec_() == QtWidgets.QDialog.Accepted:
            if partition['parted']['type'] == 'primary':
                prilog = PARTITION_TYPE_PRIMARY
            elif partition['parted']['type'] == 'logical':
                prilog = PARTITION_TYPE_LOGICAL
            elif partition['parted']['type'] == 'pri/log':
                if dialog.partition_create_type_primary.isChecked():
                    prilog = PARTITION_TYPE_PRIMARY
                else:
                    prilog = PARTITION_TYPE_LOGICAL

            if dialog.partition_create_place_beginning.isChecked():
                place = PARTITION_PLACE_BEGINNING
            else:
                place = PARTITION_PLACE_END

            method_description = str(
                dialog.partition_create_use_combo.currentText())
            method = self.create_use_method_names[method_description]

            mountpoint = str(dialog.partition_create_mount_combo.currentText())

            self.ctrlr.allow_change_step(False)
            self.ctrlr.dbfilter.create_partition(
                devpart,
                str(dialog.partition_create_size_spinbutton.value()),
                prilog, place, method, mountpoint)

    def on_partition_create_use_combo_changed(self, *args):
        if not hasattr(self, 'create_use_method_names'):
            return
        known_filesystems = ('ext4', 'ext3', 'ext2',
                             'btrfs', 'jfs', 'xfs',
                             'fat16', 'fat32', 'ntfs', 'uboot')
        text = str(self.create_dialog.partition_create_use_combo.currentText())
        if text not in self.create_use_method_names:
            return

        method = self.create_use_method_names[text]
        if method not in known_filesystems:
            self.create_dialog.partition_create_mount_combo.clearEditText()
            self.create_dialog.partition_create_mount_combo.setEnabled(False)
        else:
            self.create_dialog.partition_create_mount_combo.setEnabled(True)
            self.create_dialog.partition_create_mount_combo.clear()
            for mp, choice_c, choice in \
                    self.ctrlr.dbfilter.default_mountpoint_choices(method):
                self.create_dialog.partition_create_mount_combo.addItem(mp)

    def partman_edit_dialog(self, devpart, partition):
        if not self.ctrlr.allowed_change_step():
            return

        # lazy loading
        dialog = self.edit_dialog
        if not dialog:
            self.edit_dialog = QtWidgets.QDialog(self)
            dialog = self.edit_dialog
            uic.loadUi("%s/partition_edit_dialog.ui" % _uidir, dialog)
            dialog.partition_edit_use_combo.currentIndexChanged[int].connect(
                self.on_partition_edit_use_combo_changed)

            self.ctrlr._wizard.translate_widget_children(dialog)

        current_size = None
        if ('can_resize' not in partition or not partition['can_resize'] or
                'resize_min_size' not in partition or
                'resize_max_size' not in partition):
            dialog.partition_edit_size_label.hide()
            dialog.partition_edit_size_spinbutton.hide()
        else:
            # Yes, I know, 1000000 bytes is annoying. Sorry. This is what
            # partman expects.
            min_size_mb = int(partition['resize_min_size']) // 1000000
            cur_size_mb = int(partition['parted']['size']) // 1000000
            max_size_mb = int(partition['resize_max_size']) // 1000000
            # Bad things happen if the current size is out of bounds.
            min_size_mb = min(min_size_mb, cur_size_mb)
            max_size_mb = max(cur_size_mb, max_size_mb)
            dialog.partition_edit_size_spinbutton.setMinimum(min_size_mb)
            dialog.partition_edit_size_spinbutton.setMaximum(max_size_mb)
            dialog.partition_edit_size_spinbutton.setSingleStep(1)
            dialog.partition_edit_size_spinbutton.setValue(cur_size_mb)

            current_size = str(dialog.partition_edit_size_spinbutton.value())

        self.edit_use_method_names = {}
        method_descriptions = {}
        dialog.partition_edit_use_combo.clear()
        for script, arg, option in partition['method_choices']:
            self.edit_use_method_names[option] = arg
            method_descriptions[arg] = option
            dialog.partition_edit_use_combo.addItem(option)

        current_method = self.ctrlr.dbfilter.get_current_method(partition)
        if current_method and current_method in method_descriptions:
            current_method_description = method_descriptions[current_method]
            index = dialog.partition_edit_use_combo.findText(
                current_method_description)
            dialog.partition_edit_use_combo.setCurrentIndex(index)

        if 'id' not in partition:
            dialog.partition_edit_format_label.hide()
            dialog.partition_edit_format_checkbutton.hide()
            current_format = False
        elif 'method' in partition:
            dialog.partition_edit_format_label.show()
            dialog.partition_edit_format_checkbutton.show()
            dialog.partition_edit_format_checkbutton.setEnabled(
                'can_activate_format' in partition)
            current_format = (partition['method'] == 'format')
        else:
            dialog.partition_edit_format_label.show()
            dialog.partition_edit_format_checkbutton.show()
            dialog.partition_edit_format_checkbutton.setEnabled(False)
            current_format = False
        dialog.partition_edit_format_checkbutton.setChecked(current_format)

        dialog.partition_edit_mount_combo.clear()
        if 'mountpoint_choices' in partition:
            for mp, choice_c, choice in partition['mountpoint_choices']:
                # FIXME gtk frontend has a nifty way of showing the user
                # readable 'choice' text in the drop down, but only
                # selecting the 'mp' text
                dialog.partition_edit_mount_combo.addItem(mp)
        current_mountpoint = self.ctrlr.dbfilter.get_current_mountpoint(
            partition)
        if current_mountpoint is not None:
            index = dialog.partition_edit_mount_combo.findText(current_method)
            if index != -1:
                dialog.partition_edit_mount_combo.setCurrentIndex(index)
            else:
                dialog.partition_edit_mount_combo.addItem(current_mountpoint)
                dialog.partition_edit_mount_combo.setCurrentIndex(
                    dialog.partition_edit_mount_combo.count() - 1)

        if (dialog.exec_() == QtWidgets.QDialog.Accepted):
            size = None
            if current_size is not None:
                size = str(dialog.partition_edit_size_spinbutton.value())

            method_description = str(
                dialog.partition_edit_use_combo.currentText())
            method = self.edit_use_method_names[method_description]

            fmt = dialog.partition_edit_format_checkbutton.isChecked()

            mountpoint = str(dialog.partition_edit_mount_combo.currentText())

            if (current_size is not None and size is not None and
                    current_size == size):
                size = None
            if method == current_method:
                method = None
            if fmt == current_format:
                fmt = None
            if mountpoint == current_mountpoint:
                mountpoint = None

            if (size is not None or method is not None or fmt is not None or
                    mountpoint is not None):
                self.ctrlr.allow_change_step(False)
                edits = {'size': size, 'method': method,
                         'mountpoint': mountpoint}
                if fmt is not None:
                    edits['fmt'] = 'dummy'
                self.ctrlr.dbfilter.edit_partition(devpart, **edits)

    def on_partition_edit_use_combo_changed(self, *args):
        if not hasattr(self, 'edit_use_method_names'):
            return
        # If the selected method isn't a filesystem, then selecting a mount
        # point makes no sense. TODO cjwatson 2007-01-31: Unfortunately we
        # have to hardcode the list of known filesystems here.
        known_filesystems = ('ext4', 'ext3', 'ext2',
                             'btrfs', 'jfs', 'xfs',
                             'fat16', 'fat32', 'ntfs', 'uboot')
        text = str(self.edit_dialog.partition_edit_use_combo.currentText())
        if text not in self.edit_use_method_names:
            return
        method = self.edit_use_method_names[text]

        if method not in known_filesystems:
            self.edit_dialog.partition_edit_mount_combo.clearEditText()
            self.edit_dialog.partition_edit_mount_combo.setEnabled(False)
            self.edit_dialog.partition_edit_format_checkbutton.setEnabled(
                False)
        else:
            self.edit_dialog.partition_edit_mount_combo.setEnabled(True)
            self.edit_dialog.partition_edit_format_checkbutton.setEnabled(True)
            self.edit_dialog.partition_edit_mount_combo.clear()
            for mp, choice_c, choice in \
                    self.ctrlr.dbfilter.default_mountpoint_choices(method):
                self.edit_dialog.partition_edit_mount_combo.addItem(mp)

    def on_partition_list_treeview_activated(self, index):
        """ activated when partition line clicked """
        if not self.ctrlr.allowed_change_step():
            return

        item = index.internalPointer()
        devpart = item.itemData[0]
        partition = item.itemData[1]

        if 'id' not in partition:
            # Are there already partitions on this disk? If so, don't allow
            # activating the row to offer to create a new partition table,
            # to avoid mishaps.
            for child in self.partition_tree_model.children():
                data = child.itemData
                otherpart = data[1]
                if otherpart['dev'] == partition['dev'] and 'id' in otherpart:
                    break
            else:
                self.ctrlr.allow_change_step(False)
                self.ctrlr.dbfilter.create_label(devpart)
        elif partition['parted']['fs'] == 'free':
            if 'can_new' in partition and partition['can_new']:
                self.partman_create_dialog(devpart, partition)

    # actions for clicking the buttons

    def get_treeview_data(self):
        selected = self.partition_list_treeview.selectedIndexes()
        if not selected:
            return (None, None)
        index = selected[0]
        item = index.internalPointer()
        devpart = item.itemData[0]
        partition = item.itemData[1]

        return (devpart, partition)

    def on_new_table_clicked(self):
        if not self.ctrlr.allowed_change_step():
            return
        devpart, partition = self.get_treeview_data()
        if not devpart or not partition:
            return
        self.ctrlr.allow_change_step(False)
        self.ctrlr.dbfilter.create_label(devpart)

    def on_new_clicked(self):
        devpart, partition = self.get_treeview_data()
        if not devpart or not partition:
            return
        self.partman_create_dialog(devpart, partition)

    def on_edit_clicked(self):
        devpart, partition = self.get_treeview_data()
        if not devpart or not partition:
            return
        self.partman_edit_dialog(devpart, partition)

    def on_delete_clicked(self):
        if not self.ctrlr.allowed_change_step():
            return
        devpart, partition = self.get_treeview_data()
        if not devpart or not partition:
            return
        self.ctrlr.allow_change_step(False)
        self.ctrlr.dbfilter.delete_partition(devpart)

    def on_undo_clicked(self):
        if not self.ctrlr.allowed_change_step():
            return
        self.ctrlr.allow_change_step(False)
        self.ctrlr.dbfilter.undo()

    def setGrubOptions(self, options, default, grub_installable):
        self.part_advanced_bootloader_frame.setVisible(True)
        self.grub_device_entry.clear()
        for opt in options:
            path = opt[0]
            if grub_installable.get(path, False):
                self.grub_device_entry.addItem(path)

        index = self.grub_device_entry.findText(default)
        if (index == -1):
            self.grub_device_entry.addItem(default)
            index = self.grub_device_entry.count() - 1
            # select the target device
        self.grub_device_entry.setCurrentIndex(index)

    def getGrubChoice(self):
        return str(self.grub_device_entry.currentText())
