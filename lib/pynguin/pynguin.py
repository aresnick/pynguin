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
import queue
import time
from random import randrange
from math import atan2, degrees, radians, hypot, cos, sin, pi
PI = pi
import random
import string
from threading import Lock
import logging
logger = logging.getLogger('PynguinLogger')

from PyQt4 import QtCore, QtGui, QtSvg
processEvents = QtGui.QApplication.processEvents
AllEvents = QtCore.QEventLoop.AllEvents

from . import util
from .util import sign, choose_color
from . import conf


pynguin_functions = [
    'forward', 'fd', 'backward', 'bk', 'left',
    'lt', 'right', 'rt', 'reset', 'home',
    'penup', 'pendown', 'color', 'width',
    'circle', 'fill', 'nofill', 'fillcolor',
    'goto', 'xy', 'xyh', 'h', 'turnto', 'clear',
    'write', 'toward', 'distance', 'lineto', 'xyforward',
    'onscreen', 'viewcoords', 'stamp', 'square',
    'avatar', 'remove', 'promote', 'reap',
    'speed', 'track', 'notrack', 'bgcolor', 'mode', 'colorat']
interpreter_protect = [
    'p', 'pynguin', 'Pynguin', 'ModeLogo', 'ModeTurtle', 'pynguins',
    'PI', 'history', 'util', 'log']

class TooManyPynguins(RuntimeError):
    pass

class QQ(object):
    class QQDelaying(Exception):
        pass

    def __init__(self):
        self._queues = {}
        self._pynguins = []
        self.nq = 0
        self.qq = 0
        self._lock = Lock()

    def append(self, pyn, q):
        if pyn in self._pynguins:
            raise RuntimeError
        self._pynguins.append(pyn)
        self._queues[pyn] = q
        self.nq += 1

    def remove(self, pyn):
        if pyn in self._queues:
            del self._queues[pyn]
            self._pynguins.remove(pyn)
            self.nq = len(self._queues)
        self.qq = 0

    def get(self):
        if not self.nq:
            raise queue.Empty

        qq0 = self.qq
        delaying = 0
        while True:
            pyn = self._pynguins[self.qq]
            pynqq = self.qq

            self.qq += 1
            if self.qq >= self.nq:
                self.qq = 0

            if pyn._delaying is not None:
                if pyn.drawspeed == 0:
                    pyn._delaying = None
                    self.qq = pynqq
                    continue
                else:
                    delaying += 1
                    pyn._delaying -= self.nq
                    if pyn._delaying <= 0:
                        pyn._delaying = None

            else:
                try:
                    q = self._queues.get(pyn)
                    if q is not None:
                        mv = q.get(block=False)
                    else:
                        self.remove(pyn)
                        qq0 = 0
                        continue
                except queue.Empty:
                    pass
                else:
                    return mv

            if self.qq == qq0:
                if delaying:
                    raise self.QQDelaying
                else:
                    raise queue.Empty

    def clear(self, lock):
        self._lock.acquire()

        for pyn in self._pynguins:
            pyn._delaying = None

            q = self._queues.get(pyn)
            if q is None:
                continue
            #logger.info('CLEAR')
            #logger.info(pyn)
            #logger.info(q.qsize())
            while True:
                #logger.info(q)
                try:
                    mv = q.get(block=False)
                    if not lock:
                        processEvents(AllEvents)
                except queue.Empty:
                    break

        self._lock.release()

    def qqsize(self):
        sz = 0
        for pyn, q in self._queues.items():
            sz += q.qsize()
        return sz


class Pynguin(object):
    class Defunct(Exception):
        pass

    ControlC = False

    delay = 0
    _throttledown = 0

    _all_moves = QQ()
    _checktime = QtCore.QTime()
    _checktime.start()

    _drawspeed_pending = None
    _turnspeed_pending = None
    drawspeed = 0
    turnspeed = 0

    _zvalue = 0

    _name = ''

    mw = None # set by MainWindow before any Pynguin get instantiated
    rend = None # set by MainWindow before any Pynguin get instantiated

    _track_main_pynguin = None # set up by mw.setup_settings
    _track_pynguin = None

    _modename = 'pynguin'

    defunct = False

    _delaying = None
    _wfi = None

    def _log(self, *args):
        argstrings = [str(a) for a in args]
        strargs = ' '.join(argstrings)
        logger.info(strargs)

    def __init__(self, pos=None, ang=None, helper_for=False):
        '''helper not False means this pynguin is being used by one
            of the alternate modes in mode.py

            _is_helper should be a link to the pynguin this one
                is a helper for.

        '''

        self._moves = queue.Queue(0) # max number of items in queue
        self._all_moves.append(self, self._moves)

        if pos is None:
            pos = (0, 0)
        if ang is None:
            ang = 0
        self._is_helper = helper_for

        self.scene = self.mw.scene
        self.ritem = RItem() #real location, angle, etc.
        self.gitem = None # Gets set up later in the main thread
        self.drawn_items = []
        self._setup()
        self._init_move(pos, ang)

    def __lt__(self, other):
        return self._zvalue < other._zvalue

    def _setup(self):
        if not self._is_helper:
            self.mw.pynguins.append(self)

            # enforce maximum of 150 pynguins
            npyn = len(self.mw.pynguins)
            if npyn > 150:
                self.mw.pynguins.remove(self)
                raise TooManyPynguins('Exceeded maximum of 150 pynguins.')

        if self.mw.pynguin is None:
            #self._log('_setup no mw.pynguin')
            self._gitem_setup()

        else:
            #self._log('qmove _gitem_setup')
            self.qmove(self._gitem_setup)

            cc = 0
            while self.gitem is None or not self.gitem.ready:
                self.wait(0.01)
                if self.ControlC:
                    raise KeyboardInterrupt
                elif cc >= 50:
                    #self._log('_setup timeout')
                    self._gitem_setup()
                cc += 1

    def _init_move(self, pos, ang):
        x, y = pos
        self.goto(x, y)
        self.turnto(ang)

        settings = QtCore.QSettings()
        speed = settings.value('pynguin/speed', 'fast')
        self.speed(speed)

        self._set_color_to_default()
        self._set_fillcolor_to_default()

        self.pendown()
        self.fillrule('winding')

    def _remove(self, pyn):
        pyn.defunct = True
        self._all_moves.remove(pyn)

        if pyn is self:
            self._clear()
        else:
            self.drawn_items.extend(pyn.drawn_items)
            pyn.drawn_items = []

        pyn._setImageid('hidden', sync=False)
        if pyn.gitem is not None:
            self._gitem_setlabel('')
            scene = pyn.gitem.scene()
            scene.removeItem(pyn.gitem)
        pyn.ogitem = pyn.gitem
        pyn.gitem = None

        if pyn in self.mw.pynguins:
            self.mw.pynguins.remove(pyn)

        if pyn is self.mw.pynguin:
            if self.mw.pynguins:
                # need to promote another pynguin to be the main one
                mainpyn = self.mw.pynguins[0]
            else:
                #nobody left ... create a new one
                mname = pyn._modename
                mainpyn = self.mw.new_pynguin(mname, show_cmd=False)
            self.mw.pynguin = mainpyn
            self.mw.setup_interpreter_locals()

    def remove(self, pyn=None):
        '''take the given pynguin (or this one if none specified)
            out of the scene.

        If removing a different pynguin from this one, this one will
            adopt all of the drawn items from the other pynguin. In
            other words, items drawn by the pynguin that is being
            removed will not be cleared immediately, but can later
            be cleared by this pynguin.

        If this pynguin is removing itself, it will first clear all
            of its own drawings, otherwise there will be no way to
            clear them out later.
        '''

        if pyn is None:
            pyn = self

        self.mw._defunct_pynguins.append(pyn)
        if pyn in self.mw.pynguins:
            self.mw.pynguins.remove(pyn)

        self._log('rmv', pyn)
        if hasattr(pyn, '_pyn'):
            self._log('plus')
            self.remove(pyn._pyn)
        pyn.waitforit()
        self.qmove(self._remove, (pyn,))

    def reap(self):
        '''promote self to be main pynguin and remove all other pynguins,
            taking charge of their drawings.
        '''
        if self is not self.mw.pynguin:
            self.promote(self)
            #self.waitforit()

        pynguins = self.mw.pynguins
        pynguins.remove(self)
        while pynguins:
            pyn = pynguins.pop()
            self.remove(pyn)
            #self.waitforit()
        pynguins.append(self)

        self.qmove(self._clear_defunct_pynguins_later)

    def _promote(self, pyn):
        self.mw.pynguin = pyn
        self.mw.setup_interpreter_locals()
    def promote(self, pyn=None):
        '''make the given pynguin the main pynguin, and update the
            console locals to make the new main pynguins method the
            built-in commands.
        '''
        if pyn is None:
            pyn = self
        self.qmove(self._promote, (pyn,))
        self.mw.setup_interpreter_locals(pyn)

    def _gitem_setup(self):
        self.gitem = PynguinGraphicsItem(self.rend, 'pynguin', self) #display only
        self._imageid = 'pynguin'
        self.scene.addItem(self.gitem)
        Pynguin._zvalue += 1
        self.gitem.setZValue(9999999 - self._zvalue)
        self.gitem._current_line = None

        self.gitem.ready = True

    def _set_item_pos(self, item, pos):
        item.setPos(pos)

    def _setx(self, x):
        self.goto(x, self.y)
    def _getx(self):
        return self.pos.x()
    x = property(_getx, _setx)

    def _sety(self, y):
        self.goto(self.x, y)
    def _gety(self):
        return self.pos.y()
    y = property(_gety, _sety)

    def _setang(self, ang):
        self.turnto(ang)
    def _getang(self):
        return self.ritem.ang
    ang = property(_getang, _setang)
    heading = ang

    def _set_pos(self, args):
        '''Setter for the position property.

            args can be a QPoint[F] or a 2-tuple of numbers.
        '''
        try:
            pos = QtCore.QPointF(args)
        except TypeError:
            pos = QtCore.QPointF(*args)
        self._set_item_pos(self.ritem, pos)
        self.qmove(self._set_item_pos, (self.gitem, pos,))
    def _get_pos(self):
        'Getter for the position property.'
        return self.ritem.pos()
    pos = property(_get_pos, _set_pos)

    def xy(self, x=None, y=None):
        '''Get or set the position. Call with no args to get: xy()
            Or provide both x and y to set: xy(150, 200)
        '''
        if x is None and y is None:
            return self.x, self.y
        elif x is not None and y is not None:
            self.goto(x, y)
        else:
            raise ValueError

    def xyh(self, x=None, y=None, h=None):
        '''Get or set the position and heading. Call with no args to
            get: xyh()
            Or provide x, y, and h to set: xyh(150, 200, 180)
        '''
        if x is None and y is None and h is None:
            x, y = self.xy()
            h = self.h()
            return x, y, h
        elif x is not None and y is not None and h is not None:
            self.xy(x, y)
            self.h(h)
        else:
            raise ValueError

    def h(self, h=None):
        '''Get or set the heading. Call with no args to get: h()
            Or provide heading to set: h(180)
        '''
        if h is None:
            return self.heading
        else:
            self.heading = h

    def xyforward(self, distance):
        '''return the x-y coordinate of the point the pynguin would be at
            if it were to move forward the given distance.
        '''
        deg = self.heading
        rad = deg * (PI / 180)
        dx = distance * cos(rad)
        dy = distance * sin(rad)

        x0, y0 = self.xy()

        x = x0 + dx
        y = y0 + dy

        return x, y

    @classmethod
    def _empty_move_queue(cls, lock=False):
        cls._all_moves.clear(lock)

    def _sync_items(self):
        '''Sometimes, after running code is interrupted (like by Ctrl-C)
            the actual position (ritem.pos) and displayed position
            (gitem.pos) will be out of sync.

            This method can be called to synchronize the ritem to the
            position and rotation of the display.

        '''

        if self.gitem is not None:
            pos = self.gitem.pos()
            ang = self.gitem.ang
        else:
            pos = (0, 0)
            ang = 0
        self.ritem.setPos(pos)
        self.ritem.ang = ang

    @classmethod
    def _process_moves(cls):
        '''Apply the queued commands for the graphical display item
            This must be done from the main thread
        '''

        delay = cls.delay
        etime = cls._checktime.elapsed()
        #logger.info('_r')
        if cls.ControlC:
            cls.ControlC += 1
            cls._empty_move_queue()
            #logger.info('CC _pm %s' % cls.ControlC)
            #logger.info('CCnomove %s' % cls.mw.interpretereditor.cmdthread)
            if cls.mw.interpretereditor.cmdthread is not None:
                #logger.info('CC1')
                cls.mw.interpretereditor.cmdthread.terminate()
                #logger.info('CC2')

        elif etime > delay:
            ied = cls.mw.interpretereditor
            runmoves = 0
            while True:
                runmoves += 1
                if runmoves >= 100:
                    break

                try:
                    move, args, pyn = cls._all_moves.get()
                except queue.Empty:
                    cls._throttledown += 1
                    if cls._throttledown > 200:
                        cls.delay = 300
                    elif cls._throttledown > 20:
                        cls.delay = 10

                    if cls.delay:
                        cls.mw.killTimer(cls.mw._movetimer)
                        cls.mw._movetimer = cls.mw.startTimer(cls.delay)

                    #logger.info(cls._throttledown)
                    #logger.info(etime)
                    break
                except cls._all_moves.QQDelaying:
                    pass
                else:
                    if cls.delay:
                        cls.mw.killTimer(cls.mw._movetimer)
                        cls.mw._movetimer = cls.mw.startTimer(0)

                    cls._throttledown = 0
                    cls.delay = 0

                    if pyn.defunct:
                        logger.info('defunct')
                    else:
                        try:
                            #logger.info(move)
                            #logger.info(args)
                            move(*args)
                        except Exception:
                            import sys
                            tb = sys.exc_info()[2]
                            import traceback
                            tb = traceback.format_exc()
                            logger.info(tb)
                            ied.write(tb)
                            ied.write('\n')
                            if ied.cmdthread is not None:
                                ied.cmdthread.terminate()
                                ied.cmdthread = None
                            cls._empty_move_queue()
                            ied.write('>>> ')

            cls._checktime.restart()

        QtGui.QApplication.processEvents(QtCore.QEventLoop.AllEvents)

    def _qdelay(self, n):
        if self._delaying is not None:
            raise RuntimeError
        else:
            self._delaying = n

    def wait(self, s):
        for ms in range(int(s*1000)):
            time.sleep(0.001)
            QtGui.QApplication.processEvents(QtCore.QEventLoop.AllEvents)

    @classmethod
    def wait_for_empty_q(cls):
        n = 0
        while cls._all_moves.qqsize():
            #logger.info(cls._all_moves.qqsize())
            cls._process_moves()
        #logger.info('READY')

    def _waitforit(self, flag):
        self._wfi = flag

    def waitforit(self):
        flag = ''.join(random.sample(string.ascii_letters, 15))
        self.qmove(self._waitforit, (flag,))
        #self._log('waiting for:', flag)
        while self._wfi != flag:
            if self.ControlC:
                logger.info('WFI Break')
                break
            self.mw.interpretereditor.spin(1, 0)
        #self._log('found:', flag)
        self._wfi = None
        # lock this!

    def _gitem_new_line(self):
        if self.gitem is not None:
            self.gitem._current_line = None

    def _item_forward(self, item, distance, draw=True):
        '''Move item ahead distance. If draw is True, also add a line
            to the item's scene. draw should only be true for gitem
        '''
        ang = item.ang
        rad = ang * (PI / 180)
        dx = distance * cos(rad)
        dy = distance * sin(rad)

        p1 = item.pos()

        x = p1.x()+dx
        y = p1.y()+dy
        p2 = QtCore.QPointF(x, y)
        item.setPos(p2)

        if draw and item._pen:
            cl = self.gitem._current_line
            if cl is None:
                ppath = QtGui.QPainterPath(p1)
                ppath.lineTo(p2)
                if self.gitem._fillmode:
                    ppath.setFillRule(self.gitem._fillrule)

                line = item.scene().addPath(ppath, item.pen)

                if self.gitem._fillmode:
                    line.setBrush(self.gitem.brush)

                line.setZValue(self._zvalue)
                Pynguin._zvalue += 1
                self.drawn_items.append(line)
                self.gitem._current_line = line
            else:
                ppath = cl.path()
                plast = ppath.currentPosition()
                if p2 != plast:
                    ppath.lineTo(p2)
                    cl.setPath(ppath)

    def _gitem_move(self, distance):
        self._item_forward(self.gitem, distance)

    def _gitem_breakup_move(self, distance):
        '''used to break up movements for graphic animations. gitem will
            move forward by distance, but it will be done in steps that
            depend on the drawspeed setting
        '''
        self._check_drawspeed_change()

        drawspeed = self.drawspeed
        if distance >= 0:
            perstep = drawspeed
        else:
            perstep = -drawspeed

        adistance = abs(distance)
        d = 0
        while d < adistance:
            if perstep == 0:
                step = distance
                d = adistance
            elif d + drawspeed > adistance:
                step = sign(perstep) * (adistance - d)
            else:
                step = perstep
            d += drawspeed

            self.qmove(self._gitem_move, (step,))
            if self.drawspeed:
                self.qmove(self._qdelay, (100*(40-self.drawspeed),))

            QtGui.QApplication.processEvents(QtCore.QEventLoop.AllEvents)

    @classmethod
    def _check_drawspeed_change(cls):
        if Pynguin._drawspeed_pending is not None:
            Pynguin.drawspeed = Pynguin._drawspeed_pending
            Pynguin._drawspeed_pending = None
            Pynguin.turnspeed = Pynguin._turnspeed_pending
            Pynguin._turnspeed_pending = None

    def qmove(self, func, args=None):
        '''queue up a command for later application'''

        if self.defunct:
            raise Pynguin.Defunct

        if self.ControlC:
            Pynguin.ControlC += 1
            raise KeyboardInterrupt

        if args is None:
            args = ()

        #logger.info('qmove %s' % func)
        thread = QtCore.QThread.currentThread()
        #logger.info(thread)
        #import threading
        #logger.info(threading.current_thread())
        if thread == self.mw._mainthread:
            #logger.info('QMOVE MAIN THREAD')
            #logger.info(func)
            #logger.info(args)
            # Coming from main thread. Could be an onclick handler
            #   or a menu-item action
            func(*args)
            return

        self._moves.put_nowait((func, args, self))

    def forward(self, distance):
        '''forward(distance) # in pixels | aka: fd(distance)

        Move the pynguin forward by distance pixels. Note that
            forward depends on which direction the pynguin is
            facing when you tell him to go forward.

        If the pen is down, this will also draw a line as the
            pynguin moves forward.
        '''
        self._item_forward(self.ritem, distance, False)
        self._gitem_breakup_move(distance)
    fd = forward

    def backward(self, distance):
        '''backward(distance) # in pixels | aka: bk(distance)

        Move the pynguin backward by distance pixels. Note that
            forward depends on which direction the pynguin is
            facing when you tell him to go forward.

        If the pen is down, this will also draw a line as the
            pynguin moves backward.
        '''
        self.forward(-distance)
    bk = backward

    def _item_left(self, item, degrees):
        item.rotate(-degrees)
    def _gitem_turn(self, degrees):
        self._item_left(self.gitem, degrees)
    def _gitem_breakup_turn(self, degrees):
        self._check_drawspeed_change()

        turnspeed = self.turnspeed
        if degrees >= 0:
            perstep = self.turnspeed
        else:
            perstep = -self.turnspeed

        adegrees = abs(degrees)
        a = 0
        n = 0
        while a < adegrees:
            if perstep == 0:
                step = degrees
                a = adegrees
            elif a + turnspeed > adegrees:
                step = sign(perstep) * (adegrees - a)
            else:
                step = perstep
            n += 1
            a += self.turnspeed

            self.qmove(self._gitem_turn, (step,))
            if self.turnspeed:
                #logger.info('DELAY')
                #logger.info('SELF %s' % self)
                #logger.info('TS %s' % self.turnspeed)
                self.qmove(self._qdelay, (100*(80-self.turnspeed),))

    def left(self, degrees):
        '''left(angle) # in degrees | aka: lt(angle)

        Rotate the pynguin counter-clockwise by angle degrees. Note
            that the final angle will depend on the initial angle.

        To turn the pynguin directly to a particular angle, use turnto
        '''
        self._item_left(self.ritem, degrees)
        self._gitem_breakup_turn(degrees)
    lt = left

    def right(self, degrees):
        '''right(angle) # in degrees | aka: rt(angle)

        Rotate the pynguin clockwise by angle degrees. Note
            that the final angle will depend on the initial angle.

        To turn the pynguin directly to a particular angle, use turnto
        '''
        self.left(-degrees)
    rt = right

    def _item_goto(self, item, pos):
        item.setPos(pos)
        item.set_transform()

    def _gitem_goto(self, pos):
        self._item_goto(self.gitem, pos)
    def goto(self, x, y=None):
        '''goto(x, y) # in pixels.

        Jump the pynguin directly to the coordinates given in x and y.
            The (0, 0) location is in the center of the screen, with
            positive x values to the right, and positive y values down.

        Or, if given the single argument 'random' jump to a random
            location on the currently visible screen as determined
            by the viewcoords() method.

        No line will be drawn, no matter what the state of the pen.
        '''
        if x != 'random':
            #logging.debug('g1')
            pos = QtCore.QPointF(x, y)
            #logging.debug('g2')
            self._item_goto(self.ritem, pos)
            #logging.debug('g3')
            self.qmove(self._gitem_new_line)
            #logging.debug('g4')
            self.qmove(self._gitem_goto, (pos,))
            #logging.debug('g5')
        elif y != None:
            # passed in 'random' plus something else...
            # That can't be right
            raise ValueError("'random' must be passed alone.")
        else:
            xmin, ymin, xmax, ymax = self.viewcoords()
            x = random.randrange(int(xmin), int(xmax))
            y = random.randrange(int(ymin), int(ymax))
            self.goto(x, y)

    def _gitem_setangle(self, ang):
        self._item_setangle(self.gitem, ang)
    def _item_setangle(self, item, ang):
        item.ang = ang
        item.set_transform()

    def turnto(self, ang):
        '''turnto(angle) # in degrees

        Turn the pynguin directly to the given angle. The angle is given
            in degrees with 0 degrees being to the right, positive angles
            clockwise, and negative angles counter-clockwise.

        The final angle will be the angle specified, not an angle relative
            to the initial angle. For relative angles, use left or right.
        '''
        if ang != 'random':
            try:
                test = float(ang)
                test2 = ang + 1
            except (TypeError, ValueError):
                raise TypeError('turnto(ang) takes one number as a parameter: the angle to turn to.')

            self._item_setangle(self.ritem, ang)
            self.qmove(self._gitem_setangle, (ang,))

        else:
            ang = random.randrange(360)
            self.turnto(ang)

    def _closest_turn(self, ang):
        '''return the angle to turn most quickly from current angle to ang
        '''
        ang0 = self.ritem.ang
        dang = ang - ang0
        dang = dang % 360
        if dang > 180:
            dang = dang - 360
        elif dang < -180:
            dang = dang + 360
        return dang

    def toward(self, x, y):
        '''toward(x, y) # in pixels

        Turn toward the given coordinates. After this command, the pynguin
            will be facing directly toward the given coordinates.
        '''
        cpos = self.ritem.pos()
        cx = cpos.x()
        cy = cpos.y()
        dx = x-cx
        dy = y-cy

        rad = atan2(dy, dx)
        ang = degrees(rad)

        self.right(self._closest_turn(ang))

    def distance(self, x, y):
        '''distance(x, y) # in pixels

        return the distance (in pixels) to the given coordinates
        '''
        cpos = self.ritem.pos()
        cx = cpos.x()
        cy = cpos.y()
        dx = x-cx
        dy = y-cy
        return hypot(dx, dy)

    def lineto(self, x, y=None):
        '''line(x, y) # in pixels

        Move directly to the given coordinates. Always draws a line,
            no matter the state of the pen before the call.
        '''
        if x != 'random':
            pen = self.pen
            self.pendown()
            self.toward(x, y)
            self.forward(self.distance(x, y))
            if not pen:
                self.penup()
        elif y != None:
            # passed in 'random' plus something else...
            # That can't be right
            raise ValueError("'random' must be passed alone.")
        else:
            xmin, ymin, xmax, ymax = self.viewcoords()
            x = random.randrange(int(xmin), int(xmax))
            y = random.randrange(int(ymin), int(ymax))
            self.lineto(x, y)

    def _write(self, text):
        font = QtGui.QFont('Arial', 22)
        item = self.gitem.scene().addSimpleText(text, font)
        item.setZValue(self._zvalue)
        Pynguin._zvalue += 1
        item.setPen(self.gitem.pen)
        item.setBrush(self.gitem.pen.color())
        x, y = self.gitem.x(), self.gitem.y()
        item.translate(x, y)
        item.rotate(self.gitem.ang)
        self.drawn_items.append(item)

    def write(self, text):
        '''write(text)

        Draw a text message at the current location.
        '''
        strtxt = str(text)
        self.qmove(self._write, (strtxt,))

    def dbg(self):
        'test function for drawing on to the background plane'
        scene = self.scene
        bgp = scene.bgp
        bgp.drawEllipse(QtCore.QRect(50, 100, 200, 300))
        view = scene.view

        # scroll the scene to force an update
        view.scrollContentsBy(0, 1)
        view.scrollContentsBy(0, -1)

    def _item_home(self, item):
        self._item_goto(item, QtCore.QPointF(0, 0))
        self._item_setangle(item, 0)

    def _gitem_home(self):
        self._item_home(self.gitem)

    def _gitem_track(self, track, pyn):
        if track:
            Pynguin._track_pynguin = pyn
        else:
            Pynguin._track_pynguin = None


        if hasattr(pyn, '_is_helper') and pyn._is_helper:
            # _track_main_pynguin gets set in mode.py
            pass
        else:
            if track and pyn is self.mw.pynguin:
                Pynguin._track_main_pynguin = True
            else:
                Pynguin._track_main_pynguin = False

        self.gitem._track()
        self.mw._sync_track(bool(Pynguin._track_main_pynguin))

    def track(self, track=True):
        self.qmove(self._gitem_track, (track, self))
    def notrack(self):
        self.track(False)

    def home(self):
        '''home()

        Move directly to the home location (0, 0) and turn to angle 0
        '''
        self._item_home(self.ritem)
        self._item_setangle(self.ritem, 0)
        self.qmove(self._item_home, (self.gitem,))
        self.qmove(self._gitem_new_line)
        self.qmove(self._gitem_setangle, (0,))
        self.mw.scene.view.centerOn(0, 0)
        self.mw._centerview()

    def _clear(self):
        for item in self.drawn_items:
            scene = item.scene()
            scene.removeItem(item)
        self.drawn_items = []
        self._gitem_new_line()

    def clear(self):
        self.qmove(self._clear)

    def _full_reset(self):
        #self._empty_move_queue()

        self._remove_other_pynguins()
        self.mw.setup_interpreter_locals()
        self.reset()

        self.qmove(self._clear_defunct_pynguins_later)

    def _clear_defunct_pynguins_later(self):
        self.mw._defunct_pynguins = self.mw._defunct_pynguins[-50:]
        logger.info('YS %s'%len(self.mw._defunct_pynguins))

    def reset(self, full=False):
        '''reset()

        Move to home location and angle and restore state
            to the initial values (pen, fill, etc).

        if full is True, also removes any added pynguins and clears out
            any pending pynguin movements. Also resets the pynguin
            functions that are pulled in to the interpreter namespace
            automatically.
        '''

        if full:
            if self is not self.mw.pynguin:
                self.promote()
                self.waitforit()

            for pyn in self.mw.pynguins:
                if pyn is not self and pyn.gitem is not None:
                    pyn.reset()
                    self.waitforit()

            self.qmove(self._full_reset)
            self.waitforit()

        else:
            settings = QtCore.QSettings()
            if self.avatar() == 'hidden':
                reset_forces_visible = settings.value('pynguin/reset_forces_visible', True, bool)
                if reset_forces_visible:
                    self.avatar('pynguin')

            self.clear()
            if self is self.mw.pynguin:
                self._set_bgcolor_to_default()
            self.label('')
            self.goto(0, 0)
            self.turnto(0)
            self.pendown()
            self.width(2)
            self._set_color_to_default()
            self.nofill()
            self._set_fillcolor_to_default()
            self.fillrule('winding')
            self.mw.zoom100()
            self.mw.scene.view.centerOn(0, 0)
            self.mw._centerview()
            logger.info('RWFI')
            self.waitforit()

    def _remove_other_pynguins(self):
        '''remove the graphical avatar items for all the pynguins
            other than the main one.
        '''
        pynguins = self.mw.pynguins
        if self in pynguins:
            pynguins.remove(self)

        while pynguins:
            pyn = pynguins.pop()
            pyn.defunct = True
            self.mw._defunct_pynguins.append(pyn)
            scene = pyn.gitem.scene()
            if scene is not None:
                scene.removeItem(pyn.gitem)

            #if hasattr(pyn.gitem, 'litem') and pyn.gitem.litem is not None:
                #liscene = pyn.gitem.litem.scene()
                #if liscene is not None:
                    #liscene.removeItem(pyn.gitem.litem)

            if hasattr(pyn, '_pyn'):
                _pyn = pyn._pyn
                scene = _pyn.gitem.scene()
                if scene is not None:
                    scene.removeItem(_pyn.gitem)
                #if hasattr(_pyn.gitem, 'litem') and _pyn.gitem.litem is not None:
                    #liscene = _pyn.gitem.litem.scene()
                    #if liscene is not None:
                        #liscene.removeItem(_pyn.gitem.litem)

        pynguins.append(self)

    def _pendown(self, down=True):
        self.gitem._pen = down
        self.mw._sync_pendown_menu(down)

    def penup(self):
        '''penup()

        Put the pen in the up (non-drawing) position.
        '''
        self.pen = self.ritem._pen = False
        self.qmove(self._pendown, (False,))
        self.qmove(self._gitem_new_line)

    def pendown(self):
        '''pendown()

        Put the pen in the down (drawing) position.
        '''
        self.pen = self.ritem._pen = True
        self.qmove(self._pendown)

    def _color(self, r=None, g=None, b=None, a=255):
        c = QtGui.QColor(r, g, b, a)
        self.gitem.pen.setColor(c)

    def color(self, r=None, g=None, b=None, a=None):
        '''color(red, green, blue) # 0-255 for each value
        color() # return the current color

        Set the line color for drawing. The color should be given as
            3 integers between 0 and 255, specifying the red, blue, and
            green components of the color.

        Uses the choose_color() function from the util module which
            also offers these options:

            Can also pass in just the name of a color, or the
                string 'random' for a randomly selected color or
                'rlight' for a random light color
                'rmedium' for a random medium color
                'rdark' for a random dark color
                'ralpha' for a random color with random alpha channel

        return the color being used for drawing -- makes getting
            randomly selected colors easier.
        '''
        if r is g is b is None:
            return self.ritem.color

        r, g, b, a = choose_color(r, g, b, a)
        self.ritem.color = (r, g, b, a)
        self.qmove(self._gitem_new_line)
        self.qmove(self._color, (r, g, b, a))

        return r, g, b, a

    def _set_color_to_default(self):
        settings = QtCore.QSettings()
        default = conf.default_color
        rgba = int(settings.value('pynguin/color', default))
        c = QtGui.QColor.fromRgba(rgba)
        r, g, b, a = c.getRgb()
        if self.ritem.color != (r, g, b, a):
            self.color(r, g, b, a)


    def bgcolor(self, r=None, g=None, b=None):
        settings = QtCore.QSettings()
        if r is g is b is None:
            color = self.scene.backgroundBrush().color()
            r, g, b, _ = color.getRgb()
            return r, g, b
        else:
            r, g, b, a = choose_color(r, g, b)
            if (r, g, b) != self.mw._bgcolor:
                self.mw._bgcolor = (r, g, b)
                ncolor = QtGui.QColor(r, g, b)
                brush = QtGui.QBrush(ncolor)
                self.mw.scene.setBackgroundBrush(brush)

    def _set_bgcolor_to_default(self):
        settings = QtCore.QSettings()
        default = conf.default_bgcolor
        c = settings.value('view/bgcolor', default)
        self.bgcolor(c)

    def _colorat(self):
        scene = self.scene
        x, y = int(self.x), int(self.y)
        items = scene.items(QtCore.QPointF(x, y))

        current_line = self.gitem._current_line
        if current_line in items:
            items.remove(current_line)

        pyns = self.mw.pynguins[:]
        hiding = []
        while pyns:
            pyn = pyns.pop()

            gitem = pyn.gitem
            item = gitem.item

            if item in items:
                items.remove(item)
            if gitem in items:
                items.remove(gitem)
                gitem.hide()
                hiding.append(gitem)

            if hasattr(pyn, '_pyn'):
                pyns.append(pyn._pyn)

        if items:
            src = QtCore.QRectF(x, y, 1, 1)
            sz = QtCore.QSize(1, 1)
            self._i = i = QtGui.QImage(sz, QtGui.QImage.Format_RGB32)
            p = QtGui.QPainter(i)
            irf = QtCore.QRectF(0, 0, 1, 1)
            if current_line is not None:
                current_line.hide()
            scene.render(p, irf, src)
            if current_line is not None:
                current_line.show()
            rgb = i.pixel(0, 0)
            color = QtGui.QColor(rgb)

            settings = QtCore.QSettings()
            bgcolor = settings.value('view/bgcolor')
            if color != bgcolor:
                self._colorat_return = color.name()
            else:
                self._colorat_return = util.NOTHING
        else:
            self._colorat_return = util.NOTHING

        for gitem in hiding:
            gitem.show()

    def colorat(self):
        self._colorat_return = None
        self.qmove(self._colorat)
        self.waitforit()
        rval = self._colorat_return
        self._colorat_return = None
        if rval is util.NOTHING:
            return None
        else:
            return rval

    def _width(self, w):
        self.gitem.pen.setWidth(w)

    def width(self, w=None):
        '''width(w) # in pixels
        width() # return the current width

        Set the line width for drawing.
        '''
        if w is None:
            return self.ritem.penwidth
        else:
            self.ritem.penwidth = w
            self.qmove(self._gitem_new_line)
            self.qmove(self._width, (w,))

    def _fillcolor(self, r=None, g=None, b=None, a=None):
        '''fillcolor(red, green, blue, alpha) # 0-255 for each value
        fillcolor() # return the current fill color

        Set the fill color for drawing. The color should be given as
            3 integers between 0 and 255, specifying the red, blue, and
            green components of the color. Optionally, an alpha value
            can also be given to set transparency.
        '''
        color = QtGui.QColor.fromRgb(r, g, b, a)
        self.gitem.brush.setColor(color)
        self._gitem_new_line()

    def fillcolor(self, r=None, g=None, b=None, a=None):
        '''fillcolor(r, g, b, a)

        Set the color to be used for filling drawn shapes.

        return the color being used for filling -- makes getting
            randomly selected colors easier.
        '''
        r, g, b, a = choose_color(r, g, b, a)
        if r is g is b is None:
            return self.ritem.fillcolor
        self.ritem.fillcolor = (r, g, b, a)
        self.qmove(self._fillcolor, (r, g, b, a))

        return r, g, b, a

    def _set_fillcolor_to_default(self):
        settings = QtCore.QSettings()
        default = conf.default_fillcolor
        rgba = int(settings.value('pynguin/fillcolor', default))
        c = QtGui.QColor.fromRgba(rgba)
        r, g, b, a = c.getRgb()
        if self.ritem.fillcolor != (r, g, b, a):
            self.fillcolor(r, g, b, a)

    def _gitem_fillmode(self, start):
        if start:
            self.gitem._fillmode = True
            self._gitem_new_line()
            if self is self.mw.pynguin:
                self.mw._sync_fill_menu('fill')
        else:
            self.gitem._fillmode = False
            self._gitem_new_line()
            if self is self.mw.pynguin:
                self.mw._sync_fill_menu('nofill')

    def fill(self, color=None, rule=None):
        '''fill()

        Go in to fill mode. Anything drawn will be filled until
            nofill() is called.

        Set the fill color by passing in an (r, g, b) tuple, or
            pass color='random' for a random fill color.

        If a fill color is specified (color is not None)
            return the color that is being used as fill color.

        Change the fill rule by passing in either
            'winding' (default) or 'oddeven'
        '''
        if color is not None:
            c = choose_color(color)
            self.fillcolor(*c)

        if rule is not None:
            self.fillrule(rule)

        self.ritem._fillmode = True
        self.qmove(self._gitem_fillmode, (True,))

        if color is not None:
            return self.fillcolor()

    def nofill(self):
        '''nofill()

        Turn off fill mode.
        '''
        self.ritem._fillmode = False
        self.qmove(self._gitem_fillmode, (False,))

    def _gitem_fillrule(self, rule):
        self.gitem._fillrule = rule
    def fillrule(self, rule):
        '''fillrule(method) # 'oddeven' or 'winding'

        Set the fill method to OddEvenFill or WindingFill.
        '''
        if rule == 'oddeven':
            fr = QtCore.Qt.OddEvenFill
        elif rule == 'winding':
            fr = QtCore.Qt.WindingFill
        else:
            raise ValueError
        self.ritem._fillrule = fr
        self.qmove(self._gitem_fillrule, (fr,))

    def _setImageid(self, imageid, filepath=None, sync=None):
        self.ogitem = self.gitem
        ogitem = self.ogitem
        if ogitem is None:
            return
        pos = ogitem.pos()
        ang = ogitem.ang

        if self is self.mw.pynguin and sync is None:
            do_sync = True
        elif sync:
            do_sync = True
        else:
            do_sync = False

        if filepath is None:
            # one of the built-in avatars
            rend = self.mw.rend
        else:
            # custom avatar
            fmt = QtGui.QImageReader.imageFormat(filepath)

            if fmt == 'svg':
                # custom svg avatar
                rend = self.mw.svgrenderer.getrend(filepath)
            else:
                # custom non-svg avatar
                rend = None
                pm = QtGui.QPixmap(filepath)
                w, h = pm.width(), pm.height()
                if w > h:
                    pm = pm.scaledToWidth(250)
                    h = pm.height()
                    ho = (250 - h) / 2
                    wo = 0
                elif h > w:
                    pm = pm.scaledToHeight(250)
                    w = pm.width()
                    wo = (250 - w) / 2
                    ho = 0
                else:
                    rend = pm

                if rend is None:
                    rend = QtGui.QPixmap(250, 250)
                    rend.fill(QtCore.Qt.transparent)
                    painter = QtGui.QPainter(rend)
                    painter.drawPixmap(wo, ho, pm)

        pen = ogitem.pen
        brush = ogitem.brush
        scene = ogitem.scene()
        gitem = PynguinGraphicsItem(rend, imageid, self)
        gitem.setZValue(ogitem.zValue())
        gitem.setPos(pos)
        gitem.ang = ang
        gitem.pen = pen
        gitem._pen = ogitem._pen
        gitem.brush = brush
        gitem._fillmode = ogitem._fillmode
        gitem._fillrule = ogitem._fillrule
        gitem._current_line = ogitem._current_line
        #gitem.litem = ogitem.litem
        scene.removeItem(ogitem)
        scene.addItem(gitem)
        self.gitem = gitem
        gitem.set_transform()
        if do_sync:
            if imageid is None:
                _, imageid = os.path.split(filepath)
            self.mw._sync_avatar_menu(imageid, filepath)
    def setImageid(self, imageid, filepath=None, sync=None):
        '''change the visible (avatar) image'''
        self._imageid = imageid
        self.qmove(self._setImageid, (imageid, filepath, sync))
        if self.name:
            name = self.name
            self.label('')
            self.label(name)
    def avatar(self, imageid=None, filepath=None, sync=None):
        '''set or return the pynguin's avatar image

            Some avatars are built in and can be selected by passing
                imageid only. Choices are 'pynguin', 'turtle', 'arrow',
                'robot', and 'hidden'

            An avatar can be set using an svg or png image also.

            For a png, pass the path to the file only.

            For an svg, pass the file path, and the svg id both.

            Normally, when the pynguin being modified is the main
            pynguin, you want the window menu to be synced with the
            selected avatar, however, for the special modes (ModeLogo
            and ModeTurtle) which are composed to 2 pynguins, the
            sync=False option is available so that only the visible
            pynguin avatar will be synced with the menu. Also, sync=True
            is available to force sync when updating the visible
            pynguin even though it is not actually the primary.
        '''

        if filepath is not None and imageid is not None:
            self.setImageid(imageid, filepath, sync)
        elif filepath is not None and imageid is None:
            # load from non-svg image
            self.setImageid(imageid, filepath, sync)
        elif imageid is not None:
            avatars = list(self.mw.avatars.values())
            if imageid in avatars:
                self.setImageid(imageid, None, sync)
            else:
                msg = 'Avatar "%s" not available. Avatars available are: %s' % (imageid, ', '.join(avatars))
                raise ValueError(msg)
        else:
            return self._imageid

    def _speed(self, s):
        self.drawspeed = 2 * s
        self.turnspeed = 4 * s

    def speed(self, s):
        '''Set speed of animation for all pynguins.

        Choices are: 'slow', 'medium', 'fast', 'instant'
        '''

        choices = { 'slow': 5,
                    'medium': 10,
                    'fast': 20,
                    'instant': 0}
        choice = choices.get(s)

        if choice is None:
            raise ValueError("Speed choices are %s" % list(choices.keys()))

        else:
            if hasattr(self, '_pyn'):
                pyn = self._pyn
            else:
                pyn = self

            self.qmove(pyn._speed, (choice,))

            if self is self.mw.pynguin:
                settings = QtCore.QSettings()
                settings.setValue('pynguin/speed', s)
                self.mw.sync_speed_menu(choice)

    def _circle(self, crect):
        '''instant circle'''
        gitem = self.gitem
        self._gitem_new_line()
        scene = gitem.scene()
        circle = scene.addEllipse(crect, gitem.pen)
        if gitem._fillmode:
            circle.setBrush(gitem.brush)
        circle.setZValue(self._zvalue)
        Pynguin._zvalue += 1
        self.drawn_items.append(circle)
        gitem.expand()

    def _extend_circle(self, crect, distance, signal=None):
        '''individual steps for animated circle drawing
        '''
        gitem = self.gitem
        scene = gitem.scene()
        cl = gitem._current_line
        if cl is not None and signal=='finish':
            # circle complete.
            # replace the circle drawn using line segments
            # with a real ellipse item
            self.drawn_items.pop()
            scene.removeItem(cl)
            self._gitem_new_line()
            circle = scene.addEllipse(crect, self.gitem.pen)
            if gitem._fillmode:
                circle.setBrush(gitem.brush)
            circle.setZValue(self._zvalue)
            Pynguin._zvalue += 1
            self.drawn_items.append(circle)
        elif signal == 'start':
            # first segment
            self._item_left(gitem, -2)
            self._item_forward(gitem, distance)
        else:
            # continue drawing
            self._item_left(gitem, -4)
            self._item_forward(gitem, distance)

    def _slowcircle(self, crect, r, center):
        '''Animated circle drawing
        '''
        self.qmove(self._gitem_new_line)
        pos0 = self.ritem.pos()
        ang0 = self.ritem.ang
        if center:
            pen = self.pen
            self.penup()
            self._gitem_breakup_move(r)
            self._gitem_breakup_turn(-90)
            if pen:
                self.pendown()

        circumference = 2 * PI * r
        self.qmove(self._extend_circle, (crect, circumference/90., 'start'))
        for n in range(2, 90):
            self.qmove(self._extend_circle, (crect, circumference/90.))
            if 40-self.drawspeed:
                self.qmove(self._qdelay, (100*(40-self.drawspeed),))
        self.qmove(self._extend_circle, (crect, 0, 'finish'))

        if center:
            self.penup()
            self._gitem_breakup_turn(-90)
            self._gitem_breakup_move(r)
            self._gitem_breakup_turn(180)
            if pen:
                self.pendown()
        self.qmove(self._gitem_goto, (pos0,))
        self.qmove(self._gitem_setangle, (ang0,))

    def circle(self, r, center=False):
        '''circle(radius, center) # radius in pixels

        Draw a circle of radius r.

        If center is True, the current position will be the center of
            the circle. Otherwise, the circle will be drawn with the
            current position and rotation being a tangent to the circle.
        '''

        ritem = self.ritem
        cpt = ritem.pos()

        if not center:
            radians = (((PI*2)/360.) * ritem.ang)
            tocenter = radians + PI/2

            dx = r * cos(tocenter)
            dy = r * sin(tocenter)

            tocpt = QtCore.QPointF(dx, dy)
            cpt = cpt + tocpt

        ul = cpt - QtCore.QPointF(r, r)
        sz = QtCore.QSizeF(2*r, 2*r)

        crect = QtCore.QRectF(ul, sz)

        self._check_drawspeed_change()
        if self.drawspeed == 0:
            # instant circles
            if self.pen:
                self.qmove(self._circle, (crect,))
        else:
            # animated circles
            self._slowcircle(crect, r, center)

    def square(self, side, center=False):
        '''square(side, center=False) # length of side in pixels

        Draw a square with sides of length side.

        If center is True, the current position will be the center
            of the square. The sides will still be parallel or
            perpendicular to the current direction.
        '''

        pen = self.pen
        if center:
            self.penup()
            half_side = float(side)/2
            self.forward(half_side)
            self.left(90)
            self.forward(half_side)
            self.left(90)
            if pen:
                self.pendown()

        for side_n in range(4):
            self.forward(side)
            self.left(90)

        if center:
            self.penup()
            self.left(90)
            self.forward(half_side)
            self.right(90)
            self.forward(half_side)
            self.right(180)

        if pen:
            self.pendown()

    def _viewrect(self):
        view = self.scene.view
        viewportrect = view.viewport().geometry()
        tl = viewportrect.topLeft()
        br = viewportrect.bottomRight()
        tlt = view.mapToScene(tl)
        brt = view.mapToScene(br)
        return QtCore.QRectF(tlt, brt)

    def onscreen(self):
        '''onscreen()

        return True if the pynguin is in the visible area, or
            False if it is outside the visible area.
        '''
        pos = self.ritem.pos()
        return pos in self._viewrect()

    def viewcoords(self, floats=False):
        '''viewcoords()

        return the coordinates of the boundaries of the visible area.
            By default, returns the coordinates as integer values.

        Get the coords with code like this:
            xmin, xmax, ymin, ymax = viewcoords()

        To get float values instead of integers, pass in the optional
            parameter floats=True
        '''
        self.mw.interpretereditor.spin(5)
        coords = self._viewrect().getCoords()
        if not floats:
            coords = [int(c) for c in coords]
        return coords

    def onclick(self, x, y):
        '''This method will be called automatically when the user
            right-clicks the mouse in the viewable area.

        To override this method, define a new function called onclick(x, y)
            and it will be inserted for automatic calling.

        Alternately, create a Pynguin subclass with its own
            onclick(self, x, y) method.
        '''
        pass

    def _stamp(self, x, y, imageid=None):
        gitem = self.gitem
        if imageid is None:
            imageid = gitem.imageid
            rend = gitem.rend
        else:
            rend = self.mw.rend
        item = PynguinGraphicsItem(rend, imageid, None)
        item.ang = gitem.ang
        item.setPos(gitem.pos())
        item.setZValue(self._zvalue)
        Pynguin._zvalue += 1
        gitem.scene().addItem(item)
        self.drawn_items.append(item)
    def stamp(self, imageid=None):
        '''stamp()
        stamp(imagename) # 'pynguin', 'robot', 'turtle', or 'arrow'

        Leave a stamp of the current pynguin image at the current location.

        Can also stamp the other images by including the image name.
        '''
        pos = self.ritem.pos()
        x, y = pos.x(), pos.y()
        self.qmove(self._stamp, (x, y, imageid))

    def _gitem_setlabel(self, name):
        self.gitem.setlabel(name)

    def _setname(self, name):
        if name != self._name:
            self._name = name
            self.qmove(self._gitem_setlabel, (name,))
    def _getname(self):
        return self._name
    name = property(_getname, _setname)

    def label(self, name=None):
        if name is None:
            return self.name
        else:
            self.name = name

    def mode(self, mname=None):
        '''Convert this pynguin to a different coordinate/angle modes.

        Does not convert in place. Returns a new object of the new type.

        The primary pynguin is automatically re-bound to p and to pynguin
        in the interpreter, but in scripts it is difficult to ensure that
        you are getting the new object. It is best to bind the returned
        pynguin and use that for following commands.


        Modes available:
                            angle 0  |     pos angles     | pos x | pos y
                            -------  | ------------------ | ----- | -----
            pynguin:         east    |     clockwise      | east  | south
            (default)                |                    |       |
                                     |                    |       |
            logo:            north   |     clockwise      | east  | north
                                     |                    |       |
            turtle:          east    | counter-clockwise  | east  | north
            (python turtle           |                    |       |
                default)
        '''

        if mname is None:
            return self._modename

        from . import mode
        if mname not in mode.modes:
            raise TypeError('Mode "%s" unknown' % mname)

        av = self.avatar()
        name = self.name
        is_main_pynguin = self is self.mw.pynguin

        p = self.mw.new_pynguin(mname, show_cmd=False)
        self._set_mode_replace(self, p)
        p.remove(self)
        p.avatar(av)
        p.color(self.color())
        p.width(self.width())

        if is_main_pynguin:
            p.promote(p)
            settings = QtCore.QSettings()
            settings.setValue('pynguin/mode', mname)
            self.mw._sync_mode_menu(mname)

            if Pynguin._track_main_pynguin:
                p.track()

        p._modename = mname
        if name:
            p.label(name)

        self.qmove = self._qmove_after_mode_switch

        return p

    def _qmove_after_mode_switch(*args, **kw):
        raise RuntimeError('Attempting to use expired object after change of mode. Use the object returned by mode() instead.')

    def _set_mode_replace(self, opyn, npyn):
        '''After changing mode, put the newly created pynguin
            back where the original pynguin was.
        '''
        if hasattr(opyn, '_pyn'):
            x, y = opyn._pyn.xy()
            ang = opyn._pyn.h()
        else:
            x, y = opyn.xy()
            ang = opyn.h()

        if hasattr(npyn, '_pyn'):
            x, y = npyn._xy_rsl(x, y)
            ang = npyn._ang_rsl(ang)

        npyn.goto(x, y)
        npyn.turnto(ang)



class RItem(object):
    '''Used to track the "real" state of the pynguin (as opposed
        to the visible state which may be delayed for animation
        at slower speeds)

        RItem uses the same API as GraphicsItem
    '''
    def __init__(self):
        self.setPos(QtCore.QPointF(0, 0))
        self._pen = True
        self.ang = 0
        self.color = (255, 255, 255)
        self.fillcolor = (100, 220, 110)
        self.penwidth = 2

    def pos(self):
        return self._pos

    def setPos(self, pos):
        self._pos = pos

    def set_transform(self):
        pass

    def rotate(self, deg):
        'turn clockwise from current angle by deg degrees'
        self.ang += deg


class GraphicsItem(QtGui.QGraphicsItem):
    def __init__(self, parent=None):
        QtGui.QGraphicsItem.__init__(self, parent)
        self._pen = True
        self.ang = 0

    def set_transform(self):
        pass

    def rotate(self, deg):
        'turn clockwise from current angle by deg degrees'
        self.ang += deg

    def paint(self, painter, option, widget):
        pass


class PynguinGraphicsItem(GraphicsItem):
    def __init__(self, rend, imageid, pynguin):
        cx, cy = 125, 125
        scale = 0.20
        cxs, cys = cx*scale, cy*scale
        cpt = QtCore.QPointF(cxs, cys)
        self.cpt = cpt
        self.scale = scale
        self.rend = rend
        self.pynguin = pynguin

        GraphicsItem.__init__(self)

        self.setImageid(imageid)

        self.litem = None # label item

        self.set_transform()

        self.pen = QtGui.QPen(QtCore.Qt.white)
        self.pen.setWidth(2)

        color = QtGui.QColor(100, 220, 110)
        self.brush = QtGui.QBrush(color)
        self._fillmode = False
        self._fillrule = QtCore.Qt.WindingFill

        self._notrack = False # set when dragging to prevent crash

        self.ready = False

    def setlabel(self, text):
        litem = self.litem
        if litem is not None:
            #item = litem.item
            #iscene = item.scene()
            #if iscene is not None:
                #iscene.removeItem(item)
            #else:
                #logger.info('LII No Scene')
            #liscene = litem.scene()
            #if liscene is not None:
                #liscene.removeItem(litem)
            #else:
                #logger.info('LI No Scene')
            litem._settext(text)
        else:
            self.litem = PynguinLabelItem(self)
            scene = self.scene()
            #if self.litem in scene.items():
                #logger.info('IN SCENE')
            #else:
                #scene.addItem(self.litem)
            scene.addItem(self.litem)
            self.litem._settext(text)
        self.set_transform()

    def setPos(self, pos):
        GraphicsItem.setPos(self, pos)
        self.set_transform()
        self.expand(pos)
        self._track()

    def expand(self, pos=None):
        '''Check if the scene needs to expand for the drawn items.

        pass in pos=None to check all drawn items even if it is
            likely that the current position would not cause a
            need to expand the scene. (Used currently for the
            quick-draw circle which never actually moves the
            pynguin, but which may add a circle that needs to
            expand the scene rect).
        '''
        scene = self.scene()
        if scene is not None:
            scenerect = scene.sceneRect()
            if pos is None or not scenerect.contains(pos):
                itemrect = scene.itemsBoundingRect()
                newrect = itemrect.united(scenerect)
                scene.setSceneRect(newrect)

    def _track(self):
        'center the view on the pynguin'

        if Pynguin._track_pynguin and not self._notrack:
            pynguin = self.pynguin
            trackpyn = Pynguin._track_pynguin
            scene = self.scene()
            if pynguin is trackpyn and scene is not None:
                scene.view.ensureVisible(self)
                pynguin.mw._centerview()

    def set_transform(self):
        cpt = self.cpt
        cx, cy = cpt.x(), cpt.y()

        ang = self.ang

        trans = QtGui.QTransform()
        trans.translate(-cx, -cy)
        trans.translate(cx, cy).rotate(ang).translate(-cx, -cy)
        trans.scale(self.scale, self.scale)

        if self.litem is not None:
            self.litem.set_transform()

        self.setTransform(trans)

    def rotate(self, deg):
        'turn clockwise from current angle by deg degrees'
        self.ang += deg
        self.set_transform()

    def setImageid(self, imageid):
        self.imageid = imageid
        if imageid is not None:
            self.item = QtSvg.QGraphicsSvgItem(self)
            self.item.setSharedRenderer(self.rend)
            self.item.setElementId(imageid)
            irect = self.rend.boundsOnElement(imageid)
            w, h = irect.width(), irect.height()
            ws, hs = w*self.scale, h*self.scale
            self.cpt = QtCore.QPointF(ws/2, hs/2)
        else:
            # non-svg image
            self.item = QtGui.QGraphicsPixmapItem(self.rend, self)

    def boundingRect(self):
        return self.item.boundingRect()

    def mousePressEvent(self, ev):
        button = ev.button()
        if button == QtCore.Qt.LeftButton:
            ev.accept()

    def mouseMoveEvent(self, ev):
        buttons = ev.buttons()
        if buttons & QtCore.Qt.LeftButton:
            ev.accept()
            pynguin = self.pynguin
            if pynguin is not None:
                self._notrack = True
                pos = ev.lastScenePos()
                x, y = pos.x(), pos.y()
                pynguin.goto(x, y)
                self._notrack = False

            ps = pynguin.mw.pynguins
            if pynguin not in ps and pynguin._is_helper not in ps:
                # There is a visible pynguin onscreen which the user
                # has grabbed and moved, but that pynguin is not in
                # the pynguin list for some reason. Add it back in.
                ps.append(pynguin)

    def mouseReleaseEvent(self, ev):
        self._track()


class PynguinLabelItem(QtGui.QGraphicsTextItem):
    def __init__(self, parent):
        self.parent = parent
        offx, offy = 0, 40
        scale = 5.0
        offxs, offys = offx*scale, offy*scale
        offpt = QtCore.QPointF(offxs, offys)
        self.offpt = offpt
        self.scale = scale
        self._text = ''
        self._zvalue = 99999

        QtGui.QGraphicsTextItem.__init__(self, parent)

        self._setup()
        self.set_transform()

    def _setup(self):
        self._settext('')
        self.setZValue(self._zvalue)

    def _settext(self, text):
        self._text = text
        self.setPlainText(text)
        self.setZValue(self._zvalue)
        br = self.boundingRect()
        self.cpt = br.center()
        offpt = self.offpt
        offx, offy = offpt.x(), offpt.y()
        pcpt = self.parent.cpt
        px, py = pcpt.x(), pcpt.y()
        self.setTransformOriginPoint(-px, -py)

    def set_transform(self):
        pcpt = self.parent.cpt
        pcx, pcy = pcpt.x(), pcpt.y()
        offpt = self.offpt
        offx, offy = offpt.x(), offpt.y()
        cpt = self.cpt
        cx, cy = cpt.x(), cpt.y()
        ang = self.parent.ang
        trans = QtGui.QTransform()
        pscale = self.parent.scale
        pscale1 = 1/pscale
        trans.translate(pscale1*pcx, pscale1*pcy)
        trans.rotate(-ang)
        scale = self.scale
        trans.translate(-scale*cx, -scale*cy)
        trans.translate(offx, offy)
        trans.scale(self.scale, self.scale)
        self.setTransform(trans)
