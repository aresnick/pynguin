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
import sys
import code
import Queue
import zipfile
import glob
from random import randrange
from math import atan2, degrees, radians, hypot, cos, sin, pi
PI = pi

from PyQt4 import QtCore, QtGui, QtSvg, uic
from PyQt4.Qt import QFrame, QWidget, QHBoxLayout, QPainter

from editor import HighlightedTextEdit



pynguin_functions = ['forward', 'fd', 'backward', 'bk', 'left',
                        'lt', 'right', 'rt', 'reset', 'home',
                        'penup', 'pendown', 'color', 'width',
                        'circle', 'fill', 'nofill', 'fillcolor',
                        'begin_fill', 'end_fill', 'goto', 'turnto',
                        'write', 'toward', 'distance', 'lineto',
                        'onscreen',]
interpreter_protect = ['p', 'new_pynguin', 'PI', 'history']

uidir = 'data/ui'

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

class MainWindow(QtGui.QMainWindow):
    def __init__(self, app):
        self.app = app
        self.paused = False
        self.rend = getrend(self.app)

        self._fdir = os.path.expanduser('~')
        self._filepath = None
        self._modified = False

        import pynguin
        appdir, _ = os.path.split(os.path.abspath(pynguin.__file__))
        self.appdir = appdir
        uifile = 'pynguin.ui'
        uipath = os.path.join(appdir, uidir, uifile)
        MWClass, _ = uic.loadUiType(uipath)

        QtGui.QMainWindow.__init__(self)
        self.ui = MWClass()
        self.ui.setupUi(self)

        self.scene = Scene()
        view = self.ui.view
        view.setScene(self.scene)
        self.scene.view = view
        view.show()
        view.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        view.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)

        self.speedgroup = QtGui.QActionGroup(self)
        self.speedgroup.addAction(self.ui.actionSlow)
        self.speedgroup.addAction(self.ui.actionMedium)
        self.speedgroup.addAction(self.ui.actionFast)
        self.speedgroup.addAction(self.ui.actionInstant)
        self.speedgroup.setExclusive(True)
        self.speedgroup.triggered.connect(self.setSpeed)

        self.pynguins = []
        self._primary_pynguin = True
        self.pynguin = self.new_pynguin()
        trans = QtGui.QTransform()
        #trans.scale(0.15, 0.15)
        trans.scale(1, 1)
        self.scene.view.setTransform(trans)
        view.centerOn(self.pynguin.gitem)

        self.editor = CodeArea(self)
        hbox = QHBoxLayout(self.ui.edframe)
        hbox.setSpacing(0)
        hbox.setMargin(0)
        #hbox.addWidget(self.number_bar)
        hbox.addWidget(self.editor)

        self.interpretereditor = Interpreter(self)
        hbox = QHBoxLayout(self.ui.interpreterframe)
        hbox.setSpacing(0)
        hbox.setMargin(0)
        #hbox.addWidget(self.number_bar)
        hbox.addWidget(self.interpretereditor)
        ilocals = {'p': self.pynguin,
                    'PI':pi,
                    'new_pynguin':self.new_pynguin,
                    'history': self.history}
        for fname in pynguin_functions:
            function = getattr(self.pynguin, fname)
            ilocals[fname] = function
        self.interpreter_locals = ilocals
        self.interpreter = code.InteractiveConsole(self.interpreter_locals)
        self.interpretereditor.interpreter = self.interpreter

        self.interpretereditor.setFocus()

        self.ui.rsplitter.setSizes([390, 110])
        self.ui.wsplitter.setSizes([550, 350])

        self.viewgroup = QtGui.QActionGroup(self)
        self.viewgroup.addAction(self.ui.actionPynguin)
        self.viewgroup.addAction(self.ui.actionArrow)
        self.viewgroup.addAction(self.ui.actionRobot)
        self.viewgroup.addAction(self.ui.actionTurtle)
        self.viewgroup.addAction(self.ui.actionHidden)
        self.viewgroup.setExclusive(True)
        self.viewgroup.triggered.connect(self.setImage)

        self.pengroup = QtGui.QActionGroup(self)
        self.pengroup.addAction(self.ui.actionPenUp)
        self.pengroup.addAction(self.ui.actionPenDown)
        self.pengroup.setExclusive(True)
        self.pengroup.triggered.connect(self.setPen)

        self.fillgroup = QtGui.QActionGroup(self)
        self.fillgroup.addAction(self.ui.actionFill)
        self.fillgroup.addAction(self.ui.actionNofill)
        self.fillgroup.setExclusive(True)
        self.fillgroup.triggered.connect(self.setFill)

        self.setup_settings()
        self.setup_recent()

        self.setup_examples()

    def setup_examples(self):
        filemenu = self.ui.filemenu
        actionsave = self.ui.actionSave
        exmenu = QtGui.QMenu('Examples', filemenu)
        exa = filemenu.insertMenu(actionsave, exmenu)
        examplemenu = exa.menu()

        examplesrel = 'doc/examples'
        examplespath = os.path.join(self.appdir, examplesrel)
        self.examplespath = examplespath
        examplesglob = '%s/*.pyn' % examplespath
        examples = glob.glob(examplesglob)
        for ex in examples:
            pth, fn = os.path.split(ex)
            def excb(fp=ex):
                self.open_example(fp)
            action = examplemenu.addAction(fn, excb)

    def open_example(self, fp):
        if not self.maybe_save():
            return
        else:
            self._filepath = None

        self._new()
        self._openfile(fp, False)

    def setup_settings(self):
        settings = QtCore.QSettings()
        QtCore.QCoreApplication.setOrganizationName('pynguin.googlecode.com')
        QtCore.QCoreApplication.setOrganizationDomain('pynguin.googlecode.com')
        QtCore.QCoreApplication.setApplicationName('pynguin')
        self.settings = settings

    def setup_recent(self):
        settings = self.settings
        settings = QtCore.QSettings()
        recent = []
        for n in range(settings.beginReadArray('recent')):
            settings.setArrayIndex(n)
            fname = settings.value('fname').toString()
            recent.append(str(fname))
        settings.endArray()

        filemenu = self.ui.filemenu
        actionsave = self.ui.actionSave
        recmenu = QtGui.QMenu('Recent', filemenu)
        exa = filemenu.insertMenu(actionsave, recmenu)
        examplemenu = exa.menu()
        for fp in recent:
            pth, fn = os.path.split(fp)
            if not fn:
                continue
            def excb(fp=fp):
                self.open_recent(fp)
            examplemenu.addAction(fn, excb)

    def open_recent(self, fp):
        if not self.maybe_save():
            return
        else:
            self._filepath = None

        self._fdir, _ = os.path.split(fp)
        self._new()
        self._filepath = fp
        self._openfile(fp)

    def new_pynguin(self):
        p = Pynguin(self.scene, (0, 0), 0, self.rend)
        self.pynguins.append(p)
        self.setSpeed()

        if self._primary_pynguin:
            p._process_moves()
            self._primary_pynguin = False
        else:
            self.pynguin.qmove(p._process_moves)

        return p

    def closeEvent(self, ev=None):
        if self.maybe_save():
            ev.accept()
        else:
            ev.ignore()

    def history(self, clear=False):
        if not clear:
            for line in self.interpretereditor.history:
                self.interpretereditor.write('%s\n' % line)
        else:
            self.interpretereditor.history = []

    def new(self):
        if self.maybe_save():
            self._new()
        else:
            pass

    def _new(self):
        for pynguin in self.pynguins:
            pynguin.reset()
            if pynguin is not self.pynguin:
                self.scene.removeItem(pynguin.gitem)
                self.pynguins.remove(pynguin)
        del_later = []
        for name in self.interpreter_locals:
            if name not in pynguin_functions and name not in interpreter_protect:
                del_later.append(name)
        for name in del_later:
            del self.interpreter_locals[name]
        self.editor.clear()
        self.interpretereditor.clear()
        self._filepath = None

    def maybe_save(self):
        if self._modified:
            ret = QtGui.QMessageBox.warning(self, self.tr("Application"),
                        self.tr("The document has been modified.\n"
                                "Do you want to save your changes?"),
                        QtGui.QMessageBox.Yes | QtGui.QMessageBox.Default,
                        QtGui.QMessageBox.No,
                        QtGui.QMessageBox.Cancel | QtGui.QMessageBox.Escape)
            if ret == QtGui.QMessageBox.Yes:
                return self.save()
            elif ret == QtGui.QMessageBox.Cancel:
                return False
        return True

    def _savestate(self):
        '''write out the files in the editor window, and keep the list
            of history entries. All of this is packed up in to a zip
            file and given a .pyn filename ending.

        '''

        self.editor.savecurrent()

        r, ext = os.path.splitext(self._filepath)
        if ext != '.pyn':
            ext = '.pyn'
        self._filepath = r + ext
        z = zipfile.ZipFile(self._filepath, 'w')

        mselect = self.ui.mselect
        for n in range(mselect.count()):
            ename = str(mselect.itemText(n))
            efile = self.editor.documents[ename]
            arcname = '##%5s##__%s' % (n, ename)
            z.writestr(arcname, efile)

        historyname = '@@history@@'
        history = '\n'.join(self.interpretereditor.history)
        z.writestr(historyname, history)

        z.close()

        self._modified = False
        self.setWindowModified(False)

        self.addrecentfile(self._filepath)

        return True

    def addrecentfile(self, fp):
        settings = self.settings
        settings = QtCore.QSettings()
        recent = [fp]
        for n in range(settings.beginReadArray('recent')):
            settings.setArrayIndex(n)
            fname = settings.value('fname').toString()
            if fname and fname not in recent:
                recent.append(fname)
        settings.endArray()

        recent = recent[:6]

        settings.beginWriteArray('recent')
        for n in range(len(recent)):
            settings.setArrayIndex(n)
            fpath = recent[n]
            settings.setValue('fname', fpath)
        settings.endArray()

    def save(self):
        '''call _savestate with current file name, or get a file name from
            the user and then call _savestate
        '''

        if self._filepath is None:
            return self.saveas()
        else:
            return self._savestate()

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
            return False

        return self._savestate()

    def open(self):
        '''read in a previously written .pyn file (written by _savestate)
            Any documents that look like function definitions will be
                exec'd to load them in to the interpreter local namespace.
            Any previous history will be lost and replaced with the
                history loaded from the file.
        '''
        if not self.maybe_save():
            return

        if self._fdir is None:
            fdir = QtCore.QString(os.path.abspath(os.path.curdir))
        else:
            fdir = self._fdir

        fp = str(QtGui.QFileDialog.getOpenFileName(self, 'Open file', fdir, 'Text files (*.pyn)'))
        if fp:
            self._fdir, _ = os.path.split(fp)
            self._new()
            self._filepath = fp
            self._openfile(fp)

    def _openfile(self, fp, add_to_recent=True):
        z = zipfile.ZipFile(fp, 'r')
        for ename in z.namelist():
            fo = z.open(ename, 'rU')
            data = fo.read()
            if ename.startswith('##'):
                hdr = ename[0:9]
                if hdr.startswith('##') and hdr.endswith('##'):
                    title = ename[11:]
                    self.editor.add(data)
                    if data.startswith('def '):
                        try:
                            exec data in self.interpreter_locals
                        except:
                            print 'problem', title
            elif ename.startswith('@@history@@'):
                history = data.split('\n')
                self.interpretereditor.history = history

        self.ui.mselect.setCurrentIndex(0)
        self.changedoc(0)

        self._modified = False
        self.setWindowModified(False)

        if add_to_recent:
            self.addrecentfile(self._filepath)

    def export(self):
        '''save the current drawing'''
        if self._fdir is None:
            fdir = QtCore.QString(os.path.abspath(os.path.curdir))
        else:
            fdir = self._fdir

        fp = str(QtGui.QFileDialog.getSaveFileName(self, 'Export Image', fdir))
        if fp:
            self._fdir, _ = os.path.split(fp)
        else:
            return False

        for pynguin in self.pynguins:
            pynguin.gitem.hide()

        scene = self.scene
        view = scene.view

        scene.setSceneRect(scene.sceneRect().united(scene.itemsBoundingRect()))

        src = scene.sceneRect()
        szf = src.size()
        sz = QtCore.QSize(szf.width(), szf.height())
        self._i = i = QtGui.QImage(sz, QtGui.QImage.Format_ARGB32)
        p = QtGui.QPainter(i)
        ir = i.rect()
        irf = QtCore.QRectF(0, 0, src.width(), src.height())

        scene.render(p, irf, src)
        if not i.save(fp):
            QtGui.QMessageBox.warning(self,
                                'Unable to save',
                                'Cannot export image.')

        for pynguin in self.pynguins:
            pynguin.gitem.show()

    def newdoc(self):
        '''Add a new (blank) page to the document editor'''
        self.editor.new()
        self.editor.setFocus()

        self._modified = True
        self.setWindowModified(True)

    def changedoc(self, idx):
        '''switch which document is visible in the document editor'''
        docname = str(self.ui.mselect.itemText(idx))
        if docname in self.editor.documents:
            self.editor.switchto(docname)
            self.editor.setFocus()

    def removedoc(self):
        '''throw away the currently displayed editor document'''
        mselect = self.ui.mselect
        idx = mselect.currentIndex()
        docname = str(mselect.itemText(idx))
        mselect.removeItem(idx)
        if mselect.count():
            self.changedoc(0)
            mselect.setCurrentIndex(0)
        else:
            self.editor._doc.setPlainText('')
            self.editor.settitle('NEW')

        if docname in self.editor.documents:
            del self.editor.documents[docname]

        self._modified = True
        self.setWindowModified(True)

    def testcode(self):
        '''exec the code in the current editor window and load it in
            to the interpreter local namespace

            If the first line looks like a function definition, use
            it to feed a line to the interpreter set up to call the
            function.
        '''
        self.editor.savecurrent()
        docname = str(self.ui.mselect.currentText())
        code = str(self.editor.documents[docname])

        # fix up the code a bit first...
        # make sure the last line ends with newline
        # and make sure the code does not end with
        # lines that have only indentation
        lines = code.split('\n')
        lines.reverse()
        blankend = True
        rewrite = []
        for line in lines:
            if line.isspace() and blankend:
                pass
            else:
                blankend = False
                rewrite.append(line)
        rewrite.reverse()
        code = '%s\n' % '\n'.join(rewrite)
        self.editor.setPlainText(code)

        try:
            compile(code, 'current file', 'exec')
        except SyntaxError, e:
            self.editor.selectline(e.lineno)
            self.interpretereditor.write('Syntax Error in line %s\n' % e.lineno)
            self.interpretereditor.write('>>> ')
            self.editor.setFocus()
        else:
            self.interpretereditor.setFocus()
            sys.stdout = self.interpretereditor
            sys.stderr = self.interpretereditor
            if self.interpretereditor.cmdthread is None:
                self.interpretereditor.cmdthread = CmdThread(self.interpretereditor, code)
                cmdthread = self.interpretereditor.cmdthread
                cmdthread.start()
                while not cmdthread.wait(0) and not self.interpretereditor.controlC:
                    for pynguin in self.pynguins:
                        pynguin._r_process_moves()
                    QtGui.QApplication.processEvents(QtCore.QEventLoop.AllEvents)
                if self.interpretereditor.controlC:
                    cmdthread.terminate()
                    for pynguin in self.pynguins:
                        pynguin._empty_move_queue()
                        pynguin._r_process_moves()
                        pynguin._sync_items()
                    self.interpretereditor.append('KeyboardInterrupt\n')
                    self.interpretereditor.controlC = False
                    self.interpretereditor.needmore = False
                    self.interpretereditor.interpreter.resetbuffer()
                    sys.stdout = self.interpretereditor.save_stdout
                    sys.stderr = self.interpretereditor.save_stderr
                    self.interpretereditor.write('>>> ')
                self.interpretereditor.cmdthread = None

                line0 = code.split('\n')[0]
                if line0.startswith('def ') and line0.endswith(':'):
                    firstparen = line0.find('(')
                    lastparen = line0.rfind(')')
                    if firstparen > -1 and lastparen > -1:
                        tocall = line0[4:lastparen+1]
                        self.interpretereditor.addcmd(tocall)

            else:
                self.interpretereditor.write('not starting...\n')
                self.interpretereditor.write('code already running\n')
                self.interpretereditor.write('>>> ')

        self.interpretereditor.setFocus()

    def setPenColor(self):
        '''use a color selection dialog to set the pen line color

        sets the color for the primary pynguin only. For other later
            added pynguins, use p.color()
        '''
        icolor = self.pynguin.gitem.pen.brush().color()
        ncolor = QtGui.QColorDialog.getColor(icolor, self)
        if ncolor.isValid():
            self.pynguin.gitem.pen.setColor(ncolor)
            r, g, b, a = ncolor.getRgb()
            cmd = 'color(%s, %s, %s)\n' % (r, g, b)
            self.interpretereditor.addcmd(cmd)

    def setPenWidth(self):
        '''open a dialog with a spin button to get a new pen line width

        sets the width for the primary pynguin only. For other later
            added pynguins, use p.width()
        '''
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
        cmd = 'width(%s)\n' % nwidth
        self.interpretereditor.addcmd(cmd)

    def setPen(self, ev):
        '''toggle pen up and pen down

        sets the pen for the primary pynguin only. For other later
            added pynguins, use p.penup() or p.pendown()
        '''
        if ev == self.ui.actionPenUp:
            self.pynguin.penup()
            self.interpretereditor.addcmd('penup()\n')
        else:
            self.pynguin.pendown()
            self.interpretereditor.addcmd('pendown()\n')

    def setFill(self, ev):
        '''toggle fill on / off

        sets the fill for the primary pynguin only. For other later
            added pynguins, use p.fill() or p.nofill()
        '''
        if ev == self.ui.actionFill:
            self.pynguin.fill()
            self.interpretereditor.addcmd('fill()\n')
        else:
            self.pynguin.nofill()
            self.interpretereditor.addcmd('nofill()\n')

    def setFillColor(self):
        '''use a color selection dialog to set the fill color

        sets the fill color for the primary pynguin only. For other
            later added pynguins, use p.fillcolor()
        '''
        icolor = self.pynguin.gitem.brush.color()
        ncolor = QtGui.QColorDialog.getColor(icolor, self)
        if ncolor.isValid():
            r, g, b, a = ncolor.getRgb()
            self.pynguin.fillcolor(r, g, b)
            cmd = 'fillcolor(%s, %s, %s)\n' % (r, g, b)
            self.interpretereditor.addcmd(cmd)

    def setImage(self, ev):
        '''select which image to show

        sets the image for the primary pynguin only. For other later
            added pynguins, use p.setImageid() or p.setImageid()
        '''
        choices = {self.ui.actionPynguin: 'pynguin',
                    self.ui.actionArrow: 'arrow',
                    self.ui.actionRobot: 'robot',
                    self.ui.actionTurtle: 'turtle',
                    self.ui.actionHidden: 'hidden',}
        self.pynguin.setImageid(choices[ev])

    def _setSpeed(self, speed):
        for pynguin in self.pynguins:
            pynguin._drawspeed_pending = 2 * speed
            pynguin._turnspeed_pending = 4 * speed
    def setSpeed(self, ev=None):
        '''select drawing speed setting. Sets the speed for _all_ pynguins!'''
        if ev is None:
            ev = self.speedgroup.checkedAction()

        choice = {self.ui.actionSlow: 5,
                    self.ui.actionMedium: 10,
                    self.ui.actionFast: 20,
                    self.ui.actionInstant: 0,}

        speed = choice[ev]
        self._setSpeed(speed)

    def about(self):
        AboutDialog().exec_()


class CodeArea(HighlightedTextEdit):
    def __init__(self, mw):
        HighlightedTextEdit.__init__(self)
        self.mw = mw
        self.mselect = mw.ui.mselect
        self.documents = {}
        self.title = ''
        self.settitle('Untitled')

    def clear(self):
        self._doc.clear()
        self.documents = {}
        self.mselect.clear()

    def keyPressEvent(self, ev):
        k = ev.key()

        Return = QtCore.Qt.Key_Return
        lead = 0
        if k == Return:
            curs = self.textCursor()
            cpos = curs.position()
            cblk = self._doc.findBlock(cpos)
            atstart = curs.atBlockStart()
            if atstart:
                lead = 0
            else:
                cblktxt = str(cblk.text())
                ts = cblktxt.split()
                if ts:
                    lead = cblktxt.find(ts[0])

                char = self._doc.characterAt(cpos-1)
                colon = QtCore.QChar(':')
                if char == colon:
                    # auto indent
                    lead += 4

        HighlightedTextEdit.keyPressEvent(self, ev)
        if lead:
            self.insertPlainText(' '*lead)

        fblk = self._doc.firstBlock()
        txt = str(fblk.text())
        self.settitle(txt)
        if self._doc.isModified():
            self.mw._modified = True
            self.mw.setWindowModified(True)

    def settitle(self, txt):
        '''set the title for the current document to txt
            Also updates the combobox document selector.

            If txt looks like a function definition, uses
            the name/ signature of the function as the
            title instead of the whole line.
        '''
        if txt.startswith('def ') and txt.endswith(':'):
            title = txt[4:-1]
        elif txt=='NEW' or txt=='':
            title = 'Untitled'
        else:
            title = txt

        if title in self.documents and self.title=='Untitled':
            # This is probably a copy/paste of another page
            copyn = 0
            for othertitle in self.documents.keys():
                if othertitle==title or \
                    (title[-5:-4]=='#' and othertitle.startswith(title[4:-6])) or \
                    (othertitle[:-5]==title[:-5]) or \
                    (title == othertitle[4:-6] and othertitle[-5:-4]=='#'):
                    copyn += 1

            if title[-5:-4]=='#':
                title = title[:-5]

            title = txt
            titleadd = '#%04d' % copyn
            fblk = self._doc.firstBlock()
            fblklen = fblk.length()

            fblktxt = str(fblk.text())
            if fblktxt[-5:-4] == '#':
                curs = QtGui.QTextCursor(self._doc)
                curs.setPosition(fblklen-6, 0)
                curs.setPosition(fblklen-1, 1)
                self.setTextCursor(curs)
                curs.removeSelectedText()
                fblklen = fblk.length()
                title = str(fblk.text()).rstrip()

            curs = QtGui.QTextCursor(self._doc)
            curs.setPosition(fblklen-1, 0)
            self.setTextCursor(curs)
            self.insertPlainText(titleadd)
            title = title + titleadd

        if title != self.title:
            if txt != 'NEW':
                idx = self.mselect.findText(self.title)
                if idx > -1:
                    self.mselect.removeItem(idx)
                if self.title in self.documents:
                    self.documents[title] = self.documents[self.title]
                    del self.documents[self.title]
            self.title = title
            self.mselect.addItem(title)

        idx = self.mselect.findText(self.title)
        self.mselect.setCurrentIndex(idx)

    def savecurrent(self):
        '''get the text of the current document and save it in the
            documents dictionary, keyed by title
        '''
        title = self.title
        text = str(self._doc.toPlainText())
        if title != 'Untitled' or text:
            self.documents[title] = text

    def new(self):
        '''save the current document and start a new blank document'''
        self.savecurrent()
        self._doc.setPlainText('')
        self.settitle('NEW')

    def switchto(self, docname):
        '''save the current document and switch to the document titled docname'''
        self.savecurrent()
        self._doc.setPlainText(self.documents[docname])
        self.title = docname

    def add(self, txt):
        '''add a new document with txt as the contents'''
        self.new()
        self._doc.setPlainText(txt)
        title = txt.split('\n')[0]
        self.settitle(title)
        self.savecurrent()

    def selectline(self, n):
        '''highlight line number n'''
        docline = 1
        doccharstart = 0
        blk = self._doc.begin()
        while docline < n:
            txt = blk.text()
            lentxt = len(txt)+1
            doccharstart += lentxt
            blk = blk.next()
            docline += 1
        txt = blk.text()
        lentxt = len(txt)
        doccharend = doccharstart + lentxt

        curs = QtGui.QTextCursor(self._doc)
        curs.setPosition(doccharstart, 0)
        curs.setPosition(doccharend, 1)
        self.setTextCursor(curs)


class CmdThread(QtCore.QThread):
    def __init__(self, ed, txt):
        '''set up a separate thread to run the code given in txt in the
            InteractiveInterpreter ed.'''
        QtCore.QThread.__init__(self)
        QtCore.QThread.setTerminationEnabled()
        self.ed = ed
        self.txt = txt
    def run(self):
        ed = self.ed
        sys.stdout = ed
        sys.stderr = ed
        lines = self.txt.split('\n')
        for line in lines:
            ed.needmore = ed.interpreter.push(line)
        sys.stdout = ed.save_stdout
        sys.stderr = ed.save_stderr

class Interpreter(HighlightedTextEdit):
    def __init__(self, parent):
        HighlightedTextEdit.__init__(self)
        self.mw = parent
        self.pynguin = parent.pynguin
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

    def clear(self):
        self.history = []
        self._outputq = []
        self._doc.clear()
        self.write('>>> ')

    def addcmd(self, cmd):
        self.write(cmd)
        if cmd[-1] == '\n':
            self.write('>>> ')
            self.history.append(cmd.rstrip())

    def write(self, text):
        '''cannot write directly to the console...
            instead, append this text to the output queue for later use.
        '''
        if text:
            self._outputq.append(text)

    def writeoutputq(self):
        '''process the text output queue. Must be done from the main thread.
        '''
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
        A = QtCore.Qt.Key_A
        Home = QtCore.Qt.Key_Home
        E = QtCore.Qt.Key_E

        lblk = self._doc.lastBlock()
        cpos = self.textCursor().position()
        cblk = self._doc.findBlock(cpos)
        cblkpos = cblk.position()

        passthru = True

        if k == Return:
            self.movetoend()

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
                    for pynguin in self.mw.pynguins:
                        pynguin._r_process_moves()
                    QtGui.QApplication.processEvents(QtCore.QEventLoop.AllEvents)
                if self.controlC:
                    self.cmdthread.terminate()
                    for pynguin in self.mw.pynguins:
                        pynguin._empty_move_queue()
                        pynguin._r_process_moves()
                        pynguin._sync_items()
                    self.append('KeyboardInterrupt\n')
                    self.controlC = False
                    self.needmore = False
                    self.interpreter.resetbuffer()
                    sys.stdout = self.save_stdout
                    sys.stderr = self.save_stderr
                self.cmdthread = None

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
            else:
                self.write('KeyboardInterrupt\n')
                self.write('>>> ')

        elif (self._check_control_key and k==A) or k == Home:
            self.movetostart()
            passthru = False

        elif (self._check_control_key and k==E):
            self.movetoend()
            passthru = False

        self.scrolldown()

        if passthru:
            HighlightedTextEdit.keyPressEvent(self, ev)

    def scrolldown(self):
        '''force the console to scroll all the way down, and put
            the cursor after the last letter.
        '''
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

    def movetostart(self):
        '''move the cursor to the start of the line (after the prompt)'''
        cpos = self.textCursor().position()
        cblk = self._doc.findBlock(cpos)
        pos = cblk.position()
        curs = self.textCursor()
        curs.setPosition(pos+4, 0)
        self.setTextCursor(curs)

    def movetoend(self):
        '''move the cursor to the end of the line'''
        cpos = self.textCursor().position()
        cblk = self._doc.findBlock(cpos)
        pos = cblk.position()
        endpos = pos + cblk.length() - 1
        curs = self.textCursor()
        curs.setPosition(endpos, 0)
        self.setTextCursor(curs)

    def erasetostart(self):
        '''erase from the current cursor position to the beginning
            of the line
        '''
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
        self._item_setangle(self.ritem, ang)
        self.qmove(self._item_setangle, (self.gitem, ang,))

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

    def _item_home(self, item):
        self._item_goto(item, QtCore.QPointF(0, 0))
        self._item_setangle(item, 0)

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

    def reset(self):
        self.qmove(self._reset)
        self._item_home(self.ritem)

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

    def _width(self, w=None):
        if w is None:
            return self.gitem.pen.width()
        else:
            self.gitem.pen.setWidth(w)

    def width(self, w=None):
        self.qmove(self._item_forward, (self.gitem, 0))
        self.qmove(self._width, (w,))

    def _fillcolor(self, r=None, g=None, b=None):
        color = QtGui.QColor.fromRgb(r, g, b)
        self.gitem.brush.setColor(color)
        self._item_forward(self.gitem, 0)

    def fillcolor(self, r=None, g=None, b=None):
        if r is g is b is None:
            return self.ritem.fillcolor
        else:
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
        scene.removeItem(ogitem)
        scene.addItem(gitem)
        self.gitem = gitem

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
        self.item = QtSvg.QGraphicsSvgItem(self)
        self.item.setSharedRenderer(self.rend)
        self.item.setElementId(imageid)

    def boundingRect(self):
        return self.item.boundingRect()



class AboutDialog(QtGui.QDialog):
    def __init__(self):
        QtGui.QDialog.__init__(self)
        uifile = 'about.ui'
        uipath = os.path.join(uidir, uifile)
        uic.loadUi(uipath, self)


class Splash(QtGui.QSplashScreen):
    def __init__(self, app):
        rend = getrend(app)
        img = QtGui.QPixmap(500, 320)
        #img.fill(QtCore.Qt.transparent)
        self.img = img
        painter = QtGui.QPainter(img)
        rend.render(painter, 'splash')
        painter.end()
        QtGui.QSplashScreen.__init__(self, img)
        #self.setMask(img.mask())
        QtCore.QTimer.singleShot(1500, self.away)

    def away(self):
        self.finish(self.win)

def run():
    app = QtGui.QApplication(sys.argv)

    splash = Splash(app)
    splash.show()

    win = MainWindow(app)
    splash.win = win
    win.show()
    app.exec_()


if __name__ == "__main__":
    run()
