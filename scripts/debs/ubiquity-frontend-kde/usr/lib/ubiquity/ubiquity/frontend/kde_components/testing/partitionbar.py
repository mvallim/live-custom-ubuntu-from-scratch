# -*- coding: utf-8 -*-

import sys

from PyQt5 import QtWidgets

from ubiquity.frontend.kde_components.PartitionBar import PartitionsBar


if __name__ == "__main__":
    app = QtWidgets.QApplication(sys.argv)
    QtWidgets.QApplication.setStyle("Oxygen")

    wid = QtWidgets.QWidget()
    layout = QtWidgets.QVBoxLayout(wid)

    pb1 = PartitionsBar(wid)
    layout.addWidget(pb1)

    pb1.addPartition('/dev/sdb1', 57511125504, 'ext4')
    pb1.addPartition('/dev/sdb5', 2500452864, 'linux-swap')
    pb1.setResizePartition(
        '/dev/sdb1', 230989824, 55143440896, 52143440896, 'distro')

    pb2 = PartitionsBar(wid)
    layout.addWidget(pb2)

    pb2.addPartition("/dev/sdb1", 5000, "linux-swap")
    pb2.addPartition("/dev/sdb2", 20000, "ext3")
    pb2.addPartition("/dev/sdb3", 30000, "fat32")
    pb2.addPartition("/dev/sdb4", 50000, "ntfs")
    pb2.setResizePartition('/dev/sdb2', 5000, 15000, 20000, 'Kubuntu')

    pb2 = PartitionsBar(wid)
    layout.addWidget(pb2)

    pb2.addPartition('/dev/sdb1', 4005679104, 'ext4')
    pb2.addPartition('/dev/sdb-1', 53505446400, 'free')
    pb2.addPartition('/dev/sdb5', 2500452864, 'linux-swap')

    wid.show()

    sys.exit(app.exec_())
