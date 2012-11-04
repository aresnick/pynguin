# Copyright 2010-2012 Lee Harr
#
# This file is part of pynguin.
# http://pynguin.googlecode.com/
#
# Pynguin is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Pynguin is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Pynguin.  If not, see <http://www.gnu.org/licenses/>.


from PyQt4 import QtGui, QtCore

from . import util


class Splash(QtGui.QSplashScreen):
    def __init__(self, app):
        svgrenderer = util.SvgRenderer(app)
        rend = svgrenderer.getrend()
        img = QtGui.QPixmap(500, 320)
        img.fill(QtCore.Qt.transparent)
        self.img = img
        painter = QtGui.QPainter(img)
        rend.render(painter, 'splash')
        painter.end()
        QtGui.QSplashScreen.__init__(self, img)
        self.setMask(img.mask())
        self.away_later()

    def away_later(self):
        QtCore.QTimer.singleShot(1500, self.away)

    def away(self):
        if hasattr(self, 'win'):
            self.finish(self.win)
        else:
            self.away_later()
