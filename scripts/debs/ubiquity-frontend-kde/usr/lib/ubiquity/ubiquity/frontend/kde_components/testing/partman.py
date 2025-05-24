# -*- coding: utf-8 -*-

import os
import sys

from PyQt5 import QtWidgets

from ubiquity.frontend.kde_components.PartMan import PartMan


if __name__ == "__main__":

    app = QtWidgets.QApplication(sys.argv)
    app.setStyle("Oxygen")

    PartMan._uidir = '../../../../gui/qt'

    styleFile = os.path.join(PartMan._uidir, "style.qss")
    with open(styleFile, 'r') as sf:
        app.setStyleSheet(sf.read())

    win = PartMan(None)
    win.setObjectName("widgetStack")
    win.show()

    cache_order = [
        '/var/lib/partman/devices/=dev=sda//',
        '/var/lib/partman/devices/=dev=sda//32256-8167703039',
        '/var/lib/partman/devices/=dev=sda//8167735296-8587192319',
        '/var/lib/partman/devices/=dev=sdb//',
        '/var/lib/partman/devices/=dev=sdb//32256-5074997759',
        '/var/lib/partman/devices/=dev=sdb//5075030016-5362882559',
        '/var/lib/partman/devices/=dev=sdc//',
        '/var/lib/partman/devices/=dev=sdc//32256-5074997759',
        '/var/lib/partman/devices/=dev=sdc//5075030016-5362882559',
    ]

    def tree_device(dev, part_id=None):
        prefix = '60partition_tree__________/var/lib/partman/devices/=dev='
        if part_id is None:
            return prefix + dev + '//'
        else:
            return prefix + dev + '//' + part_id

    disk_cache = {
        '/var/lib/partman/devices/=dev=sda//': {
            'dev': '=dev=sda',
            'device': '/dev/sda',
            'display': tree_device('sda'),
            'label': ['msdos'],
        },
        '/var/lib/partman/devices/=dev=sdb//': {
            'dev': '=dev=sdb',
            'device': '/dev/sdb',
            'display': tree_device('sdb'),
            'label': ['msdos'],
        },
        '/var/lib/partman/devices/=dev=sdc//': {
            'dev': '=dev=sdc',
            'device': '/dev/sdc',
            'display': tree_device('sdc'),
            'label': ['msdos'],
        },
    }

    partition_cache = {
        '/var/lib/partman/devices/=dev=sda//32256-8167703039': {
            'can_resize': True,
            'detected_filesystem': 'ext4',
            'dev': '=dev=sda',
            'display': tree_device('sda', '32256-8167703039'),
            'id': '32256-8167703039',
            'method_choices': [
                ('25filesystem', 'ext4', 'Ext4 journaling file system'),
                ('25filesystem', 'ext3', 'Ext3 journaling file system'),
                ('25filesystem', 'ext2', 'Ext2 file system'),
                ('25filesystem', 'btrfs', 'btrfs journaling file system'),
                ('25filesystem', 'jfs', 'JFS journaling file system'),
                ('25filesystem', 'xfs', 'XFS journaling file system'),
                ('25filesystem', 'fat16', 'FAT16 file system'),
                ('25filesystem', 'fat32', 'FAT32 file system'),
                ('40swap', 'swap', 'swap area'),
                ('70dont_use', 'dontuse', 'do not use the partition'),
            ],
            'parent': '/dev/sda',
            'parted': {
                'fs': 'ext4',
                'id': '32256-8167703039',
                'name': '',
                'num': '1',
                'path': '/dev/sda1',
                'size': '8167670784',
                'type': 'primary',
            },
            'resize_max_size': 8167670784,
            'resize_min_size': 2758852608,
            'resize_pref_size': 8167670784,
        },
        '/var/lib/partman/devices/=dev=sda//8167735296-8587192319': {
            'can_resize': True,
            'detected_filesystem': 'linux-swap',
            'dev': '=dev=sda',
            'display': tree_device('sda', '8167735296-8587192319'),
            'id': '8167735296-8587192319',
            'method': 'swap',
            'method_choices': [
                ('25filesystem', 'ext4', 'Ext4 journaling file system'),
                ('25filesystem', 'ext3', 'Ext3 journaling file system'),
                ('25filesystem', 'ext2', 'Ext2 file system'),
                ('25filesystem', 'btrfs', 'btrfs journaling file system'),
                ('25filesystem', 'jfs', 'JFS journaling file system'),
                ('25filesystem', 'xfs', 'XFS journaling file system'),
                ('25filesystem', 'fat16', 'FAT16 file system'),
                ('25filesystem', 'fat32', 'FAT32 file system'),
                ('40swap', 'swap', 'swap area'),
                ('70dont_use', 'dontuse', 'do not use the partition'),
            ],
            'parent': '/dev/sda',
            'parted': {
                'fs': 'linux-swap',
                'id': '8167735296-8587192319',
                'name': '',
                'num': '5',
                'path': '/dev/sda5',
                'size': '419457024',
                'type': 'logical',
            },
            'resize_max_size': 419457024,
            'resize_min_size': 4096,
            'resize_pref_size': 419457024,
        },
        '/var/lib/partman/devices/=dev=sdb//32256-5074997759': {
            'can_resize': True,
            'detected_filesystem': 'ext4',
            'dev': '=dev=sdb',
            'display': tree_device('sdb', '32256-5074997759'),
            'id': '32256-5074997759',
            'method_choices': [
                ('25filesystem', 'ext4', 'Ext4 journaling file system'),
                ('25filesystem', 'ext3', 'Ext3 journaling file system'),
                ('25filesystem', 'ext2', 'Ext2 file system'),
                ('25filesystem', 'btrfs', 'btrfs journaling file system'),
                ('25filesystem', 'jfs', 'JFS journaling file system'),
                ('25filesystem', 'xfs', 'XFS journaling file system'),
                ('25filesystem', 'fat16', 'FAT16 file system'),
                ('25filesystem', 'fat32', 'FAT32 file system'),
                ('40swap', 'swap', 'swap area'),
                ('70dont_use', 'dontuse', 'do not use the partition'),
            ],
            'parent': '/dev/sdb',
            'parted': {
                'fs': 'ext4',
                'id': '32256-5074997759',
                'name': '',
                'num': '1',
                'path': '/dev/sdb1',
                'size': '5074965504',
                'type': 'primary',
            },
            'resize_max_size': 5074965504,
            'resize_min_size': 223924224,
            'resize_pref_size': 5074965504,
        },
        '/var/lib/partman/devices/=dev=sdb//5075030016-5362882559': {
            'can_resize': True,
            'detected_filesystem': 'linux-swap',
            'dev': '=dev=sdb',
            'display': tree_device('sdb', '5075030016-5362882559'),
            'id': '5075030016-5362882559',
            'method': 'swap',
            'method_choices': [
                ('25filesystem', 'ext4', 'Ext4 journaling file system'),
                ('25filesystem', 'ext3', 'Ext3 journaling file system'),
                ('25filesystem', 'ext2', 'Ext2 file system'),
                ('25filesystem', 'btrfs', 'btrfs journaling file system'),
                ('25filesystem', 'jfs', 'JFS journaling file system'),
                ('25filesystem', 'xfs', 'XFS journaling file system'),
                ('25filesystem', 'fat16', 'FAT16 file system'),
                ('25filesystem', 'fat32', 'FAT32 file system'),
                ('40swap', 'swap', 'swap area'),
                ('70dont_use', 'dontuse', 'do not use the partition'),
            ],
            'parent': '/dev/sdb',
            'parted': {
                'fs': 'linux-swap',
                'id': '5075030016-5362882559',
                'name': '',
                'num': '5',
                'path': '/dev/sdb5',
                'size': '287852544',
                'type': 'logical',
            },
            'resize_max_size': 287852544,
            'resize_min_size': 4096,
            'resize_pref_size': 287852544,
        },
        '/var/lib/partman/devices/=dev=sdc//32256-5074997759': {
            'can_resize': True,
            'detected_filesystem': 'ext4',
            'dev': '=dev=sdc',
            'display': tree_device('sdc', '32256-5074997759'),
            'id': '32256-5074997759',
            'method_choices': [
                ('25filesystem', 'ext4', 'Ext4 journaling file system'),
                ('25filesystem', 'ext3', 'Ext3 journaling file system'),
                ('25filesystem', 'ext2', 'Ext2 file system'),
                ('25filesystem', 'btrfs', 'btrfs journaling file system'),
                ('25filesystem', 'jfs', 'JFS journaling file system'),
                ('25filesystem', 'xfs', 'XFS journaling file system'),
                ('25filesystem', 'fat16', 'FAT16 file system'),
                ('25filesystem', 'fat32', 'FAT32 file system'),
                ('40swap', 'swap', 'swap area'),
                ('70dont_use', 'dontuse', 'do not use the partition'),
            ],
            'parent': '/dev/sdc',
            'parted': {
                'fs': 'ext4',
                'id': '32256-5074997759',
                'name': '',
                'num': '1',
                'path': '/dev/sdc1',
                'size': '5074965504',
                'type': 'primary',
            },
            'resize_max_size': 5074965504,
            'resize_min_size': 223928320,
            'resize_pref_size': 5074965504,
        },
        '/var/lib/partman/devices/=dev=sdc//5075030016-5362882559': {
            'can_resize': True,
            'detected_filesystem': 'linux-swap',
            'dev': '=dev=sdc',
            'display': tree_device('sdc', '5075030016-5362882559'),
            'id': '5075030016-5362882559',
            'method': 'swap',
            'method_choices': [
                ('25filesystem', 'ext4', 'Ext4 journaling file system'),
                ('25filesystem', 'ext3', 'Ext3 journaling file system'),
                ('25filesystem', 'ext2', 'Ext2 file system'),
                ('25filesystem', 'btrfs', 'btrfs journaling file system'),
                ('25filesystem', 'jfs', 'JFS journaling file system'),
                ('25filesystem', 'xfs', 'XFS journaling file system'),
                ('25filesystem', 'fat16', 'FAT16 file system'),
                ('25filesystem', 'fat32', 'FAT32 file system'),
                ('40swap', 'swap', 'swap area'),
                ('70dont_use', 'dontuse', 'do not use the partition'),
            ],
            'parent': '/dev/sdc',
            'parted': {
                'fs': 'linux-swap',
                'id': '5075030016-5362882559',
                'name': '',
                'num': '5',
                'path': '/dev/sdc5',
                'size': '287852544',
                'type': 'logical',
            },
            'resize_max_size': 287852544,
            'resize_min_size': 4096,
            'resize_pref_size': 287852544,
        },
    }

    win.update(disk_cache, partition_cache, cache_order)
    win.update(disk_cache, partition_cache, cache_order)

    sys.exit(app.exec_())
