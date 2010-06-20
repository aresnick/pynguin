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


import Queue
from random import randrange
from math import atan2, degrees, radians, hypot, cos, sin, pi
PI = pi
import random
import logging
logger = logging.getLogger('PynguinLogger')

from PyQt4 import QtCore, QtGui, QtSvg

from util import sign, choose_color
from conf import uidir


pynguin_functions = ['forward', 'fd', 'backward', 'bk', 'left',
                        'lt', 'right', 'rt', 'reset', 'home',
                        'penup', 'pendown', 'color', 'width',
                        'circle', 'fill', 'nofill', 'fillcolor',
                        'goto', 'xy', 'xyh', 'h', 'turnto', 'clear',
                        'write', 'toward', 'distance', 'lineto',
                        'onscreen', 'viewcoords', 'stamp']
interpreter_protect = ['p', 'pynguin', 'Pynguin', 'pynguins', 'PI', 'history']

class TooManyPynguins(RuntimeError):
    pass

class Pynguin(object):
    ControlC = False

    min_delay = 1
    delay = 50

    _moves = Queue.Queue(50) # max number of items in queue
    _checktime = QtCore.QTime()
    _checktime.start()

    _drawspeed_pending = None
    _turnspeed_pending = None
    drawspeed = 1
    turnspeed = 4
    _drawn = drawspeed
    _turned = turnspeed

    _zvalue = 0

    respond_to_mouse_click = True

    mw = None # set by MainWindow before any Pynguin get instantiated
    rend = None # set by MainWindow before any Pynguin get instantiated

    def __init__(self, pos=(0, 0), ang=0):
        self.scene = self.mw.scene
        self.ritem = RItem() #real location, angle, etc.
        self.gitem = None # Gets set up later in the main thread
        self.drawn_items = []
        self._setup()

    def _setup(self):
        self.mw.pynguins.append(self)

        # enforce maximum of 150 pynguins
        npyn = len(self.mw.pynguins)
        if npyn > 150:
            self.mw.pynguins.remove(self)
            raise TooManyPynguins('Exceeded maximum of 150 pynguins.')

        self.mw.setSpeed()

        if self.mw.pynguin is None:
            self._gitem_setup()
            self.mw.startTimer(self.delay)

        else:
            self.qmove(self._gitem_setup)
            while self.gitem is None or not self.gitem.ready:
                if self.ControlC:
                    raise KeyboardInterrupt

    def _gitem_setup(self):
        self.gitem = PynguinGraphicsItem(self.rend, 'pynguin', self) #display only
        self.imageid = 'pynguin'
        self.scene.addItem(self.gitem)
        Pynguin._zvalue += 1
        self.gitem.setZValue(9999999 - self._zvalue)
        self.pendown()
        self.fillrule('winding')
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

    def xy(self):
        return self.x, self.y

    def xyh(self):
        return self.x, self.y, self.heading

    def h(self):
        return self.heading

    @classmethod
    def _process_moves(cls):
        '''regular timer tick to make sure graphics are being updated'''
        #logging.debug('_pm')
        cls._r_process_moves()
        if cls.drawspeed == 0:
            delay = cls.min_delay
        else:
            delay = cls.delay

    @classmethod
    def _empty_move_queue(cls):
        while 1:
            #logging.debug('________________emq')
            try:
                #logging.debug('1')
                #logging.debug('________________1emq %s' % cls._moves.qsize())
                move, args = cls._moves.get(block=False)
                #logging.debug('2')
                QtGui.QApplication.processEvents(QtCore.QEventLoop.AllEvents)
                #logging.debug('________________2emq %s' % cls._moves.qsize())
            except Queue.Empty:
                #logging.debug('EMPTY')
                break

            #logging.debug('4')
        #logging.debug('5')

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
    def _r_process_moves(cls):
        '''apply the queued commands for the graphical display item
            This must be done from the main thread
        '''
        drawspeed = cls.drawspeed
        delay = cls.delay
        etime = cls._checktime.elapsed()
        if cls.ControlC:
            cls._empty_move_queue()
            #logging.debug('CCnomove')

        elif not drawspeed or etime > delay:
            ied = cls.mw.interpretereditor
            while True:
                #logging.debug('_____rpm')
                try:
                    move, args = cls._moves.get(block=False)
                except Queue.Empty:
                    break
                else:

                    try:
                        move(*args)
                    except Exception, e:
                        ied.write(unicode(e))
                        ied.write('\n')
                        if ied.cmdthread is not None:
                            ied.cmdthread.terminate()
                            ied.cmdthread = None
                        cls._empty_move_queue()
                        ied.write('>>> ')

                #print 'dt', self.gitem._drawn, self.gitem._turned

                if not drawspeed:
                    delay -= 1
                    if delay < 0:
                        QtGui.QApplication.processEvents(QtCore.QEventLoop.AllEvents)
                        delay = cls.min_delay
                        break
                elif cls._drawn > 0 and cls._turned > 0:
                    #logging.debug('dt %s %s' % (cls._drawn, cls._turned))
                    continue
                else:
                    cls._drawn = cls.drawspeed
                    cls._turned = cls.turnspeed
                    break

                if cls.drawspeed:
                    break

            cls._checktime.restart()

        QtGui.QApplication.processEvents(QtCore.QEventLoop.AllEvents)

    def _gitem_new_line(self):
        self.gitem._current_line = None

    def _item_forward(self, item, distance, draw=True):
        '''Move item ahead distance. If draw is True, also add a line
            to the item's scene. draw should only be true for gitem
        '''
        Pynguin._drawn -= abs(distance)

        ang = item.ang
        rad = ang * (PI / 180)
        dx = distance * cos(rad)
        dy = distance * sin(rad)

        p1 = item.pos()

        x = p1.x()+dx
        y = p1.y()+dy
        p2 = QtCore.QPointF(x, y)
        item.setPos(p2)

        if draw:
            scene = self.mw.scene
            if (x > scene._width / 2 or
                    x < -scene._width / 2 or
                    y > scene._width / 2 or
                    y > scene._width / 2):
                initialrect = QtCore.QRectF(-300,-300,600,600)
                itemrect = scene.itemsBoundingRect()
                scene.setSceneRect(itemrect.united(initialrect))

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

        if self.ControlC:
            raise KeyboardInterrupt

        if args is None:
            args = ()

        thread = QtCore.QThread.currentThread()
        if thread == self.mw._mainthread:
            # Coming from main thread. Could be an onclick handler
            #   or a menu-item action
            func(*args)
            return

        while 1:
            try:
                #logging.debug('qb')
                self._moves.put_nowait((func, args))
                #logging.debug('qp')
            except Queue.Full:
                #logging.debug('Full')
                QtGui.QApplication.processEvents(QtCore.QEventLoop.AllEvents)
            else:
                break

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
        Pynguin._turned -= (abs(degrees))
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
            raise ValueError, "'random' must be passed alone."
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
            raise ValueError, "'random' must be passed alone."
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
        strtxt = unicode(text)
        self.qmove(self._write, (strtxt,))

    def _item_home(self, item):
        self._item_goto(item, QtCore.QPointF(0, 0))
        self._item_setangle(item, 0)

    def _gitem_home(self):
        self._item_home(self.gitem)

    def home(self):
        '''home()

        Move directly to the home location (0, 0) and turn to angle 0
        '''
        self._item_home(self.ritem)
        self._item_setangle(self.ritem, 0)
        self.qmove(self._item_home, (self.gitem,))
        self.qmove(self._gitem_new_line)
        self.qmove(self._gitem_setangle, (0,))

    def _clear(self):
        for item in self.drawn_items:
            self.scene.removeItem(item)
        self.drawn_items = []
        self._gitem_new_line()

    def clear(self):
        self.qmove(self._clear)

    def _reset(self):
        if self is self.mw.pynguin and self._moves:
            self._empty_move_queue()
        self._clear()
        self._gitem_home()
        self._gitem_new_line()
        self._gitem_setangle(0)
        self._gitem_fillmode(0)
        self._width(2)
        self._color(255, 255, 255)
        self._pendown()
        self._fillcolor(100, 220, 110)
        self._gitem_fillrule(QtCore.Qt.WindingFill)
        self._setImageid('pynguin')

        if self is self.mw.pynguin:
            self._remove_other_pynguins()

    def reset(self):
        '''reset()

        Move to home location and angle and restore state
            to the initial values (pen, fill, etc).

        Also removes any added pynguins.
        '''
        if self is self.mw.pynguin:
            for pyn in self.mw.pynguins:
                if pyn is not self:
                    if pyn.gitem is not None:
                        pyn.reset()

        self.qmove(self._reset)
        self._item_home(self.ritem)
        self.nofill()
        self.width(2)
        self.color(255, 255, 255)
        self.pendown()
        self.fillcolor(100, 220, 110)
        self.fillrule('winding')

    def _remove_other_pynguins(self):
        pynguins = self.mw.pynguins
        pynguins.remove(self)
        while pynguins:
            pyn = pynguins.pop()
            self.scene.removeItem(pyn.gitem)
        pynguins.append(self)

    def _pendown(self, down=True):
        self.gitem._pen = down

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

    def _color(self, r=None, g=None, b=None):
        c = QtGui.QColor(r, g, b)
        self.gitem.pen.setColor(c)

    def color(self, r=None, g=None, b=None):
        '''color(red, green, blue) # 0-255 for each value
        color() # return the current color

        Set the line color for drawing. The color should be given as
            3 integers between 0 and 255, specifying the red, blue, and
            green components of the color.

        return the color being used for drawing -- makes getting
            randomly selected colors easier.
        '''
        r, g, b = choose_color(r, g, b)
        if r is g is b is None:
            return self.ritem.color
        self.ritem.color = (r, g, b)
        self.qmove(self._gitem_new_line)
        self.qmove(self._color, (r, g, b))
        return r, g, b

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

    def _fillcolor(self, r=None, g=None, b=None):
        '''fillcolor(red, green, blue) # 0-255 for each value
        fillcolor() # return the current fill color

        Set the fill color for drawing. The color should be given as
            3 integers between 0 and 255, specifying the red, blue, and
            green components of the color.
        '''
        color = QtGui.QColor.fromRgb(r, g, b)
        self.gitem.brush.setColor(color)
        self._gitem_new_line()

    def fillcolor(self, r=None, g=None, b=None):
        '''fillcolor(r, g, b)

        Set the color to be used for filling drawn shapes.

        return the color being used for filling -- makes getting
            randomly selected colors easier.
        '''
        r, g, b = choose_color(r, g, b)
        if r is g is b is None:
            return self.ritem.fillcolor
        self.ritem.fillcolor = (r, g, b)
        self.qmove(self._fillcolor, (r, g, b))
        return r, g, b

    def _gitem_fillmode(self, start):
        if start:
            self.gitem._fillmode = True
            self._gitem_new_line()
        else:
            self.gitem._fillmode = False
            self._gitem_new_line()

    def fill(self, color=None, rule=None):
        '''fill()

        Go in to fill mode. Anything drawn will be filled until
            nofill() is called.

        Set the fill color by passing in an (r, g, b) tuple.

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
        self.ritem._fillrule = fr
        self.qmove(self._gitem_fillrule, (fr,))

    def _setImageid(self, imageid):
        ogitem = self.gitem
        pos = ogitem.pos()
        ang = ogitem.ang
        rend = ogitem.rend
        pen = ogitem.pen
        scene = ogitem.scene()
        gitem = PynguinGraphicsItem(rend, imageid, self)
        gitem.setZValue(ogitem.zValue())
        gitem.setPos(pos)
        gitem.ang = ang
        gitem.pen = pen
        gitem._pen = ogitem._pen
        gitem._fillrule = ogitem._fillrule
        gitem._current_line = ogitem._current_line
        scene.removeItem(ogitem)
        scene.addItem(gitem)
        self.gitem = gitem
        gitem.set_transform()
    def setImageid(self, imageid):
        '''change the visible (avatar) image'''
        self._imageid = imageid
        self.qmove(self._setImageid, (imageid,))

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

    def _extend_circle(self, crect, distance):
        '''individual steps for animated circle drawing
        '''
        gitem = self.gitem
        scene = gitem.scene()
        cl = gitem._current_line
        if cl is not None and not distance:
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
        elif cl is None:
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
        for n in range(1, 90):
            self.qmove(self._extend_circle, (crect, circumference/90.))
        self.qmove(self._extend_circle, (crect, 0))

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

    def viewcoords(self):
        '''viewcoords()

        return the coordinates of the boundaries of the visible area.

        Get the coords with code like this:
            xmin, xmax, ymin, ymax = viewcoords()
        '''
        return self._viewrect().getCoords()

    def onclick(self, x, y):
        '''This method will be called automatically when the user clicks
            the mouse in the viewable area.

        To override this method, define a new function called onclick(x, y)
            and it will be inserted for automatic calling.
        '''
        self.goto(x, y)

    def _stamp(self, x, y, imageid=None):
        gitem = self.gitem
        if imageid is None:
            imageid = gitem.imageid
        item = PynguinGraphicsItem(gitem.rend, imageid, None)
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


class RItem(object):
    '''Used to track the "real" state of the pynguin (as opposed
        to the visible state which may be delayed for animation
        at slower speeds

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
    def __init__(self):
        QtGui.QGraphicsItem.__init__(self)
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

        self.set_transform()

        self.pen = QtGui.QPen(QtCore.Qt.white)
        self.pen.setWidth(2)

        color = QtGui.QColor(100, 220, 110)
        self.brush = QtGui.QBrush(color)
        self._fillmode = False
        self._fillrule = QtCore.Qt.WindingFill

        self.ready = False

    def setPos(self, pos):
        GraphicsItem.setPos(self, pos)
        self.set_transform()

    def set_transform(self):
        cpt = self.cpt
        cx, cy = cpt.x(), cpt.y()
        #pt = self.pos
        pt = self.pos() - cpt
        x, y = pt.x(), pt.y()

        ang = self.ang

        trans = QtGui.QTransform()
        trans.translate(-cx, -cy)
        trans.translate(cx, cy).rotate(ang).translate(-cx, -cy)
        trans.scale(self.scale, self.scale)
        self.setTransform(trans)

    def rotate(self, deg):
        'turn clockwise from current angle by deg degrees'
        self.ang += deg
        self.set_transform()

    def setImageid(self, imageid):
        self.imageid = imageid
        self.item = QtSvg.QGraphicsSvgItem(self)
        self.item.setSharedRenderer(self.rend)
        self.item.setElementId(imageid)

    def boundingRect(self):
        return self.item.boundingRect()

    def mousePressEvent(self, ev):
        button = ev.button()
        if button == QtCore.Qt.LeftButton:
            ev.accept()

    def mouseMoveEvent(self, ev):
        buttons = ev.buttons()
        if buttons & QtCore.Qt.LeftButton:
            pynguin = self.pynguin
            if pynguin is not None:
                pos = ev.lastScenePos()
                pynguin.pos = pos
                pynguin._gitem_new_line()
