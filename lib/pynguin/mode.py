from PyQt4 import QtCore, QtGui

from .pynguin import Pynguin, PynguinGraphicsItem

import logging
logger = logging.getLogger('PynguinLogger')


modes = {'pynguin': 'Pynguin',
            'logo': 'ModeLogo',
            'turtle': 'ModeTurtle'}


class ModeBase(Pynguin):
    '''Uses 2 pynguins to simulate a "logo-style" mode,
        that is: angle 0 is straight up, angles are positive
                    in the clockwise direction, positive X
                    is to the right, and positive Y is up.

        The standard self pynguin display is allowed to do
        its normal actions according to given commands, but
        is set "hidden"

        _pyn is used for display by converting from standard
        coordinates to the logo coordinates.

    '''

    def _gitem_setup(self):
        self._pyn_setup()
        Pynguin._gitem_setup(self)
        #self.qmove(self._pyn_setup)
        self.turnto(0)
        #QtCore.QTimer.singleShot(20, self._pyn_setup)
        QtCore.QTimer.singleShot(20, self._pyn_setup2)
        self.wait(0.2)
        self.gitem.ready = True

    def _pyn_setup(self):
        self._pyn = Pynguin()
        self._pyn._is_helper = True
        #self._pyn_reset_helper()

    def _pyn_setup2(self):
        Pynguin.avatar(self, 'hidden', sync=False)
        Pynguin.penup(self)
        self.gitem.setZValue(0)
        #self.turnto(0)

    def _setx(self, x):
        _, y = self.xy()
        self.goto(x, y)
    def _getx(self):
        x, y = self.xy()
        return x
    x = property(_getx, _setx)

    def _sety(self, y):
        x, _ = self.xy()
        self.goto(x, y)
    def _gety(self):
        x, y = self.xy()
        return y
    y = property(_gety, _sety)

    def _setang(self, ang):
        self.turnto(ang)
    def _getang(self):
        h = self.h()
        return h
    ang = property(_getang, _setang)
    heading = ang

    def reset(self, full=False):
        Pynguin.reset(self, full)
        if full:
            self._pyn_setup()
        else:
            self._pyn.reset()
        self._init_move((0,0),0)

    def reap(self):
        x, y, h = self.xyh()
        self.qmove(self._remove, (self._pyn,))
        self.promote(self)
        for pyn in self.mw.pynguins:
            if pyn is not self and pyn is not self._pyn:
                self.qmove(self._remove, (pyn,))
        self.qmove(self._pyn_setup)
        self.qmove(self._init_move, ((x, y), h))
        self.qmove(self._reap_helper)

    def _reap_helper(self):
        self._pyn.drawn_items.extend(self.drawn_items)
        self.drawn_items = []

    def xy(self, x=None, y=None):
        if x is None and y is None:
            x, y = self._pyn.xy()
            tx, ty = self._xy_rsl(x, y)
            return tx, ty
        else:
            tx, ty = self._xy_lfs(x, y)
            Pynguin.goto(self, tx, ty)
            tx, ty = self._xy_lrs(x, y)
            self._pyn.xy(tx, ty)

    def h(self, h=None):
        if h is None:
            ang = self._ang_rsl(self._pyn.h())
            return ang
        else:
            self.turnto(h)

    def xyforward(self, d):
        x, y = Pynguin.xyforward(self, d)
        return self._xy_lfs(x, y)

    def forward(self, d):
        logger.info('ML3forward %s' % self)
        Pynguin.forward(self, d)
        self._pyn.forward(d)
    fd = forward

    def left(self, a):
        Pynguin.left(self, a)
        self._pyn.left(a)
    lt = left

    def goto(self, x, y=None):
        if y is not None:
            tx, ty = self._xy_lfs(x, y)
            Pynguin.goto(self, tx, ty)
            tx, ty = self._xy_lrs(x, y)
            self._pyn.goto(tx, ty)
        else:
            Pynguin.goto(self, x)
            x, y = Pynguin.xy(self)
            tx, ty = self._xy_rsl(x, y)
            self._pyn.goto(tx, ty)

    def turnto(self, ang):
        if ang != 'random':
            logger.info('ML3turnto %s' % self)
            ta = self._ang_lfs(ang)
            Pynguin.turnto(self, ta)
            ta = self._ang_lrs(ang)
            self._pyn.turnto(ta)
        else:
            Pynguin.turnto(self, ang)

    def toward(self, x, y):
        logger.info('ML3toward %s' % self)
        tx, ty = self._xy_lfs(x, y)
        Pynguin.toward(self, tx, ty)
        tx, ty = self._xy_lrs(x, y)
        self._pyn.toward(tx, ty)

    def distance(self, x, y):
        tx, ty = self._xy_lfs(x, y)
        return self._pyn.distance(tx, ty)

    def lineto(self, x, y):
        logger.info('ML3lineto %s' % self)
        tx, ty = self._xy_lfs(x, y)
        ang = self._pyn.h()
        logger.info('ang %s' % ang)
        Pynguin.lineto(self, x, y)
        tx, ty = self._xy_lrs(x, y)
        #self._pyn.toward(tx, ty)
        self.goto(x, y)
        ang = self._pyn.h()
        logger.info('ang %s' % ang)
        self.turnto(self._ang_rsl(ang))

    def write(self, txt):
        self._pyn.write(txt)

    def home(self):
        Pynguin.home(self)
        self._pyn.home()
        self.turnto(0)

    def clear(self):
        self._pyn.clear()

    def penup(self):
        self._pyn.penup()
        self.pen = False

    def pendown(self):
        if hasattr(self, '_pyn'):
            self._pyn.pendown()
        self.pen = True

    def color(self, r=None, g=None, b=None):
        return self._pyn.color(r, g, b)

    def width(self, w=None):
        return self._pyn.width(w)

    def fillcolor(self, r=None, g=None, b=None):
        return self._pyn.fillcolor(r, g, b)

    def fill(self, color=None, rule=None):
        return self._pyn.fill(color, rule)

    def nofill(self):
        self._pyn.nofill()

    def fillrule(self, rule):
        if hasattr(self, '_pyn'):
            self._pyn.fillrule(rule)

    def circle(self, r, center=False):
        self._pyn.circle(r, center)

    def square(self, side, center=False):
        self._pyn.square(side, center)

    def avatar(self, imageid=None, filepath=None):
        sync = self is self.mw.pynguin
        return self._pyn.avatar(imageid, filepath, sync=sync)

    def onscreen(self):
        return self._pyn.onscreen()

    def viewcoords(self, floats=False):
        xmin, ymin, xmax, ymax = Pynguin.viewcoords(self, floats)
        txmin, tymin = self._xy_rsl(xmin, ymin)
        txmax, tymax = self._xy_rsl(xmax, ymax)
        # y-coords get swapped in sign ...
        return txmin, tymax, txmax, tymin

    def stamp(self, imageid=None):
        self._pyn.stamp(imageid)

    def label(self, name=None):
        if name is None:
            return self.name
        else:
            self._name = name
            self._pyn.label(name)

    def _setname(self, name):
        if name != self._name:
            self._name = name
            self.qmove(self._pyn._gitem_setlabel, (name,))
    def _getname(self):
        return self._name
    name = property(_getname, _setname)


class ModeLogo(ModeBase):
    def _xy_fsl(self, x, y):
        # from faked standard to logo coords
        return y, x
    def _xy_rsl(self, x, y):
        # from real standard to logo coords
        return x, -y
    def _xy_lfs(self, x, y):
        # from logo coords to fake standard coords
        return y, x
    def _xy_lrs(self, x, y):
        # from logo coords to real standard coords
        return x, -y
    def _ang_fsl(self, a):
        # from fake standard angle to logo angle
        return a
    def _ang_rsl(self, a):
        # from real standard angle to logo angle
        return a + 90
    def _ang_lfs(self, a):
        # from logo angle to fake standard angle
        return a
    def _ang_lrs(self, a):
        # from logo angle to real standard angle
        return a - 90


class ModeTurtle(ModeBase):
    def _xy_fsl(self, x, y):
        # from faked standard to logo coords
        return x, -y
    def _xy_rsl(self, x, y):
        # from real standard to logo coords
        return x, -y
    def _xy_lfs(self, x, y):
        # from logo coords to fake standard coords
        return x, -y
    def _xy_lrs(self, x, y):
        # from logo coords to real standard coords
        return x, -y
    def _ang_fsl(self, a):
        # from fake standard angle to logo angle
        return -a
    def _ang_rsl(self, a):
        # from real standard angle to logo angle
        return -a
    def _ang_lfs(self, a):
        # from logo angle to fake standard angle
        return -a
    def _ang_lrs(self, a):
        # from logo angle to real standard angle
        return -a
