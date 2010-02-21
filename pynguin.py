import os
import sys
import math
PI = math.pi
import code
import Queue
import zipfile

from PyQt4 import QtCore, QtGui, QtSvg, uic
from PyQt4.Qt import QFrame, QWidget, QHBoxLayout, QPainter

from editor import HighlightedTextEdit



pynguin_functions = ['forward', 'fd', 'backward', 'bk', 'left',
                        'lt', 'right', 'rt', 'reset', 'home',
                        'penup', 'pendown', 'color', 'width', ]

uidir = 'data/ui'
uifile = 'pynguin.ui'
uipath = os.path.join(uidir, uifile)
MWClass, _ = uic.loadUiType(uipath)

def sign(x):
    return cmp(x, 0)

def getrend(app):
    filename = 'pynguin.svg'
    filepath = os.path.join('data/images', filename)
    fp = QtCore.QString(filepath)
    rend = QtSvg.QSvgRenderer(fp, app)
    return rend

class MainWindow(QtGui.QMainWindow):
    def __init__(self, app):
        self.app = app
        self.paused = False
        self.rend = getrend(self.app)

        self._fdir = None
        self._filepath = None
        self._modified = False

        QtGui.QMainWindow.__init__(self)
        self.ui = MWClass()
        self.ui.setupUi(self)

        self.scene = Scene()
        view = self.ui.view
        view.setScene(self.scene)
        self.scene.view = view
        view.show()

        self.pynguin = Pynguin((0, 0), 0, self.rend)
        self.scene.addItem(self.pynguin.gitem)
        trans = QtGui.QTransform()
        #trans.scale(0.15, 0.15)
        trans.scale(1, 1)
        self.scene.view.setTransform(trans)
        view.centerOn(self.pynguin.gitem)

        self.editor = CodeArea(self.ui.mselect)
        hbox = QHBoxLayout(self.ui.edframe)
        hbox.setSpacing(0)
        hbox.setMargin(0)
        #hbox.addWidget(self.number_bar)
        hbox.addWidget(self.editor)

        self.interpretereditor = Interpreter()
        hbox = QHBoxLayout(self.ui.interpreterframe)
        hbox.setSpacing(0)
        hbox.setMargin(0)
        #hbox.addWidget(self.number_bar)
        hbox.addWidget(self.interpretereditor)
        ilocals = {'p': self.pynguin}
        for fname in pynguin_functions:
            function = getattr(self.pynguin, fname)
            ilocals[fname] = function
        self.interpreter_locals = ilocals
        self.interpreter = code.InteractiveConsole(self.interpreter_locals)
        self.interpretereditor.interpreter = self.interpreter

        self.interpretereditor.setFocus()

        self.viewgroup = QtGui.QActionGroup(self)
        self.viewgroup.addAction(self.ui.actionPynguin)
        self.viewgroup.addAction(self.ui.actionArrow)
        self.viewgroup.addAction(self.ui.actionRobot)
        self.viewgroup.addAction(self.ui.actionHidden)
        self.viewgroup.setExclusive(True)
        self.viewgroup.triggered.connect(self.setImage)

        self.pengroup = QtGui.QActionGroup(self)
        self.pengroup.addAction(self.ui.actionPenUp)
        self.pengroup.addAction(self.ui.actionPenDown)
        self.pengroup.setExclusive(True)
        self.pengroup.triggered.connect(self.setPen)

        self.speedgroup = QtGui.QActionGroup(self)
        self.speedgroup.addAction(self.ui.actionSlow)
        self.speedgroup.addAction(self.ui.actionMedium)
        self.speedgroup.addAction(self.ui.actionFast)
        self.speedgroup.addAction(self.ui.actionInstant)
        self.speedgroup.setExclusive(True)
        self.speedgroup.triggered.connect(self.setSpeed)
        self._setSpeed(2)

        #QtCore.QTimer.singleShot(100, self.ropy)

        #self.t = TryThread(self.pynguin)
        #self.t.start()

    def ropy(self):
        self.pynguin.left(1)
        self.pynguin.forward(15)
        QtCore.QTimer.singleShot(5, self.ropy)

    def closeEvent(self, ev=None):
        QtGui.qApp.quit()

    def new(self):
        pass

    def _savestate(self):
        self.editor.savecurrent()

        r, ext = os.path.splitext(self._filepath)
        if ext != '.pyn':
            ext = '.pyn'
        self._filepath = r + ext
        z = zipfile.ZipFile(self._filepath, 'w')

        for n, (ename, efile) in enumerate(self.editor.documents.items()):
            arcname = '##%5s##__%s' % (n, ename)
            z.writestr(arcname, efile)

        historyname = '@@history@@'
        history = '\n'.join(self.interpretereditor.history)
        z.writestr(historyname, history)

        z.close()

    def save(self):
        if self._filepath is None:
            return self.saveas()
        else:
            self._savestate()

    def saveas(self):
        if self._fdir is None:
            fdir = QtCore.QString(os.path.abspath(os.path.curdir))
        else:
            fdir = self._fdir

        fp = str(QtGui.QFileDialog.getSaveFileName(self, 'Save As', fdir))
        if fp:
            self._filepath = fp
            self._fdir, _ = os.path.split(fp)
        else:
            return

        self._savestate()

    def open(self):
        if self._fdir is None:
            fdir = QtCore.QString(os.path.abspath(os.path.curdir))
        else:
            fdir = self._fdir

        fp = str(QtGui.QFileDialog.getOpenFileName(self, 'Open file', fdir, 'Text files (*.pyn)'))
        if fp:
            self._filepath = fp
            self._fdir, _ = os.path.split(fp)

            z = zipfile.ZipFile(fp, 'r')
            for ename in z.namelist():
                fo = z.open(ename, 'rU')
                data = fo.read()
                if ename.startswith('##'):
                    hdr = ename[0:9]
                    if hdr.startswith('##') and hdr.endswith('##'):
                        title = ename[11:]
                        self.editor.add(data)
                elif ename.startswith('@@history@@'):
                    history = data.split('\n')
                    self.interpretereditor.history = history

    def newdoc(self):
        self.editor.new()
        self.editor.setFocus()

    def changedoc(self, idx):
        docname = str(self.ui.mselect.itemText(idx))
        self.editor.switchto(docname)
        self.editor.setFocus()

    def testcode(self):
        self.editor.savecurrent()
        docname = str(self.ui.mselect.currentText())
        code = str(self.editor.documents[docname])
        exec code in self.interpreter_locals
        line0 = code.split('\n')[0]
        if line0.startswith('def ') and line0.endswith(':'):
            firstparen = line0.find('(')
            if firstparen > -1:
                funcname = line0[4:firstparen]
                func = self.interpreter_locals.get(funcname, None)
                if func is not None:
                    func()

    def setPenColor(self):
        icolor = self.pynguin.gitem.pen.brush().color()
        ncolor = QtGui.QColorDialog.getColor(icolor, self)
        if ncolor.isValid():
            self.pynguin.gitem.pen.setColor(ncolor)
            r, g, b, a = ncolor.getRgb()
            cmd = 'color(%s, %s, %s)' % (r, g, b)
            self.interpretereditor.addcmd(cmd)

    def setPenWidth(self):
        iwidth = self.pynguin.gitem.pen.width()
        uifile = 'penwidth.ui'
        uipath = os.path.join(uidir, uifile)
        DClass, _ = uic.loadUiType(uipath)
        dc = DClass()
        d = QtGui.QDialog(self)
        d.ui = DClass()
        dc.setupUi(d)
        dc.thewid.setValue(iwidth)
        d.exec_()
        nwidth = dc.thewid.value()
        self.pynguin.width(nwidth)
        cmd = 'width(%s)' % nwidth
        self.interpretereditor.addcmd(cmd)

    def setPen(self, ev):
        if ev == self.ui.actionPenUp:
            self.pynguin.penup()
            self.interpretereditor.addcmd('penup()')
        else:
            self.pynguin.pendown()
            self.interpretereditor.addcmd('pendown()')

    def setImage(self, ev):
        choices = {self.ui.actionPynguin: 'pynguin',
                    self.ui.actionArrow: 'arrow',
                    self.ui.actionRobot: 'robot',
                    self.ui.actionHidden: 'hidden',}
        self.pynguin.setImageid(choices[ev])

    def _setSpeed(self, speed):
        self.pynguin.drawspeed = 2 * speed
        self.pynguin.turnspeed = 4 * speed
    def setSpeed(self, ev):
        choice = {self.ui.actionSlow: 5,
                    self.ui.actionMedium: 10,
                    self.ui.actionFast: 20,
                    self.ui.actionInstant: 0,}
        speed = choice[ev]
        self._setSpeed(speed)


class TryThread(QtCore.QThread):
    def __init__(self, pynguin):
        QtCore.QThread.__init__(self)
        self.pynguin = pynguin

    def run(self):
        for x in range(10):
            self.pynguin.forward(10)
            time.sleep(1)

class CodeArea(HighlightedTextEdit):
    def __init__(self, mselect):
        HighlightedTextEdit.__init__(self)
        self.mselect = mselect
        self.documents = {}
        self.title = ''
        self.settitle('Untitled')

    def keyPressEvent(self, ev):
        HighlightedTextEdit.keyPressEvent(self, ev)
        fblk = self._doc.firstBlock()
        txt = str(fblk.text())
        self.settitle(txt)

    def settitle(self, txt):
        if txt.startswith('def ') and txt.endswith(':'):
            title = txt[4:-1]
        elif txt=='NEW' or txt=='':
            title = 'Untitled'
        else:
            title = txt

        if title != self.title:
            if txt != 'NEW':
                idx = self.mselect.findText(self.title)
                if idx > -1:
                    self.mselect.removeItem(idx)
            self.title = title
            self.mselect.addItem(title)

        idx = self.mselect.count()
        self.mselect.setCurrentIndex(idx-1)

    def savecurrent(self):
        title = self.title
        text = str(self._doc.toPlainText())
        if title != 'Untitled' or text:
            self.documents[title] = text

    def new(self):
        self.savecurrent()
        self._doc.setPlainText('')
        self.settitle('NEW')

    def switchto(self, docname):
        self.savecurrent()
        self._doc.setPlainText(self.documents[docname])
        self.title = docname

    def add(self, txt):
        self.new()
        self._doc.setPlainText(txt)
        title = txt.split('\n')[0]
        self.settitle(title)
        self.savecurrent()


class CmdThread(QtCore.QThread):
    def __init__(self, ed, txt):
        QtCore.QThread.__init__(self)
        self.ed = ed
        self.txt = txt
    def run(self):
        ed = self.ed
        sys.stdout = ed
        sys.stderr = ed
        ed.needmore = ed.interpreter.push(self.txt)
        sys.stdout = ed.save_stdout
        sys.stderr = ed.save_stderr

class Interpreter(HighlightedTextEdit):
    def __init__(self):
        HighlightedTextEdit.__init__(self)
        self.history = []
        self._outputq = []
        self.historyp = -1

        self.save_stdout = sys.stdout
        self.save_stdin = sys.stdin
        self.save_stderr = sys.stderr

        self._check_control_key = False

        self.setWordWrapMode(QtGui.QTextOption.WordWrap)

        self.cmdthread = None
        self.controlC = False

        QtCore.QTimer.singleShot(10, self.writeoutputq)

        self.write('>>> ')


    def addcmd(self, cmd):
        self.insertPlainText(cmd)
        self.write('>>> ')
        self.history.append(cmd)

    def write(self, text):
        if text:
            self._outputq.append(text)

    def writeoutputq(self):
        while self._outputq:
            text = self._outputq.pop(0)
            self.insertPlainText(text)
            QtCore.QTimer.singleShot(100, self.scrolldown)
        QtCore.QTimer.singleShot(10, self.writeoutputq)

    def keyPressEvent(self, ev):
        k = ev.key()

        Tab = QtCore.Qt.Key_Tab
        Backtab = QtCore.Qt.Key_Backtab
        Backspace = QtCore.Qt.Key_Backspace
        Left = QtCore.Qt.Key_Left
        Return = QtCore.Qt.Key_Return
        Up = QtCore.Qt.Key_Up
        Down = QtCore.Qt.Key_Down
        Control = QtCore.Qt.Key_Control
        U = QtCore.Qt.Key_U
        C = QtCore.Qt.Key_C


        lblk = self._doc.lastBlock()
        cpos = self.textCursor().position()
        cblk = self._doc.findBlock(cpos)
        cblkpos = cblk.position()

        passthru = True

        if k == Return:
            cpos = self.textCursor().position()
            cblk = self._doc.findBlock(cpos)
            pos = cblk.position()
            blk = self._doc.findBlockByNumber(pos)
            blk = blk.previous()
            if not blk.text():
                blk = self._doc.firstBlock()

            txt = str(blk.text()[4:]).rstrip()
            if txt:
                if self.history and not self.history[-1]:
                    del self.history[-1]
                self.history.append(txt)
            self.historyp = -1

            self.append('')

            if self.cmdthread is None:
                self.cmdthread = CmdThread(self, txt)
                self.cmdthread.start()
                while not self.cmdthread.wait(0) and not self.controlC:
                    QtGui.QApplication.processEvents(QtCore.QEventLoop.AllEvents)
                self.cmdthread = None
                if self.controlC:
                    self.append('')
                    self.controlC = False
                    self.needmore = False
                    self.interpreter.resetbuffer()
                    sys.stdout = self.save_stdout
                    sys.stderr = self.save_stderr

                if not self.needmore:
                    self.write('>>> ')
                else:
                    self.write('... ')

                passthru = False
            else:
                passthru = True

        elif k in (Backspace, Left):
            lblk = self._doc.lastBlock()
            lpos = lblk.position()
            llpos = lblk.position() + lblk.length() - 1

            cpos = self.textCursor().position()
            cblk = self._doc.findBlock(cpos)
            cblkpos = cblk.position()

            print cpos, cblkpos

            if cpos <= lpos + 4:
                passthru = False
            else:
                passthru = True

        elif k in (Up, Down):
            self.scrolldown()

            cpos = self.textCursor().position()
            cblk = self._doc.findBlock(cpos)
            pos = cblk.position()

            txt = str(cblk.text()[4:]).strip()

            if not self.history:
                QtGui.QApplication.beep()

            else:
                changeline = True
                addthisline = False

                lenhist = len(self.history)

                if k==Up and self.historyp==-1:
                    addthisline = True

                if k==Up and lenhist==1:
                    self.historyp -= 1
                elif k==Up and self.historyp <= -lenhist:
                    QtGui.QApplication.beep()
                    changeline = False
                elif k==Up:
                    self.historyp -= 1
                elif k==Down and self.historyp >= -1:
                    QtGui.QApplication.beep()
                    changeline = False
                elif k==Down:
                    self.historyp += 1

                if addthisline:
                    self.history.append(txt)

                if changeline:
                    txt = self.history[self.historyp]
                    endpos = pos + cblk.length() - 1

                    if self.historyp == -1:
                        del self.history[-1]

                    curs = self.textCursor()
                    curs.setPosition(pos+4, 0)
                    curs.setPosition(endpos, 1)
                    curs.removeSelectedText()

                    self.insertPlainText(txt)

            passthru = False

        elif k == Control:
            self._check_control_key = True

        elif self._check_control_key and k==U:
            #erase from cursor to beginning of line
            self.erasetostart()

        elif self._check_control_key and k==C:
            #send keyboard interrupt
            if self.cmdthread is not None and self.cmdthread.isRunning():
                self.controlC = True

        self.scrolldown()

        if passthru:
            HighlightedTextEdit.keyPressEvent(self, ev)

    def scrolldown(self):
        cpos = self.textCursor().position()
        cblk = self._doc.findBlock(cpos)
        lblk = self._doc.lastBlock()
        if cblk != lblk:
            lblk = self._doc.lastBlock()
            lpos = lblk.position() + lblk.length() - 1
            curs = self.textCursor()
            curs.setPosition(lpos, 0)
            self.setTextCursor(curs)

        vbar = self.verticalScrollBar()
        vbar.setValue(vbar.maximum())

    def keyReleaseEvent(self, ev):
        k = ev.key()
        Control = QtCore.Qt.Key_Control
        if k == Control:
            self._check_control_key = False


    def mousePressEvent(self, ev):
        curs = self.cursorForPosition(ev.pos())
        col = curs.columnNumber()
        cpos = curs.position()
        blk = curs.block()
        #blklen = blk.length()
        blktext = str(blk.text())
        promptblk = blktext.startswith('>>>') or blktext.startswith('...')
        if promptblk and col < 4:
            curs.setPosition(cpos + 4-col)
            self.setTextCursor(curs)
        else:
            HighlightedTextEdit.mousePressEvent(self, ev)

    def erasetostart(self):
        cpos = self.textCursor().position()
        cblk = self._doc.findBlock(cpos)
        pos = cblk.position()
        endpos = pos + cblk.length() - 1

        curs = self.textCursor()
        curs.setPosition(pos+4, 0)
        curs.setPosition(endpos, 1)
        curs.removeSelectedText()


class Scene(QtGui.QGraphicsScene):
    def __init__(self):
        QtGui.QGraphicsScene.__init__(self)
        self.setSceneRect(-300, -300, 600, 600)
        color = QtGui.QColor(130, 130, 160)
        brush = QtGui.QBrush(color)
        self.setBackgroundBrush(brush)



class Pynguin(object):
    def __init__(self, pos, ang, rend):
        self.gitem = PynguinGraphicsItem(pos, ang, rend, 'pynguin')
        self.drawn_items = []
        self.drawspeed = 1
        self.turnspeed = 4
        self.delay = 40
        self.pendown()
        self._moves = Queue.Queue(50)
        QtCore.QTimer.singleShot(self.delay, self._process_moves)

    def _process_moves(self):
        try:
            move, args = self._moves.get(block=False)
        except Queue.Empty:
            pass
        else:
            move(*args)

        if self.drawspeed == 0:
            delay = 0
        else:
            delay = self.delay
        QtCore.QTimer.singleShot(delay, self._process_moves)

    def _forward(self, distance):
        gitem = self.gitem
        ang = gitem.ang
        rad = ang * (PI / 180)
        dx = distance * math.cos(rad)
        dy = distance * math.sin(rad)

        p0 = QtCore.QPointF(self.gitem.pos)

        x = gitem.pos.x()+dx
        y = gitem.pos.y()+dy
        gitem.setpos((x, y))

        p1 = QtCore.QPointF(self.gitem.pos)

        if self._pen:
            line = gitem.scene().addLine(QtCore.QLineF(p0, p1), gitem.pen)
            line.setFlag(QtGui.QGraphicsItem.ItemStacksBehindParent)
            self.drawn_items.append(line)

    def _move(self, distance):
        drawspeed = self.drawspeed
        if distance >= 0:
            perstep = drawspeed
        else:
            perstep = -drawspeed

        adistance = abs(distance)
        d = 0
        n = 0
        while d < adistance:
            if perstep == 0:
                step = distance
                d = adistance
            elif d + drawspeed > adistance:
                step = sign(perstep) * (adistance - d)
            else:
                step = perstep
            n += 1
            d += drawspeed

            while 1:
                try:
                    self._moves.put_nowait((self._forward, (step,)))
                except Queue.Full:
                    QtGui.QApplication.processEvents(QtCore.QEventLoop.AllEvents)
                else:
                    break
            QtGui.QApplication.processEvents(QtCore.QEventLoop.AllEvents)

    def forward(self, distance):
        self._move(distance)
    fd = forward

    def backward(self, distance):
        self.forward(-distance)
    bk = backward

    def _left(self, degrees):
        self.gitem.rotate(-degrees)
    def _turn(self, degrees):
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

            while 1:
                try:
                    self._moves.put_nowait((self._left, (step,)))
                except Queue.Full:
                    QtGui.QApplication.processEvents(QtCore.QEventLoop.AllEvents)
                else:
                    break
            QtGui.QApplication.processEvents(QtCore.QEventLoop.AllEvents)

    def left(self, degrees):
        self._turn(degrees)
    lt = left

    def right(self, degrees):
        self.left(-degrees)
    rt = right

    def goto(self, pos):
        self.gitem.setpos(pos)

    def home(self):
        self.gitem.ang = 0
        self.goto((0, 0))

    def reset(self):
        scene = self.gitem.scene()
        for item in self.drawn_items:
            scene.removeItem(item)
        if self._moves:
            while 1:
                try:
                    move, args = self._moves.get(block=False)
                except Queue.Empty:
                    break
        self.home()

    def penup(self):
        self._pen = False
    def pendown(self):
        self._pen = True

    def color(self, r=None, g=None, b=None):
        pen = self.gitem.pen
        if r is g is b is None:
            return pen.brush().color().getRgb()[:3]
        else:
            pen.setColor(QtGui.QColor.fromRgb(r, g, b))

    def width(self, w=None):
        if w is None:
            return self.gitem.pen.width()
        else:
            self.gitem.pen.setWidth(w)

    def setImageid(self, imageid):
        ogitem = self.gitem
        pos = ogitem.pos
        ang = ogitem.ang
        rend = ogitem.rend
        pen = ogitem.pen
        scene = ogitem.scene()
        gitem = PynguinGraphicsItem(pos, ang, rend, imageid)
        gitem.pen = pen
        scene.removeItem(ogitem)
        scene.addItem(gitem)
        self.gitem = gitem


class GraphicsItem(QtGui.QGraphicsItem):
    def __init__(self):
        QtGui.QGraphicsItem.__init__(self)

    def set_transform(self):
        cpt = self.cpt
        cx, cy = cpt.x(), cpt.y()
        #pt = self.pos
        pt = self.pos - cpt
        x, y = pt.x(), pt.y()

        ang = self.ang

        trans = QtGui.QTransform()
        trans.translate(x, y)
        trans.translate(cx, cy).rotate(ang).translate(-cx, -cy)
        trans.scale(self.scale, self.scale)
        self.setTransform(trans)

    def setpos(self, pos):
        try:
            x, y = pos
            pt = QtCore.QPointF(x, y)
        except TypeError:
            pt = pos
        self.pos = pt
        self.set_transform()

    def set_rotation(self, ang):
        self.ang = -(180/pi)*ang
        self.set_transform()

    def rotate(self, deg):
        self.ang += deg
        self.set_transform()

    def paint(self, painter, option, widget):
        pass

class PynguinGraphicsItem(GraphicsItem):
    def __init__(self, pos, ang, rend, imageid):
        cx, cy = 125, 125
        scale = 0.20
        cxs, cys = cx*scale, cy*scale
        cpt = QtCore.QPointF(cxs, cys)
        self.cpt = cpt
        self.ang = ang
        self.scale = scale
        self.rend = rend

        GraphicsItem.__init__(self)
        self.setpos(pos)

        self.setImageid(imageid)

        self.set_transform()

        self.pen = QtGui.QPen(QtCore.Qt.white)
        self.pen.setWidth(2)

    def setImageid(self, imageid):
        self.item = QtSvg.QGraphicsSvgItem(self)
        self.item.setSharedRenderer(self.rend)
        self.item.setElementId(imageid)

    def boundingRect(self):
        return self.item.boundingRect()


def run():
    app = QtGui.QApplication(sys.argv)

    #splash = Splash(app)
    #splash.show()

    win = MainWindow(app)
    win.show()
    #splash.finish(win)
    app.exec_()


if __name__ == "__main__":
    run()
