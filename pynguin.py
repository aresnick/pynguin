import os
import sys
import math
PI = math.pi
import code

from PyQt4 import QtCore, QtGui, QtSvg, uic
from PyQt4.Qt import QFrame, QWidget, QHBoxLayout, QPainter

from editor import HighlightedTextEdit



pynguin_functions = ['forward', 'fd', 'backward', 'bk', 'left',
                        'lt', 'right', 'rt', 'reset', 'home',
                        'penup', 'pendown',]

uidir = 'data/ui'
uifile = 'pynguin.ui'
uipath = os.path.join(uidir, uifile)
MWClass, _ = uic.loadUiType(uipath)


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

        QtGui.QMainWindow.__init__(self)
        self.ui = MWClass()
        self.ui.setupUi(self)

        self.scene = Scene()
        view = self.ui.view
        view.setScene(self.scene)
        self.scene.view = view
        view.show()

        self.pynguin = Pynguin((0, 0), 0, self.rend)
        self.scene.addItem(self.pynguin)
        trans = QtGui.QTransform()
        #trans.scale(0.15, 0.15)
        trans.scale(1, 1)
        self.scene.view.setTransform(trans)
        view.centerOn(self.pynguin)

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

        #QtCore.QTimer.singleShot(100, self.ropy)

    def ropy(self):
        self.pynguin.left(1)
        self.pynguin.forward(15)
        QtCore.QTimer.singleShot(5, self.ropy)

    def closeEvent(self, ev=None):
        QtGui.qApp.quit()

    def new(self):
        pass

    def save(self):
        pass

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
        elif txt=='NEW':
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
        self.documents[self.title] = self._doc.toPlainText()

    def new(self):
        self.savecurrent()
        self._doc.setPlainText('')
        self.settitle('NEW')

    def switchto(self, docname):
        self.savecurrent()
        self._doc.setPlainText(self.documents[docname])
        self.title = docname

class Interpreter(HighlightedTextEdit):
    def __init__(self):
        HighlightedTextEdit.__init__(self)
        self.history = []
        self.historyp = -1
        self.append('>>> ')

        self.save_stdout = sys.stdout
        self.save_stdin = sys.stdin
        self.save_stderr = sys.stderr

        self._check_control_key = False

        self.setWordWrapMode(QtGui.QTextOption.WordWrap)

    def write(self, text):
        text = text.rstrip()
        if text:
            sys.stdout = self.save_stdout
            #print 'writing',text
            sys.stdout = self
            text = text.strip()
            self.append(text)

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

            sys.stdout = self
            sys.stderr = self
            self.interpreter.push(txt)
            sys.stdout = self.save_stdout
            sys.stderr = self.save_stderr

            self.append('>>> ')

            passthru = False

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
            cblk = self._doc.findBlock(cpos)
            pos = cblk.position()

            txt = str(cblk.text()[4:]).strip()

            changeline = True

            lenhist = len(self.history)
            if k==Up and self.historyp <= -lenhist:
                QtGui.QApplication.beep()
                changeline = False
            elif k==Up:
                self.historyp -= 1
            elif k==Down and self.historyp >= -1:
                QtGui.QApplication.beep()
                changeline = False
            elif k==Down:
                self.historyp += 1

            if k==Up and self.historyp==-2:
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


        cpos = self.textCursor().position()
        cblk = self._doc.findBlock(cpos)
        lblk = self._doc.lastBlock()
        if cblk != lblk:
            lblk = self._doc.lastBlock()
            lpos = lblk.position() + lblk.length() - 1
            curs = self.textCursor()
            curs.setPosition(lpos, 0)
            self.setTextCursor(curs)

        if passthru:
            HighlightedTextEdit.keyPressEvent(self, ev)

        vbar = self.verticalScrollBar()
        vbar.setValue(vbar.maximum())


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

    def keyReleaseEvent(self, ev):
        k = ev.key()
        Control = QtCore.Qt.Key_Control
        if k == Control:
            self._check_control_key = False


class Scene(QtGui.QGraphicsScene):
    def __init__(self):
        QtGui.QGraphicsScene.__init__(self)
        self.setSceneRect(-300, -300, 600, 600)
        color = QtGui.QColor(130, 130, 160)
        brush = QtGui.QBrush(color)
        self.setBackgroundBrush(brush)



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
        x, y = pos
        pt = QtCore.QPointF(x, y)
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

class Pynguin(GraphicsItem):
    def __init__(self, pos, ang, rend):
        cx, cy = 110, 125
        scale = 0.20
        cxs, cys = cx*scale, cy*scale
        cpt = QtCore.QPointF(cxs, cys)
        self.cpt = cpt
        self.ang = ang
        self.scale = scale

        GraphicsItem.__init__(self)
        self.setpos(pos)

        imageid = 'pynguin'
        self.item = QtSvg.QGraphicsSvgItem(self)
        self.item.setSharedRenderer(rend)
        self.item.setElementId(imageid)

        self.set_transform()

        self.pen = QtGui.QPen(QtCore.Qt.white)
        self.pen.setWidthF(1.5)
        self.drawn_items = []

        self.pendown()

    def boundingRect(self):
        return self.item.boundingRect()

    def forward(self, distance):
        ang = self.ang
        rad = ang * (PI / 180)
        dx = distance * math.cos(rad)
        dy = distance * math.sin(rad)

        p0 = QtCore.QPointF(self.pos)

        x=self.pos.x()+dx
        y=self.pos.y()+dy
        self.setpos((x, y))

        p1 = QtCore.QPointF(self.pos)

        if self._pen:
            line = self.scene().addLine(QtCore.QLineF(p0, p1), self.pen)
            line.setFlag(QtGui.QGraphicsItem.ItemStacksBehindParent)
            self.drawn_items.append(line)
    fd = forward

    def backward(self, distance):
        self.forward(-distance)
    bk = backward

    def left(self, degrees):
        self.rotate(-degrees)
    lt = left

    def right(self, degrees):
        self.left(-degrees)
    rt = right

    def goto(self, pos):
        self.setpos(pos)

    def home(self):
        self.ang = 0
        self.goto((0, 0))

    def reset(self):
        scene = self.scene()
        for item in self.drawn_items:
            scene.removeItem(item)
        self.home()

    def penup(self):
        self._pen = False
    def pendown(self):
        self._pen = True

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
