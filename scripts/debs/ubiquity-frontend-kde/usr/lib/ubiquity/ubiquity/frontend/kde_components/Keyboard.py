# -*- coding: utf-8 -*-

import subprocess
import sys

from PyQt5.QtCore import Qt, QRectF
from PyQt5.QtGui import QFont, QPainter, QPen, QPainterPath, QColor
from PyQt5.QtWidgets import QWidget

IMG_DIR = "/usr/share/ubiquity/qt/images"


#U+ , or +U+ ... to string
def fromUnicodeString(raw):
    if raw[0:2] == "U+":
        return chr(int(raw[2:], 16))
    elif raw[0:2] == "+U":
        return chr(int(raw[3:], 16))

    return ""


class Keyboard(QWidget):

    kb_104 = {
        "extended_return": False,
        "keys": [
        (0x29, 0x2, 0x3, 0x4, 0x5, 0x6, 0x7, 0x8, 0x9, 0xa, 0xb, 0xc, 0xd),
        (0x10, 0x11, 0x12, 0x13, 0x14, 0x15, 0x16, 0x17, 0x18, 0x19, 0x1a,
         0x1b, 0x2b),
        (0x1e, 0x1f, 0x20, 0x21, 0x22, 0x23, 0x24, 0x25, 0x26, 0x27, 0x28),
        (0x2c, 0x2d, 0x2e, 0x2f, 0x30, 0x31, 0x32, 0x33, 0x34, 0x35),
        ()]
    }

    kb_105 = {
        "extended_return": True,
        "keys": [
        (0x29, 0x2, 0x3, 0x4, 0x5, 0x6, 0x7, 0x8, 0x9, 0xa, 0xb, 0xc, 0xd),
        (0x10, 0x11, 0x12, 0x13, 0x14, 0x15, 0x16, 0x17, 0x18, 0x19, 0x1a,
         0x1b),
        (0x1e, 0x1f, 0x20, 0x21, 0x22, 0x23, 0x24, 0x25, 0x26, 0x27, 0x28,
         0x2b),
        (0x54, 0x2c, 0x2d, 0x2e, 0x2f, 0x30, 0x31, 0x32, 0x33, 0x34, 0x35),
        ()]
    }

    kb_106 = {
        "extended_return": True,
        "keys": [
        (0x29, 0x2, 0x3, 0x4, 0x5, 0x6, 0x7, 0x8, 0x9, 0xa, 0xb, 0xc, 0xd,
         0xe),
        (0x10, 0x11, 0x12, 0x13, 0x14, 0x15, 0x16, 0x17, 0x18, 0x19, 0x1a,
         0x1b),
        (0x1e, 0x1f, 0x20, 0x21, 0x22, 0x23, 0x24, 0x25, 0x26, 0x27, 0x28,
         0x29),
        (0x2c, 0x2d, 0x2e, 0x2f, 0x30, 0x31, 0x32, 0x33, 0x34, 0x35, 0x36),
        ()]
    }

    lowerFont = QFont("Helvetica", 10, QFont.DemiBold)
    upperFont = QFont("Helvetica", 8)

    def __init__(self, parent=None):
        QWidget.__init__(self, parent)
        self.codes = []

        self.layout = "us"
        self.variant = ""

        self.kb = None

    def setLayout(self, layout):
        self.layout = layout

    def setVariant(self, variant):
        self.variant = variant
        self.loadCodes()
        self.loadInfo()
        self.repaint()

    def loadInfo(self):
        kbl_104 = ["us", "th"]
        kbl_106 = ["jp"]

        # most keyboards are 105 key so default to that
        if self.layout in kbl_104:
            self.kb = self.kb_104
        elif self.layout in kbl_106:
            self.kb = self.kb_106
        elif self.kb != self.kb_105:
            self.kb = self.kb_105

    def resizeEvent(self, re):
        self.space = 6
        self.usable_width = self.width() - 2
        self.key_w = (self.usable_width - 14 * self.space) // 15

        self.setMinimumHeight(self.key_w * 4 + self.space * 5)

    def paintEvent(self, pe):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)

        pen = QPen()
        pen.setWidth(1)
        pen.setColor(QColor(0x8c, 0xa3, 0xb0))
        p.setPen(pen)

        p.setBrush(QColor(0xe4, 0xec, 0xf4))

        rx = 6

        space = self.space
        w = self.usable_width
        kw = self.key_w

        def drawRow(row, sx, sy, last_end=False):
            x = sx
            y = sy
            keys = row
            rw = w - sx
            i = 0
            for k in keys:
                rect = QRectF(x, y, kw, kw)

                if i == len(keys) - 1 and last_end:
                    rect.setWidth(rw)

                p.drawRoundedRect(rect, rx, rx)
                p.setPen(Qt.black)

                rect.adjust(5, 1, 0, 0)

                p.setFont(self.lowerFont)
                p.drawText(
                    rect, Qt.AlignLeft | Qt.AlignBottom, self.regular_text(k))

                p.setFont(self.upperFont)
                p.drawText(
                    rect, Qt.AlignLeft | Qt.AlignTop, self.shift_text(k))

                rw = rw - space - kw
                x = x + space + kw
                i = i + 1

                p.setPen(pen)
            return (x, rw)

        x = .5
        y = .5

        keys = self.kb["keys"]
        ext_return = self.kb["extended_return"]

        first_key_w = 0

        rows = 4
        remaining_x = [0, 0, 0, 0]
        remaining_widths = [0, 0, 0, 0]

        for i in range(0, rows):
            if first_key_w > 0:
                first_key_w = first_key_w * 1.375

                if self.kb == self.kb_105 and i == 3:
                    first_key_w = kw * 1.275

                rect = QRectF(x, y, first_key_w, kw)
                p.drawRoundedRect(rect, rx, rx)
                x = x + first_key_w + space
            else:
                first_key_w = kw

            x, rw = drawRow(keys[i], x, y, i == 1 and not ext_return)

            remaining_x[i] = x
            remaining_widths[i] = rw

            if i != 1 and i != 2:
                rect = QRectF(x, y, rw, kw)
                p.drawRoundedRect(rect, rx, rx)

            x = .5
            y = y + space + kw

        if ext_return:
            rx = rx * 2
            x1 = remaining_x[1]
            y1 = .5 + kw * 1 + space * 1
            w1 = remaining_widths[1]
            x2 = remaining_x[2]
            y2 = .5 + kw * 2 + space * 2

            # this is some serious crap... but it has to be so
            # maybe one day keyboards won't look like this...
            # one can only hope
            pp = QPainterPath()
            pp.moveTo(x1, y1 + rx)
            pp.arcTo(x1, y1, rx, rx, 180, -90)
            pp.lineTo(x1 + w1 - rx, y1)
            pp.arcTo(x1 + w1 - rx, y1, rx, rx, 90, -90)
            pp.lineTo(x1 + w1, y2 + kw - rx)
            pp.arcTo(x1 + w1 - rx, y2 + kw - rx, rx, rx, 0, -90)
            pp.lineTo(x2 + rx, y2 + kw)
            pp.arcTo(x2, y2 + kw - rx, rx, rx, -90, -90)
            pp.lineTo(x2, y1 + kw)
            pp.lineTo(x1 + rx, y1 + kw)
            pp.arcTo(x1, y1 + kw - rx, rx, rx, -90, -90)
            pp.closeSubpath()

            p.drawPath(pp)
        else:
            x = remaining_x[2]
            y = .5 + kw * 2 + space * 2
            rect = QRectF(x, y, remaining_widths[2], kw)
            p.drawRoundedRect(rect, rx, rx)

        QWidget.paintEvent(self, pe)

    def regular_text(self, index):
        return self.codes[index - 1][0]

    def shift_text(self, index):
        return self.codes[index - 1][1]

    def ctrl_text(self, index):
        return self.codes[index - 1][2]

    def alt_text(self, index):
        return self.codes[index - 1][3]

    def loadCodes(self):
        if self.layout is None:
            return

        variantParam = ""
        if self.variant:
            variantParam = "-variant %s" % self.variant

        cmd = "ckbcomp -model pc106 -layout %s %s -compact" % (
            self.layout, variantParam)
        # print(cmd)

        pipe = subprocess.Popen(
            cmd, shell=True, stdout=subprocess.PIPE, stderr=None,
            universal_newlines=True)
        cfile = pipe.communicate()[0]

        # clear the current codes
        del self.codes[:]

        for l in cfile.split('\n'):
            if l[:7] != "keycode":
                continue

            codes = l.split('=')[1].strip().split(' ')

            plain = fromUnicodeString(codes[0])
            shift = fromUnicodeString(codes[1])
            ctrl = fromUnicodeString(codes[2])
            alt = fromUnicodeString(codes[3])

            if ctrl == plain:
                ctrl = ""

            if alt == plain:
                alt = ""

            self.codes.append((plain, shift, ctrl, alt))


## testing
if __name__ == "__main__":
    from PyQt5.QtWidgets import QApplication, QVBoxLayout

    IMG_DIR = "../../../gui/qt/images"

    app = QApplication(sys.argv)

    win = QWidget()
    l = QVBoxLayout(win)

    def addKb(layout, variant=""):
        kb1 = Keyboard()
        kb1.setLayout(layout)
        kb1.setVariant(variant)
        l.addWidget(kb1)

    addKb("us")
    addKb("gb")
    addKb("th")
    addKb("gr")
    addKb("jp")

    win.show()

    app.exec_()
