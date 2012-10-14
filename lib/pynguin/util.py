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


import os
import sys
from random import randrange
from math import copysign

from PyQt4 import QtCore, QtSvg, QtGui

import logging
logger = logging.getLogger('PynguinLogger')


NOTHING = object()

def sign(x):
    'return 1 if x is positive, -1 if negative, or zero'
    return copysign(1, x)


NODEFAULT = object()
def _plist(f):
    '''given function object,
        return a list of [(arg name: default value or None), ...]
    '''
    parameter_defaults = []
    defaults = f.__defaults__
    if defaults is not None:
        defaultcount = len(defaults)
    else:
        defaultcount = 0
    argcount = f.__code__.co_argcount
    for i in range(f.__code__.co_argcount):
        name = f.__code__.co_varnames[i]
        value = NODEFAULT
        if i >= argcount - defaultcount:
            value = defaults[i - (argcount - defaultcount)]
        parameter_defaults.append((name, value))
    return parameter_defaults


class SvgRenderer(object):
    'factory for svg renderer objects'

    def __init__(self, app):
        self.app = app

    def getrend(self, filepath=None):
        '''return a handle to the shared SVG renderer
            for the given svg file.

        If no filepath is given, return the renderer for
            the default svg file.

        '''
        if filepath is None:
            filename = 'pynguin.svg'
            filepath = os.path.join(datadir, 'images', filename)
        fp = filepath
        rend = QtSvg.QSvgRenderer(fp, self.app)
        return rend


def choose_color(r=None, g=None, b=None, a=None):
    if a is None:
        a = 255
    elif not (0<=a<=255):
        raise ValueError('Alpha value must be between 0 and 255')

    if r == 'random':
        r, g, b = [randrange(256) for cc in range(3)]
    elif r == 'rlight':
        r, g, b = [randrange(200, 256) for cc in range(3)]
    elif r == 'rmedium':
        r, g, b = [randrange(100, 200) for cc in range(3)]
    elif r == 'rdark':
        r, g, b = [randrange(100) for cc in range(3)]
    elif r == 'ralpha':
        r, g, b = [randrange(256) for cc in range(3)]
        a = randrange(100, 200)
    elif r is g is b is None:
        return None, None, None, None
    elif g is not None and b is not None:
        if not (0<=r<=255 and 0<=g<=255 and 0<=b<=255):
            raise ValueError('Color components must be between 0 and 255')
        c = QtGui.QColor.fromRgb(r, g, b, a)
        r, g, b, a = c.red(), c.green(), c.blue(), c.alpha()
    elif r is not None:
        try:
            if len(r) == 4:
                rr, gg, bb, aa = r
                rr, gg, bb, aa = int(rr), int(gg), int(bb), int(aa)
            elif len(r) == 3:
                rr, gg, bb = r
                rr, gg, bb = int(rr), int(gg), int(bb)
                aa = 255
            else:
                raise ValueError
        except ValueError:
            try:
                ci = int(r)
                c = QtGui.QColor.fromRgba(ci)
            except ValueError:
                c = QtGui.QColor(r)
            r, g, b, a = c.red(), c.green(), c.blue(), c.alpha()
        else:
            r, g, b, a = rr, gg, bb, aa
    elif r is None or g is None or b is None:
        raise TypeError

    return r, g, b, a

def nudge_color(color, r=None, g=None, b=None, a=None):
    """Change the color (a 3-element tuple) by given amounts,
        return the new RGB tuple.

    Clamps the RGB return values such that 0 <= RGB <= 255
        but does not necessarily return only integer values.

        Not returning strictly integers allows for smoother color
        variations, but note that when the values are passed
        to the pynguin color() function the values will be
        converted to integers. So in order to take advantage
        of the more precise values you will need to keep those
        separately from the actual pynguin color values.

    The function's r, g, b parameters can be either:

    numbers to be added to or subtracted from the RGB tuple
        components, or

    percentages (as strings) that will be multiplied by the component
        to increase or decrease that component by given the given
        percent.

    >>> color = (100, 100, 100)
    >>> nudge_color(color, g=15)
    (100, 115, 100)

    >>> color = (100, 100, 100)
    >>> nudge_color(color, r=-12.5)
    (87.5, 100, 100)

    >>> color = (100, 100, 100)
    >>> color = nudge_color(color, b='75%')
    >>> color
    (100, 100, 75.0)
    >>> nudge_color(color, b='75%')
    (100, 100, 57.25)

    >>> color = (100, 100, 100)
    >>> nudge_color(color, r=50, g='105%', b=-10)
    (150, 105, 90)
    """

    if len(color) == 3:
        rc, gc, bc = color
        ac = 255
    elif len(color) == 4:
        rc, gc, bc, ac = color
    else:
        raise ValueError

    if r is not None:
        try:
            rc += r
        except TypeError:
            rc *= (float(r[:-1]) / 100.0)

    if g is not None:
        try:
            gc += g
        except TypeError:
            gc *= (float(g[:-1]) / 100.0)

    if b is not None:
        try:
            bc += b
        except TypeError:
            bc *= (float(b[:-1]) / 100.0)

    if a is not None:
        try:
            ac += a
        except TypeError:
            ac *= (float(a[:-1]) / 100.0)

    rc = min(rc, 255)
    gc = min(gc, 255)
    bc = min(bc, 255)
    ac = min(ac, 255)
    rc = max(rc, 0)
    gc = max(gc, 0)
    bc = max(bc, 0)
    ac = max(ac, 0)

    return (rc, gc, bc, ac)


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
