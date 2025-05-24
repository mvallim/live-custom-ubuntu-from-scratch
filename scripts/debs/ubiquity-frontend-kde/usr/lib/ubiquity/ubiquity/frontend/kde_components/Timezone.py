# -*- coding: utf-8; Mode: Python; indent-tabs-mode: nil; tab-width: 4 -*-

import datetime
import math

from PyQt5 import QtCore, QtGui, QtWidgets

import ubiquity.tz


class City:
    """Contains information about a geographical timezone city."""

    def __init__(self, loc, pixmap):
        self.loc = loc
        self.pixmap = pixmap


class TimezoneMap(QtWidgets.QWidget):

    zoneChanged = QtCore.pyqtSignal(object, object)

    def __init__(self, parent):
        QtWidgets.QWidget.__init__(self, parent)
        # currently active city
        self.selected_city = None
        self.selected_zone = None
        # dictionary of full name (ie. 'Australia/Sydney') -> city
        self.cities = {}
        self.setObjectName("timezone_map")

        # load background pixmap
        self.imagePath = "/usr/share/ubiquity/pixmaps/timezone"
        self.pixmap = QtGui.QPixmap("%s/bg.png" % self.imagePath)
        self.setMinimumSize(self.pixmap.size() / 2)
        self.setMaximumSize(self.pixmap.size())
        policy = QtWidgets.QSizePolicy(
            QtWidgets.QSizePolicy.Preferred,
            QtWidgets.QSizePolicy.Preferred)
        policy.setHeightForWidth(True)
        self.setSizePolicy(policy)

        # redraw timer for selected city time
        self.timer = QtCore.QTimer(self)
        self.timer.timeout.connect(self.update)
        self.timer.start(1000)

        # load the pixmaps for the zone overlays
        zones = [
            '0.0', '1.0', '2.0', '3.0', '3.5', '4.0', '4.5', '5.0', '5.5',
            '5.75', '6.0', '6.5', '7.0', '8.0', '8.5', '9.0', '9.5', '10.0',
            '10.5', '11.0', '11.5', '12.0', '12.75', '13.0', '-1.0', '-2.0',
            '-3.0', '-3.5', '-4.0', '-4.5', '-5.0', '-5.5', '-6.0', '-7.0',
            '-8.0', '-9.0', '-9.5', '-10.0', '-11.0',
        ]

        zonePixmaps = {}

        for zone in zones:
            # print('%s/timezone_%s.png' % (self.imagePath, zone))
            zonePixmaps[zone] = QtGui.QPixmap(
                '%s/timezone_%s.png' % (self.imagePath, zone))

        # load the timezones from database
        self.tzdb = ubiquity.tz.Database()
        for location in self.tzdb.locations:
            zone_bits = location.zone.split('/')

            if len(zone_bits) == 1:
                continue

            # zone is the hours offset from 0
            zoneHour = (location.raw_utc_offset.seconds / 3600.0 +
                        location.raw_utc_offset.days * 24)

            # wrap around
            if zoneHour > 13.0:
                zoneHour -= 24.0

            # set the pixamp to show for the city
            zoneS = str(zoneHour)

            # try to find the closest zone
            if zoneS not in zonePixmaps:
                zoneS = None
                for offset in (.25, -.25, .5, -.5):
                    zstring = str(zoneHour + offset)
                    if zstring in zonePixmaps:
                        zoneS = zstring
                        break

            pixmap = zoneS and zonePixmaps[zoneS]

            # make new city
            self.cities[location.zone] = City(location, pixmap)

    # taken from gtk side
    def longitudeToX(self, longitude):
        # Miller cylindrical map projection is just the longitude as the
        # calculation is the longitude from the central meridian of the
        # projection.  Convert to radians.
        x = (longitude * (math.pi / 180)) + math.pi  # 0 ... 2pi
        # Convert to a percentage.
        x = x / (2 * math.pi)
        x = x * self.width()
        # Adjust for the visible map starting near 170 degrees.
        # Percentage shift required, grabbed from measurements using The GIMP.
        x = x - (self.width() * 0.039073402)
        return x

    def latitudeToY(self, latitude):
        # Miller cylindrical map projection, as used in the source map from
        # the CIA world factbook.  Convert latitude to radians.
        y = 1.25 * math.log(math.tan(
            (0.25 * math.pi) + (0.4 * (latitude * (math.pi / 180)))))
        # Convert to a percentage.
        y = abs(y - 2.30341254338)  # 0 ... 4.606825
        y = y / 4.6068250867599998
        # Adjust for the visible map not including anything beyond 60
        # degrees south (150 degrees vs 180 degrees).
        y = y * (self.height() * 1.2)
        return y

    def sizeHint(self):
        return self.pixmap.size()

    def heightForWidth(self, w):
        size = self.pixmap.size()
        if w > size.width():
            w = size.width()
        return w * size.height() // size.width()

    def paintEvent(self, unused_paintEvent):
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)

        path = QtGui.QPainterPath()
        path.addRoundedRect(QtCore.QRectF(self.rect()), 5, 5)
        painter.setClipPath(path)

        painter.drawPixmap(self.rect(), self.pixmap)

        if self.selected_city is not None:
            c = self.selected_city
            cpos = self.getPosition(c.loc.latitude, c.loc.longitude)

            if (c.pixmap):
                painter.drawPixmap(self.rect(), c.pixmap)

            painter.setBrush(QtGui.QColor(30, 30, 30, 200))
            painter.setPen(QtCore.Qt.white)

            # mark the location with a dot
            painter.drawEllipse(cpos, 3, 3)

            # paint the time instead of the name
            try:
                now = datetime.datetime.now(
                    ubiquity.tz.SystemTzInfo(c.loc.zone))
                timestring = now.strftime('%X')

                start = cpos + QtCore.QPoint(3, -3)
                margin = 2

                # correct the text render position if text will render off
                # widget
                text_size = painter.fontMetrics().size(
                    QtCore.Qt.TextSingleLine, timestring)
                text_size += QtCore.QSize(margin * 2, margin * 2)

                rect = QtCore.QRect(
                    start, start + QtCore.QPoint(
                        text_size.width(), -text_size.height()))

                # check bounds of the time display
                if rect.top() < 0:
                    rect.moveTop(start.y() + 3)
                if rect.right() > self.width():
                    rect.moveRight(start.x() - 3)

                painter.setPen(QtCore.Qt.NoPen)
                painter.drawRoundedRect(rect, 3, 3)
                painter.setPen(QtCore.Qt.white)
                painter.drawText(rect, QtCore.Qt.AlignCenter, timestring)

            except (ValueError, OverflowError):
                # Some versions of Python have problems with clocks set
                # before the epoch (http://python.org/sf/1646728).
                # ignore and don't display a string
                pass

        # debug info for making sure the cities are in proper places
        '''for c in self.zones['America']['cities']:
            cpos = self.getPosition(c.lat, c.long)

            painter.drawLine(cpos + QPoint(1,1), cpos - QPoint(1,1))
            painter.drawLine(cpos + QPoint(1,-1), cpos - QPoint(1,-1))
            #painter.drawText(cpos + QPoint(2,-2), c.city_name)'''

    # @return pixel coordinate of a latitude and longitude for self
    # map uses Miller Projection, but is also clipped
    def getPosition(self, la, lo):
        width = min(self.width(), self.pixmap.width())
        height = min(self.height(), self.pixmap.height())
        # need to add/sub magic numbers because the map doesn't actually go
        # from -180...180, -90...90 thus the upper corner is not -180, -90
        # and we have to compensate
        # we need a better method of determining the actual range so we can
        # better place cities (shtylman)
        xdeg_offset = -6
        # the 180 - 360 accounts for the fact that the map does not span the
        # entire -90 to 90 the map does span the entire 360 though, just
        # offset
        x = ((width * (180.0 + lo) / 360.0) +
             (width * xdeg_offset / 180.0))
        x = x % width

        # top and bottom clipping latitudes
        topLat = 81
        bottomLat = -59

        # percent of entire possible range
        topPer = topLat / 180.0

        # get the y in rectangular coordinates
        y = 1.25 * math.log(math.tan(math.pi / 4.0 + 0.4 * math.radians(la)))

        # calculate the map range (smaller than full range because the map
        # is clipped on top and bottom)
        fullRange = 4.6068250867599998
        # the amount of the full range devoted to the upper hemisphere
        topOffset = fullRange * topPer
        mapRange = abs(
            1.25 * math.log(math.tan(
                math.pi / 4.0 + 0.4 * math.radians(bottomLat))) - topOffset)

        # Convert to a percentage of the map range
        y = abs(y - topOffset)
        y = y / mapRange

        # this then becomes the percentage of the height
        y = y * height

        return QtCore.QPoint(int(x), int(y))

    def mouseReleaseEvent(self, mouseEvent):
        pos = mouseEvent.pos()

        # get closest city to the point clicked
        closest = None
        bestdist = 0
        for c in self.tzdb.locations:
            np = pos - self.getPosition(c.latitude, c.longitude)
            dist = np.x() * np.x() + np.y() * np.y()
            if (dist < bestdist or closest is None):
                closest = c
                bestdist = dist

        # we need to set the combo boxes
        # this will cause the redraw we need
        if closest is not None:
            self._set_timezone(closest)

    # sets the timezone based on the full name (i.e 'Australia/Sydney')
    def set_timezone(self, name):
        self._set_timezone(self.tzdb.get_loc(name), name)

    # internal set timezone based on a city
    def _set_timezone(self, loc, zone=None):
        city = loc and self.cities[loc.zone]
        if city:
            self.selected_city = city
            self.selected_zone = zone or loc.zone
            self.zoneChanged.emit(loc, self.selected_zone)
            self.repaint()

    # return the full timezone string
    def get_timezone(self):
        return self.selected_zone
