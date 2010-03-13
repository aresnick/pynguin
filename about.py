# Copyright 2010 Lee Harr
#
# This file is part of pynguin.
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

from PyQt4 import QtGui, uic

from conf import uidir


class AboutDialog(QtGui.QDialog):
    def __init__(self):
        QtGui.QDialog.__init__(self)
        uifile = 'about.ui'
        uipath = os.path.join(uidir, uifile)
        uic.loadUi(uipath, self)
