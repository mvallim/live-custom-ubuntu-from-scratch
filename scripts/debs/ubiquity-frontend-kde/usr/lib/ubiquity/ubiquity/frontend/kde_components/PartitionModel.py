# -*- coding: utf-8; Mode: Python; indent-tabs-mode: nil; tab-width: 4 -*-

import os

from PyQt5 import QtCore

from ubiquity import i18n


def get_string(name, lang=None, prefix=None):
    """Get the string name in the given lang or a default."""
    if lang is None and 'LANG' in os.environ:
        lang = os.environ['LANG']
    return i18n.get_string(name, lang, prefix)


# describes the display for the manual partition view widget
class PartitionModel(QtCore.QAbstractItemModel):
    def __init__(self, ubiquity, parent=None):
        QtCore.QAbstractItemModel.__init__(self, parent)

        self.rootItem = None
        self.clear()

    def clear(self):
        self.beginResetModel()
        rootData = []
        rootData.append(QtCore.QVariant(get_string('partition_column_device')))
        rootData.append(QtCore.QVariant(get_string('partition_column_type')))
        rootData.append(QtCore.QVariant(
            get_string('partition_column_mountpoint')))
        rootData.append(QtCore.QVariant(get_string('partition_column_format')))
        rootData.append(QtCore.QVariant(get_string('partition_column_size')))
        rootData.append(QtCore.QVariant(get_string('partition_column_used')))
        self.rootItem = TreeItem(rootData)
        self.endResetModel()

    def append(self, data, ubiquity):
        row = self.rowCount(QtCore.QModelIndex())
        self.beginInsertRows(QtCore.QModelIndex(), row, row)
        self.rootItem.appendChild(TreeItem(data, ubiquity, self.rootItem))
        self.endInsertRows()

    def columnCount(self, parent):
        if parent.isValid():
            return parent.internalPointer().columnCount()
        else:
            return self.rootItem.columnCount()

    def data(self, index, role):
        if not index.isValid():
            return QtCore.QVariant()

        item = index.internalPointer()

        if role == QtCore.Qt.CheckStateRole and index.column() == 3:
            return QtCore.QVariant(item.data(index.column()))
        elif role == QtCore.Qt.DisplayRole and index.column() != 3:
            return QtCore.QVariant(item.data(index.column()))
        else:
            return QtCore.QVariant()

    def setData(self, index, value, role):
        item = index.internalPointer()
        if role == QtCore.Qt.CheckStateRole and index.column() == 3:
            item.partman_column_format_toggled(value)
        return True

    def flags(self, index):
        if not index.isValid():
            return QtCore.Qt.ItemIsEnabled

        # self.setData(
        #     index, QtCore.QVariant(QtCore.Qt.Checked),
        #     QtCore.Qt.CheckStateRole)
        # return QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable
        if index.column() == 3:
            item = index.internalPointer()
            if item.formatEnabled():
                return (QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable |
                        QtCore.Qt.ItemIsUserCheckable)
            else:
                return (QtCore.Qt.ItemIsSelectable |
                        QtCore.Qt.ItemIsUserCheckable)
        else:
            return QtCore.Qt.ItemIsEnabled | QtCore.Qt.ItemIsSelectable

    def headerData(self, section, orientation, role):
        if (orientation == QtCore.Qt.Horizontal and
                role == QtCore.Qt.DisplayRole):
            return self.rootItem.data(section)

        return QtCore.QVariant()

    def index(self, row, column, parent=QtCore.QModelIndex()):
        if not parent.isValid():
            parentItem = self.rootItem
        else:
            parentItem = parent.internalPointer()

        childItem = parentItem.child(row)
        if childItem:
            return self.createIndex(row, column, childItem)
        else:
            return QtCore.QModelIndex()

    def parent(self, index):
        if not index.isValid():
            return QtCore.QModelIndex()

        childItem = index.internalPointer()
        parentItem = childItem.parent()

        if parentItem == self.rootItem:
            return QtCore.QModelIndex()

        return self.createIndex(parentItem.row(), 0, parentItem)

    def rowCount(self, parent):
        if not parent.isValid():
            parentItem = self.rootItem
        else:
            parentItem = parent.internalPointer()

        return parentItem.childCount()

    def children(self):
        return self.rootItem.children()


class TreeItem:
    def __init__(self, data, controller=None, parent=None):
        self.parentItem = parent
        self.itemData = data
        self.childItems = []
        self.controller = controller
        if controller:
            self.dbfilter = controller.dbfilter
        else:
            self.dbfilter = None

    def appendChild(self, item):
        self.childItems.append(item)

    def child(self, row):
        return self.childItems[row]

    def childCount(self):
        return len(self.childItems)

    def children(self):
        return self.childItems

    def columnCount(self):
        if self.parentItem is None:
            return len(self.itemData)
        else:
            return 5

    def data(self, column):
        if self.parentItem is None:
            return QtCore.QVariant(self.itemData[column])
        elif column == 0:
            return QtCore.QVariant(self.partman_column_name())
        elif column == 1:
            return QtCore.QVariant(self.partman_column_type())
        elif column == 2:
            return QtCore.QVariant(self.partman_column_mountpoint())
        elif column == 3:
            return QtCore.QVariant(self.partman_column_format())
        elif column == 4:
            return QtCore.QVariant(self.partman_column_size())
        elif column == 5:
            return QtCore.QVariant(self.partman_column_used())
        else:
            return QtCore.QVariant("other")

    def parent(self):
        return self.parentItem

    def row(self):
        if self.parentItem:
            return self.parentItem.childItems.index(self)

        return 0

    def partman_column_name(self):
        partition = self.itemData[1]
        if 'id' not in partition:
            # whole disk
            return partition['device']
        elif partition['parted']['fs'] != 'free':
            return '  %s' % partition['parted']['path']
        elif partition['parted']['type'] == 'unusable':
            return '  %s' % get_string('partman/text/unusable')
        else:
            # partman uses "FREE SPACE" which feels a bit too SHOUTY for
            # this interface.
            return '  %s' % get_string('partition_free_space')

    def partman_column_type(self):
        partition = self.itemData[1]
        if 'id' not in partition or 'method' not in partition:
            if ('parted' in partition and
                    partition['parted']['fs'] != 'free' and
                    'detected_filesystem' in partition):
                return partition['detected_filesystem']
            else:
                return ''
        elif ('filesystem' in partition and
              partition['method'] in ('format', 'keep')):
            return partition['acting_filesystem']
        else:
            return partition['method']

    def partman_column_mountpoint(self):
        partition = self.itemData[1]
        if hasattr(self.dbfilter, 'get_current_mountpoint'):
            mountpoint = self.dbfilter.get_current_mountpoint(partition)
            if mountpoint is None:
                mountpoint = ''
        else:
            mountpoint = ''
        return mountpoint

    def partman_column_format(self):
        partition = self.itemData[1]
        if 'id' not in partition:
            return ''
        elif 'method' in partition:
            if partition['method'] == 'format':
                return QtCore.Qt.Checked
            else:
                return QtCore.Qt.Unchecked
        else:
            return QtCore.Qt.Unchecked  # FIXME should be enabled(False)

    def formatEnabled(self):
        """Is the format tickbox enabled?"""
        partition = self.itemData[1]
        return 'method' in partition and 'can_activate_format' in partition

    def partman_column_format_toggled(self, unused_value):
        if not self.controller.allowed_change_step():
            return
        if not hasattr(self.controller.dbfilter, 'edit_partition'):
            return
        devpart = self.itemData[0]
        partition = self.itemData[1]
        if 'id' not in partition or 'method' not in partition:
            return
        self.controller.allow_change_step(False)
        self.controller.dbfilter.edit_partition(devpart, fmt='dummy')

    def partman_column_size(self):
        partition = self.itemData[1]
        if 'id' not in partition:
            return ''
        else:
            # Yes, I know, 1000000 bytes is annoying. Sorry. This is what
            # partman expects.
            size_mb = int(partition['parted']['size']) // 1000000
            return '%d MB' % size_mb

    def partman_column_used(self):
        partition = self.itemData[1]
        if 'id' not in partition or partition['parted']['fs'] == 'free':
            return ''
        elif 'resize_min_size' not in partition:
            return get_string('partition_used_unknown')
        else:
            # Yes, I know, 1000000 bytes is annoying. Sorry. This is what
            # partman expects.
            size_mb = int(partition['resize_min_size']) // 1000000
            return '%d MB' % size_mb
