# Copyright 2010 Lee Harr
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


import os

from PyQt4 import QtGui, QtCore, uic

from . import util
from .util import get_datadir
from .conf import version

datadir = get_datadir()
uidir = os.path.join(datadir, 'ui')

class AboutDialog(QtGui.QDialog):
    def __init__(self, app):
        QtGui.QDialog.__init__(self)
        uifile = 'about.ui'
        uipath = os.path.join(uidir, uifile)
        self.ui = uic.loadUi(uipath, self)

        svgrenderer = util.SvgRenderer(app)
        rend = svgrenderer.getrend()
        img = QtGui.QPixmap(225, 144)
        img.fill(QtCore.Qt.transparent)
        self.img = img
        painter = QtGui.QPainter(img)
        rend.render(painter, 'splash')
        painter.end()

        self.ui.splasharea.setPixmap(self.img)
        self.ui.progtitle.setText(version)
