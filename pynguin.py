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


import Queue
from random import randrange
from math import atan2, degrees, radians, hypot, cos, sin, pi
PI = pi

from PyQt4 import QtCore, QtGui, QtSvg

from util import sign
from conf import uidir


pynguin_functions = ['forward', 'fd', 'backward', 'bk', 'left',
                        'lt', 'right', 'rt', 'reset', 'home',
                        'penup', 'pendown', 'color', 'width',
                        'circle', 'fill', 'nofill', 'fillcolor',
                        'begin_fill', 'end_fill', 'goto', 'turnto',
                        'write', 'toward', 'distance', 'lineto',
                        'onscreen','stamp']
interpreter_protect = ['p', 'new_pynguin', 'PI', 'history']


class Pynguin(object):
    def __init__(self, scene, pos, ang, rend):
        self.scene = scene
        self.gitem = PynguinGraphicsItem(rend, 'pynguin') #display only
        self.scene.addItem(self.gitem)
        self.ritem = RItem() #real location, angle, etc.
        self.gitem.setZValue(9999999)
        self.drawn_items = []
        self._drawspeed_pending = None
        self._turnspeed_pending = None
        self.drawspeed = 1
        self.turnspeed = 4
        self.gitem._drawn = self.drawspeed
        self.gitem._turned = self.turnspeed
        self.gitem._current_line = None
        self.ritem._drawn = self.drawspeed
        self.ritem._turned = self.turnspeed
        self.delay = 50
        self._moves = Queue.Queue(50) # max number of items in queue
        self.pendown()
        self._checktime = QtCore.QTime()
        self._checktime.start()
        self._zvalue = 0
        self.fillrule('winding')

    def _set_item_pos(self, item, pos):
        item.setPos(pos)

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

    def _process_moves(self):
        '''regular timer tick to make sure graphics are being updated'''
        self._r_process_moves()
        if self.drawspeed == 0:
            delay = 0
        else:
            delay = self.delay
        QtCore.QTimer.singleShot(delay, self._process_moves)

    def _sync_items(self):
        '''Sometimes, after running code is interrupted (like by Ctrl-C)
            the actual position (ritem.pos) and displayed position
            (gitem.pos) will be out of sync.

            This method can be called to synchronize the ritem to the
            position and rotation of the display.

        '''

        self.ritem.setPos(self.gitem.pos())
        self.ritem.ang = self.gitem.ang

    def _r_process_moves(self):
        '''apply the queued commands for the graphical display item
            This must be done from the main thread
        '''
        drawspeed = self.drawspeed
        delay = self.delay
        etime = self._checktime.elapsed()
        if not drawspeed or etime > delay:
            while True:
                try:
                    move, args = self._moves.get(block=False)
                except Queue.Empty:
                    break
                else:
                    move(*args)

                #print 'dt', self.gitem._drawn, self.gitem._turned

                if not drawspeed:
                    delay -= 1
                    if delay < 0:
                        QtGui.QApplication.processEvents(QtCore.QEventLoop.AllEvents)
                        delay = 5 * self.delay
                elif self.gitem._drawn > 0 and self.gitem._turned > 0:
                    continue
                else:
                    self.gitem._drawn = self.drawspeed
                    self.gitem._turned = self.turnspeed
                    break

                if self.drawspeed:
                    break

            QtGui.QApplication.processEvents(QtCore.QEventLoop.AllEvents)
            self._checktime.restart()

    def _item_forward(self, item, distance, draw=True):
        '''Move item ahead distance. If draw is True, also add a line
            to the item's scene. draw should only be true for gitem
        '''
        if not distance and item is self.gitem:
            self.gitem._current_line = None
            return

        item._drawn -= abs(distance)

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
                self._zvalue += 1
                self.drawn_items.append(line)
                self.gitem._current_line = line
            else:
                ppath = cl.path()
                plast = ppath.currentPosition()
                if p2 != plast:
                    ppath.lineTo(p2)
                    cl.setPath(ppath)

    def _gitem_move(self, distance):
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

            self.qmove(self._item_forward, (self.gitem, step,))

            QtGui.QApplication.processEvents(QtCore.QEventLoop.AllEvents)

    def _check_drawspeed_change(self):
        if self._drawspeed_pending is not None:
            self.drawspeed = self._drawspeed_pending
            self._drawspeed_pending = None
            self.turnspeed = self._turnspeed_pending
            self._turnspeed_pending = None

    def qmove(self, func, args=None):
        '''queue up a command for later application'''

        if args is None:
            args = ()
        while 1:
            try:
                self._moves.put_nowait((func, args))
            except Queue.Full:
                QtGui.QApplication.processEvents(QtCore.QEventLoop.AllEvents)
            else:
                break

    def forward(self, distance):
        self._item_forward(self.ritem, distance, False)
        self._gitem_move(distance)
    fd = forward

    def backward(self, distance):
        self.forward(-distance)
    bk = backward

    def _item_left(self, item, degrees):
        item.rotate(-degrees)

    def _item_left(self, item, degrees):
        item._turned -= (abs(degrees))
        item.rotate(-degrees)
    def _gitem_turn(self, degrees):
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

            self.qmove(self._item_left, (self.gitem, step,))

    def left(self, degrees):
        self._item_left(self.ritem, degrees)
        self._gitem_turn(degrees)
    lt = left

    def right(self, degrees):
        self.left(-degrees)
    rt = right

    def _item_goto(self, item, pos):
        item.setPos(pos)
        item.set_transform()

    def goto(self, x, y):
        pos = QtCore.QPointF(x, y)
        self._item_goto(self.ritem, pos)
        self.qmove(self._item_forward, (self.gitem, 0))
        self.qmove(self._item_goto, (self.gitem, pos))

    def _item_setangle(self, item, ang):
        item.ang = ang
        item.set_transform()

    def turnto(self, ang):
        ang0 = self.ritem.ang
        turn = abs(ang - ang0)
        if ang0 < ang:
            self.right(turn)
        else:
            self.left(turn)

    def toward(self, x, y):
        '''turn toward the given coordinates'''
        cpos = self.ritem.pos()
        cx = cpos.x()
        cy = cpos.y()
        dx = x-cx
        dy = y-cy

        rad = atan2(dy, dx)
        ang = degrees(rad)

        self.turnto(ang)

    def distance(self, x, y):
        '''return the distance to the given coordinates'''
        cpos = self.ritem.pos()
        cx = cpos.x()
        cy = cpos.y()
        dx = x-cx
        dy = y-cy
        return hypot(dx, dy)

    def lineto(self, x, y):
        self.toward(x, y)
        self.forward(self.distance(x, y))

    def _write(self, text):
        font = QtGui.QFont('Arial', 22)
        item = self.gitem.scene().addSimpleText(text, font)
        item.setPen(self.gitem.pen)
        item.setBrush(self.gitem.pen.color())
        x, y = self.gitem.x(), self.gitem.y()
        item.translate(x, y)
        item.rotate(self.gitem.ang)
        self.drawn_items.append(item)

    def write(self, text):
        self.qmove(self._write, (text,))

    def _item_home(self, item):
        self._item_goto(item, QtCore.QPointF(0, 0))
        self._item_setangle(item, 0)

    def home(self):
        self._item_home(self.ritem)
        self._item_setangle(self.ritem, 0)
        self.qmove(self._item_home, (self.gitem,))
        self.qmove(self._item_forward, (self.gitem, 0))
        self.qmove(self._item_setangle, (self.gitem, 0,))

    def _empty_move_queue(self):
        while 1:
            try:
                move, args = self._moves.get(block=False)
            except Queue.Empty:
                break

    def _reset(self):
        for item in self.drawn_items:
            scene = item.scene()
            scene.removeItem(item)
        self.drawn_items = []
        if self._moves:
            self._empty_move_queue()
        self.qmove(self._item_home, (self.gitem,))
        self.qmove(self._item_forward, (self.gitem, 0))
        self.qmove(self._item_setangle, (self.gitem, 0,))
        self.qmove(self._gitem_fillmode, (0,))

    def reset(self):
        self.qmove(self._reset)
        self._item_home(self.ritem)
        self.nofill()

    def _pendown(self, down=True):
        self.gitem._pen = down

    def penup(self):
        self.pen = self.ritem._pen = False
        self.qmove(self._pendown, (False,))
        self.qmove(self._item_forward, (self.gitem, 0))

    def pendown(self):
        self.pen = self.ritem._pen = True
        self.qmove(self._pendown)

    def _color(self, r=None, g=None, b=None):
        self.gitem.pen.setColor(QtGui.QColor.fromRgb(r, g, b))

    def color(self, r=None, g=None, b=None):
        if r == 'random':
            r, g, b = [randrange(256) for cc in range(3)]
        elif r is g is b is None:
            return self.ritem.color

        self.ritem.color = (r, g, b)
        self.qmove(self._item_forward, (self.gitem, 0))
        self.qmove(self._color, (r, g, b))

    def _width(self, w):
        self.gitem.pen.setWidth(w)

    def width(self, w=None):
        if w is None:
            return self.ritem.penwidth
        else:
            self.ritem.penwidth = w
            self.qmove(self._item_forward, (self.gitem, 0))
            self.qmove(self._width, (w,))

    def _fillcolor(self, r=None, g=None, b=None):
        color = QtGui.QColor.fromRgb(r, g, b)
        self.gitem.brush.setColor(color)
        self._item_forward(self.gitem, 0)

    def fillcolor(self, r=None, g=None, b=None):
        if r == 'random':
            r, g, b = [randrange(256) for cc in range(3)]
        elif r is g is b is None:
            return self.ritem.fillcolor

        self.ritem.fillcolor = (r, g, b)
        self.qmove(self._fillcolor, (r, g, b))

    def _gitem_fillmode(self, start):
        if start:
            self.gitem._fillmode = True
            self._item_forward(self.gitem, 0)
        else:
            self.gitem._fillmode = False
            self._item_forward(self.gitem, 0)

    def fill(self):
        '''go in to fill mode. Anything drawn will be filled until
            nofill() is called.
        '''
        self.ritem._fillmode = True
        self.qmove(self._gitem_fillmode, (True,))

    def nofill(self):
        '''turn off fill mode'''
        self.ritem._fillmode = False
        self.qmove(self._gitem_fillmode, (False,))

    def begin_fill(self):
        self.fill()

    def end_fill(self):
        self.nofill()

    def _gitem_fillrule(self, rule):
        self.gitem._fillrule = rule
    def fillrule(self, rule):
        if rule == 'oddeven':
            fr = QtCore.Qt.OddEvenFill
        elif rule == 'winding':
            fr = QtCore.Qt.WindingFill
        self.ritem._fillrule = fr
        self.qmove(self._gitem_fillrule, (fr,))

    def setImageid(self, imageid):
        '''change the visible (avatar) image'''
        ogitem = self.gitem
        pos = ogitem.pos()
        ang = ogitem.ang
        rend = ogitem.rend
        pen = ogitem.pen
        scene = ogitem.scene()
        gitem = PynguinGraphicsItem(rend, imageid)
        gitem.setZValue(9999999)
        gitem.setPos(pos)
        gitem.ang = ang
        gitem.pen = pen
        gitem._pen = ogitem._pen
        gitem._drawn = ogitem._drawn
        gitem._turned = ogitem._turned
        gitem._current_line = ogitem._current_line
        scene.removeItem(ogitem)
        scene.addItem(gitem)
        self.gitem = gitem
        gitem.set_transform()

    def _circle(self, crect):
        '''instant circle'''
        gitem = self.gitem
        self._item_forward(gitem, 0)
        scene = gitem.scene()
        circle = scene.addEllipse(crect, gitem.pen)
        if gitem._fillmode:
            circle.setBrush(gitem.brush)
        circle.setZValue(self._zvalue)
        self._zvalue += 1
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
            self._item_forward(gitem, 0)
            circle = scene.addEllipse(crect, self.gitem.pen)
            if gitem._fillmode:
                circle.setBrush(gitem.brush)
            circle.setZValue(self._zvalue)
            self._zvalue += 1
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
        self.qmove(self._item_forward, (self.gitem, 0))
        pos0 = self.ritem.pos()
        ang0 = self.ritem.ang
        sangle = self.gitem.ang
        if center:
            pen = self.pen
            self.penup()
            self._gitem_move(r)
            self._gitem_turn(-90)
            if pen:
                self.pendown()
            sangle += 90

        circumference = 2 * PI * r
        for n in range(1, 90):
            self.qmove(self._extend_circle, (crect, circumference/90.))
        self.qmove(self._extend_circle, (crect, 0))

        if center:
            self.penup()
            self._gitem_turn(-90)
            self._gitem_move(r)
            self._gitem_turn(180)
            if pen:
                self.pendown()
        self.qmove(self._item_goto, (self.gitem, pos0,))
        self.qmove(self._item_setangle, (self.gitem, ang0,))

    def circle(self, r, center=False):
        '''Draw a circle of radius r.

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

    def viewrect(self):
        view = self.scene.view
        viewportrect = view.viewport().geometry()
        tl = viewportrect.topLeft()
        br = viewportrect.bottomRight()
        tlt = view.mapToScene(tl)
        brt = view.mapToScene(br)
        return QtCore.QRectF(tlt, brt)

    def onscreen(self):
        pos = self.ritem.pos()
        return pos in self.viewrect()

    def onclick(self, x, y):
        self.goto(x, y)

    def _stamp(self, x, y, imageid=None):
        gitem = self.gitem
        if imageid is None:
            imageid = gitem.imageid
        item = PynguinGraphicsItem(gitem.rend, imageid)
        item.ang = gitem.ang
        item.setPos(gitem.pos())
        item.setZValue(self._zvalue)
        self._zvalue += 1
        gitem.scene().addItem(item)
        self.drawn_items.append(item)
    def stamp(self, imageid=None):
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

    def set_rotation(self, ang):
        'directly set rotation (in radians)'
        self.ang = -(180/PI)*ang

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

    def set_rotation(self, ang):
        'directly set rotation (in radians)'
        self.ang = -(180/PI)*ang

    def rotate(self, deg):
        'turn clockwise from current angle by deg degrees'
        self.ang += deg

    def paint(self, painter, option, widget):
        pass


class PynguinGraphicsItem(GraphicsItem):
    def __init__(self, rend, imageid):
        cx, cy = 125, 125
        scale = 0.20
        cxs, cys = cx*scale, cy*scale
        cpt = QtCore.QPointF(cxs, cys)
        self.cpt = cpt
        self.scale = scale
        self.rend = rend

        GraphicsItem.__init__(self)

        self.setImageid(imageid)

        self.set_transform()

        self.pen = QtGui.QPen(QtCore.Qt.white)
        self.pen.setWidth(2)

        color = QtGui.QColor(100, 220, 110)
        self.brush = QtGui.QBrush(color)
        self._fillmode = False

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

    def set_rotation(self, ang):
        'directly set rotation (in radians)'
        self.ang = -(180/PI)*ang
        self.set_transform()

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
