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
from random import randrange

from PyQt4 import QtCore, QtSvg, QtGui


def sign(x):
    'return 1 if x is positive, -1 if negative, or zero'
    return cmp(x, 0)

def getrend(app):
    'return a handle to the app-wide shared SVG renderer'
    filename = 'pynguin.svg'
    filepath = os.path.join('data/images', filename)
    fp = QtCore.QString(filepath)
    rend = QtSvg.QSvgRenderer(fp, app)
    return rend

def choose_color(r=None, g=None, b=None):
    if r == 'random':
        r, g, b = [randrange(256) for cc in range(3)]
    elif r == 'rlight':
        r, g, b = [randrange(200, 256) for cc in range(3)]
    elif r == 'rmedium':
        r, g, b = [randrange(100, 200) for cc in range(3)]
    elif r == 'rdark':
        r, g, b = [randrange(100) for cc in range(3)]
    elif r is g is b is None:
        return None, None, None
    elif g is not None and b is not None:
        c = QtGui.QColor.fromRgb(r, g, b)
        r, g, b = c.red(), c.green(), c.blue()
    elif r is not None:
        c = QtGui.QColor(r)
        r, g, b = c.red(), c.green(), c.blue()
    elif r is None or g is None or b is None:
        raise TypeError

    return r, g, b
