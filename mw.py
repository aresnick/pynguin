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
from math import pi
import code
import glob

from PyQt4 import QtGui, QtCore, uic
from PyQt4.Qt import QHBoxLayout

from pynguin import Pynguin, pynguin_functions, interpreter_protect
from util import getrend
from codearea import CodeArea
from interpreter import Interpreter
from conf import uidir


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


class Scene(QtGui.QGraphicsScene):
    def __init__(self):
        QtGui.QGraphicsScene.__init__(self)
        self.setSceneRect(-300, -300, 600, 600)
        color = QtGui.QColor(130, 130, 160)
        brush = QtGui.QBrush(color)
        self.setBackgroundBrush(brush)