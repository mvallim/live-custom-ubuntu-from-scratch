# -*- coding: utf-8 -*-

import os
import sys

from PyQt5 import QtWidgets

from ubiquity.frontend.kde_components.PartAuto import PartAuto


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)

    PartAuto._uidir = '../../../../gui/qt'

    styleFile = os.path.join(PartAuto._uidir, "style.qss")
    with open(styleFile, 'r') as sf:
        app.setStyleSheet(sf.read())

    win = PartAuto()
    win.setObjectName("widgetStack")
    win.show()

    diskLayout = {
        '=dev=sda': [
            ('/dev/sda1', 8167670784, '32256-8167703039', "ext3"),
            ('/dev/sda5', 419457024, '8167735296-8587192319', "ext3"),
        ],
        '=dev=sdb': [
            ('/dev/sdb1', 5074965504, '32256-5074997759', "free"),
            ('/dev/sdb5', 287852544, '5075030016-5362882559', "ext3"),
        ],
        '=dev=sdc': [
            ('/dev/sdc1', 5074965504, '32256-5074997759', "ntfs"),
            ('/dev/sdc5', 287852544, '5075030016-5362882559', "free"),
        ],
    }

    # call functions twice to test returning to the page
    # make sure things are cleared properly
    win.setDiskLayout(diskLayout)
    win.setDiskLayout(diskLayout)

    biggest_free_choice = 'Use the largest continuous free space',
    choices = ['Install them side by side, choosing between them each startup',
               'Erase and use the entire disk',
               'Specify partitions manually (advanced)']

    extra_options = {
        'Erase and use the entire disk': [
            'SCSI1 (0,0,0) (sda) - 8.6 GB ATA VBOX HARDDISK',
            'SCSI1 (0,1,0) (sdb) - 5.4 GB ATA VBOX HARDDISK',
            'SCSI2 (0,1,0) (sdc) - 5.4 GB ATA VBOX HARDDISK',
        ],
        'Install them side by side, choosing between them each startup': (
            2757079040, 5485413376, 4121246208, '/dev/sda1'),
        'Use the largest continuous free space': [],
    }

    manual_choice = 'Specify partitions manually (advanced)'
    resize_choice = (
        'Install them side by side, choosing between them each startup')

    win.setupChoices(choices, extra_options, resize_choice, manual_choice,
                     biggest_free_choice)

    win.setupChoices(choices, extra_options, resize_choice, manual_choice,
                     biggest_free_choice)

    print(win.getChoice())

    sys.exit(app.exec_())
