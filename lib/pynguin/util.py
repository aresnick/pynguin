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
import sys
from random import randrange

from PyQt4 import QtCore, QtSvg, QtGui


def sign(x):
    'return 1 if x is positive, -1 if negative, or zero'
    return cmp(x, 0)

def getrend(app):
    'return a handle to the app-wide shared SVG renderer'
    filename = 'pynguin.svg'
    filepath = os.path.join(datadir, 'images', filename)
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
        try:
            rr, gg, bb = r
            rr, gg, bb = int(rr), int(gg), int(bb)
        except ValueError:
            c = QtGui.QColor(r)
            r, g, b = c.red(), c.green(), c.blue()
        else:
            r, g, b = rr, gg, bb
    elif r is None or g is None or b is None:
        raise TypeError

    return r, g, b

def nudge_color(color, red=None, blue=None, green=None):
    """Change the pen color by given amounts.

    Amounts can be either integer numbers (to be added to the RGB
    tuple components), or percentages (to increase or decrease
    that component by given percent)

    >>> color==(100, 100, 100) then calling
    >>> nudge_color(color, red=50, blue=-10, green="75%")
    (150, 90, 75)
    """

    r, g, b = color
    if red is not None:
        try:
            r += red
        except TypeError:
            r *= (float(red[:-1]) / 100.0)
    if blue is not None:
        try:
            b += blue
        except TypeError:
            b *= (float(blue[:-1]) / 100.0)
    if green is not None:
        try:
            g += green
        except TypeError:
            g *= (float(green[:-1]) / 100.0)

    r = min(r, 255)
    g = min(g, 255)
    b = min(b, 255)
    r = max(r, 0)
    g = max(g, 0)
    b = max(b, 0)

    return (r, g, b)


def get_datadir():
    if '-d' in sys.argv:
        dd = 'data'
        base = ''
    else:
        dd = 'share/pynguin'
        base = sys.prefix

    absbase = os.path.abspath(base)

    return os.path.join(absbase, dd)

def get_docdir():
    if '-d' in sys.argv:
        dd = 'doc'
        base = ''
    else:
        dd = 'share/doc/pynguin'
        base = sys.prefix

    absbase = os.path.abspath(base)

    return os.path.join(absbase, dd)

def check_data_doc_dir():
    d1 = get_datadir()
    d2 = get_docdir()
    return os.path.exists(d1) and os.path.exists(d2)

datadir = get_datadir()
