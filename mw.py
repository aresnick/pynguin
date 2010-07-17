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
from math import pi
import glob
import zipfile
import logging
logger = logging.getLogger('PynguinLogger')

from PyQt4 import QtGui, QtCore, uic
from PyQt4.Qt import QHBoxLayout

from pynguin import Pynguin, pynguin_functions, interpreter_protect
from util import getrend, sign
from codearea import CodeArea
from interpreter import Interpreter, CmdThread, Console
from about import AboutDialog
from conf import uidir, bug_url
from conf import backupfolder, backupfile, backuprate, keepbackups


class MainWindow(QtGui.QMainWindow):
    def __init__(self, app):
        self.app = app
        self.paused = False
        self.rend = getrend(self.app)

        self._fdir = os.path.expanduser('~')
        self._filepath = None
        self._modified = False

        self._mainthread = QtCore.QThread.currentThread()

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
        view.mousePressEvent = self.onclick
        view.wheelEvent = self.mousewheelscroll
        view.mouseMoveEvent = self.mousemove

        self.speedgroup = QtGui.QActionGroup(self)
        self.speedgroup.addAction(self.ui.actionSlow)
        self.speedgroup.addAction(self.ui.actionMedium)
        self.speedgroup.addAction(self.ui.actionFast)
        self.speedgroup.addAction(self.ui.actionInstant)
        self.speedgroup.setExclusive(True)
        self.speedgroup.triggered.connect(self.setSpeed)

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
        ilocals = {}
        self.interpreter_locals = ilocals
        self.interpreter = Console(self.interpreter_locals, self.interpretereditor)
        self.interpretereditor.interpreter = self.interpreter
        self.interpretereditor.setFocus()

        Pynguin.mw = self
        Pynguin.rend = self.rend
        self.pynguins = []
        self.pynguin = None
        self.pynguin = self.new_pynguin()

        self._scale = 1
        trans = QtGui.QTransform()
        trans.scale(self._scale, self._scale)
        self.scene.view.setTransform(trans)
        view.centerOn(self.pynguin.gitem)

        self.interpretereditor.pynguin = self.pynguin
        self.setup_interpreter_locals()

        self.ui.rsplitter.setSizes([390, 110])
        self.ui.wsplitter.setSizes([550, 350])
        self.ui.wsplitter.splitterMoved.connect(self.recenter)

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

        QtCore.QTimer.singleShot(60000, self.autosave)
        self._centerview()

    def setup_interpreter_locals(self):
        ilocals = self.interpreter_locals
        ilocals.update(PI=pi,
                        Pynguin=Pynguin,
                        pynguin=self.pynguin,
                        p=self.pynguin,
                        pynguins=self.pynguins,
                        history=self.history,)
        for fname in pynguin_functions:
            function = getattr(self.pynguin, fname)
            ilocals[fname] = function

    def mousewheelscroll(self, ev):
        delta = ev.delta()
        view = self.scene.view
        view.setTransformationAnchor(QtGui.QGraphicsView.AnchorUnderMouse)
        self.zoom(delta)
        view.setTransformationAnchor(QtGui.QGraphicsView.AnchorViewCenter)

    def zoom(self, delta):
        view = self.scene.view

        scaleperc = 1 + ((delta / 120.0) * 0.05)
        self._scale *= scaleperc

        trans = QtGui.QTransform()
        trans.scale(self._scale, self._scale)
        view.setTransform(trans)

        self._centerview()

    def zoomin(self):
        self.zoom(120)
    def zoomout(self):
        self.zoom(-120)
    def zoom100(self):
        self._scale = 1
        self.zoom(0)

    def mousemove(self, ev):
        QtGui.QGraphicsView.mouseMoveEvent(self.scene.view, ev)

        buttons = ev.buttons()
        if buttons & QtCore.Qt.MidButton:
            pos = ev.posF()
            dpos = self._middledragstart - pos
            ctr0 = self._dragstartcenter
            ctr = ctr0 + (dpos / self._scale)

            self._cx = ctr.x()
            self._cy = ctr.y()
            self.recenter()

    def pan(self, dx=0, dy=0):
        cx0 = self._cx
        cy0 = self._cy
        self._cx +=  dx / self._scale
        self._cy -=  dy / self._scale
        self.recenter()
        ctr1 = self._viewcenter()
        cx1 = ctr1.x()
        cy1 = ctr1.y()
        if dx:
            ctr = QtCore.QPointF(cx1, cy0)
        elif dy:
            ctr = QtCore.QPointF(cx0, cy1)
        self._centerview(ctr)

    def panleft(self):
        self.pan(dx=-25)
    def panright(self):
        self.pan(dx=+25)
    def panup(self):
        self.pan(dy=+25)
    def pandown(self):
        self.pan(dy=-25)

    def _viewrect(self):
        view = self.scene.view
        viewportrect = view.viewport().geometry()
        tl = viewportrect.topLeft()
        br = viewportrect.bottomRight()
        tlt = view.mapToScene(tl)
        brt = view.mapToScene(br)
        return QtCore.QRectF(tlt, brt)

    def _viewcenter(self):
        ctr = self._viewrect().center()
        return ctr

    def _centerview(self, ctr=None):
        if ctr is None:
            ctr = self._viewcenter()
        self._cx = ctr.x()
        self._cy = ctr.y()

    def onclick(self, ev):
        QtGui.QGraphicsView.mousePressEvent(self.scene.view, ev)

        button = ev.button()
        if not ev.isAccepted() and button==QtCore.Qt.LeftButton:
            self.leftclick(ev)

        elif button==QtCore.Qt.MidButton:
            self.middleclick(ev)

        self.interpretereditor.setFocus()

    def middleclick(self, ev):
        self._middledragstart = ev.posF()
        self._dragstartcenter = self._viewcenter()

    def leftclick(self, ev):
        evpos = ev.pos()
        scpos = self.scene.view.mapToScene(evpos)
        for pyn in self.pynguins:
            if pyn.respond_to_mouse_click:
                pyn.onclick(scpos.x(), scpos.y())
        ev.ignore()

    def recenter(self):
        center = QtCore.QPointF(self._cx, self._cy)
        self.ui.view.centerOn(center)

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

        # push some of the examples to the top of the list
        ordered = ['welcome', 'somex', 'morex']
        topex = []
        for o in ordered:
            fn = '%s.pyn' % o
            for ex in examples:
                if ex.endswith(fn):
                    topex.append(ex)
        for place, ex in enumerate(topex):
            examples.remove(ex)
            examples.insert(place, ex)

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
        QtCore.QCoreApplication.setOrganizationName('pynguin.googlecode.com')
        QtCore.QCoreApplication.setOrganizationDomain('pynguin.googlecode.com')
        QtCore.QCoreApplication.setApplicationName('pynguin')
        settings = QtCore.QSettings()
        self.settings = settings

        fontsize, ok = settings.value('editor/fontsize', 16).toInt()
        if ok:
            self.editor.setfontsize(fontsize)
        wrap = settings.value('editor/wordwrap', False).toBool()
        if wrap:
            self.ui.actionWordwrap.setChecked(True)
            self.wordwrap()

    def setup_recent(self):
        settings = self.settings
        settings = QtCore.QSettings()
        recent = []
        for n in range(settings.beginReadArray('recent')):
            settings.setArrayIndex(n)
            fname = settings.value('fname').toString()
            recent.append(unicode(fname))
        settings.endArray()

        filemenu = self.ui.filemenu
        actionsave = self.ui.actionSave
        rmenu = QtGui.QMenu('Recent', filemenu)
        rec = filemenu.insertMenu(actionsave, rmenu)
        recmenu = rec.menu()
        for fp in recent:
            pth, fn = os.path.split(fp)
            if not fn:
                continue
            def excb(fp=fp):
                self.open_recent(fp)
            recmenu.addAction(fn, excb)

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
        p = Pynguin()
        return p

    def timerEvent(self, ev):
        Pynguin._process_moves()

    def closeEvent(self, ev=None):
        if self.maybe_save():
            self.interpretereditor.cmdthread = None
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
            self._new(newdoc=True)
        else:
            pass

    def _new(self, newdoc=False):
        self.pynguin.reset(True)
        del_later = []
        for name in self.interpreter_locals:
            if name not in pynguin_functions and name not in interpreter_protect:
                del_later.append(name)
        for name in del_later:
            del self.interpreter_locals[name]
        self.editor.clear()
        self.interpretereditor.clear()
        if newdoc:
            self.newdoc()
        self._modified = False
        windowtitle = 'pynguin [*]'
        self.setWindowTitle(windowtitle)
        self.setWindowModified(False)
        self._filepath = None

    def check_modified(self):
        if self._modified:
            return True
        else:
            for tdoc in self.editor.textdocuments.values():
                if tdoc.isModified():
                    return True

        return False

    def maybe_save(self):
        if self.check_modified():
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

    def autosave(self):
        '''automatically save a copy of the current project.
        Also moves older backups up a number and deletes the
            oldest backup.
        '''
        if not keepbackups:
            return

        folder = backupfolder or self._fdir
        fp = os.path.join(backupfolder, backupfile % '')
        self._writefile(fp)

        for fn in range(keepbackups, 1, -1):
            fpsrc = os.path.join(backupfolder, backupfile % (fn-1))
            fpdst = os.path.join(backupfolder, backupfile % fn)
            if os.path.exists(fpsrc):
                os.rename(fpsrc, fpdst)

        os.rename(fp, fpsrc)

        QtCore.QTimer.singleShot(backuprate*60000, self.autosave)

    def _writefile(self, fp):
        z = zipfile.ZipFile(fp, 'w')

        mselect = self.ui.mselect
        for n in range(mselect.count()):
            docid = unicode(mselect.itemData(n).toString())
            code = unicode(self.editor.documents[docid])
            arcname = '##%5s##__%s' % (n, docid)
            code = self.cleancode(code)
            self.editor.documents[docid] = code
            z.writestr(arcname, code.encode('utf-8'))

        historyname = '@@history@@'
        history = '\n'.join(self.interpretereditor.history)
        z.writestr(historyname, history.encode('utf-8'))

        z.close()

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

        self._writefile(self._filepath)

        self._modified = False
        for tdoc in self.editor.textdocuments.values():
            tdoc.setModified(False)
        self.setWindowModified(False)

        self.addrecentfile(self._filepath)

        self._verify_saved(self._filepath)

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

        fp = unicode(QtGui.QFileDialog.getSaveFileName(self, 'Save As', fdir))
        if fp:
            self._filepath = fp
            self._fdir, _ = os.path.split(fp)
        else:
            return False

        retval = self._savestate()

        fdir, fname = os.path.split(self._filepath)
        windowtitle = '%s [*] - Pynguin' % fname
        self.setWindowTitle(windowtitle)
        self.setWindowModified(False)

        return retval

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

        fp = unicode(QtGui.QFileDialog.getOpenFileName(self, 'Open file', fdir, 'Text files (*.pyn)'))
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
            data = data.decode('utf-8')
            if ename.startswith('##'):
                hdr = ename[0:9]
                if hdr.startswith('##') and hdr.endswith('##'):
                    title = ename[11:]
                    self.editor.add(data)
                    if data.startswith('def ') or data.startswith('class '):
                        try:
                            exec data in self.interpreter_locals
                        except Exception, e:
                            print 'problem', e
                            print 'in...'
                            line1 = data.split('\n')[0]
                            print unicode(line1)
            elif ename.startswith('@@history@@'):
                history = data.split('\n')
                self.interpretereditor.history = history

        self.ui.mselect.setCurrentIndex(0)
        self.changedoc(0)

        self._modified = False
        fdir, fname = os.path.split(fp)
        windowtitle = '%s [*] - Pynguin' % fname
        self.setWindowTitle(windowtitle)
        self.setWindowModified(False)

        if add_to_recent:
            self.addrecentfile(self._filepath)

    def _verify_saved(self, fp):
        '''verify that the saved file contains the correct data.'''
        z = zipfile.ZipFile(fp, 'r')
        for ename in z.namelist():
            fo = z.open(ename, 'rU')
            data = fo.read()
            data = data.decode('utf-8')
            if ename.startswith('##'):
                hdr = ename[0:9]
                if hdr.startswith('##') and hdr.endswith('##'):
                    docid = ename[11:]
                    if data != self.editor.documents[docid]:
                        QtGui.QMessageBox.warning(self,
                                'Unable to save',
                                'Files not saved!')
                        break

    def export(self):
        '''save the current drawing'''
        if self._fdir is None:
            fdir = QtCore.QString(os.path.abspath(os.path.curdir))
        else:
            fdir = self._fdir

        fp = unicode(QtGui.QFileDialog.getSaveFileName(self, 'Export Image', fdir))
        if fp:
            root, ext = os.path.splitext(fp)
            if not ext:
                ext = '.png'
                fp += ext
            self._fdir, _ = os.path.split(fp)
        else:
            return False

        for pynguin in self.pynguins:
            pynguin.gitem.hide()

        scene = self.scene
        view = scene.view

        ibr = scene.itemsBoundingRect()

        tl = ibr.topLeft()
        tlx, tly = tl.x(), tl.y()
        tlx -= 20
        tly -= 20
        tlp = QtCore.QPointF(tlx, tly)
        ibr.setTopLeft(tlp)

        br = ibr.bottomRight()
        brx, bry = br.x(), br.y()
        brx += 20
        bry += 20
        brp = QtCore.QPointF(brx, bry)
        ibr.setBottomRight(brp)

        scene.setSceneRect(scene.sceneRect().united(ibr))

        src = scene.sceneRect()
        szf = src.size()
        sz = QtCore.QSize(szf.width(), szf.height())
        self._i = i = QtGui.QImage(sz, QtGui.QImage.Format_ARGB32)
        p = QtGui.QPainter(i)
        ir = i.rect()
        irf = QtCore.QRectF(0, 0, src.width(), src.height())

        scene.render(p, irf, src)
        if not i.save(fp):
            if ext not in ('.png', '.jpg', '.jpeg', '.tga'):
                msg = 'Unsupported format.\n\nTry using filename.png'
            else:
                msg = 'Cannot export image.'
            QtGui.QMessageBox.warning(self,
                                'Unable to save',
                                msg)

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
        docid = unicode(self.ui.mselect.itemData(idx).toString())
        if docid in self.editor.documents:
            self.editor.switchto(docid)
            self.editor.setFocus()

    def removedoc(self):
        '''throw away the currently displayed editor document'''
        mselect = self.ui.mselect
        idx = mselect.currentIndex()
        docname = unicode(mselect.itemText(idx))
        mselect.removeItem(idx)
        if mselect.count():
            self.changedoc(0)
            mselect.setCurrentIndex(0)
        else:
            self.editor._doc.setPlainText('')
            self.newdoc()

        if docname in self.editor.documents:
            del self.editor.documents[docname]

        self._modified = True
        self.setWindowModified(True)

    def cleancode(self, code):
        '''fix up the code a bit first...
        make sure the last line ends with newline
        and make sure the code does not end with
        lines that have only indentation
        '''
        lines = code.split('\n')
        lines.reverse()
        blankend = True
        rewrite = []
        for line in lines:
            if blankend and (not line or line.isspace()):
                pass
            else:
                blankend = False
                line = line.rstrip()
                rewrite.append(line)

        rewrite.reverse()
        code = '%s\n' % '\n'.join(rewrite)
        return code

    def testcode(self):
        '''exec the code in the current editor window and load it in
            to the interpreter local namespace

            If the first line looks like a function definition, use
            it to feed a line to the interpreter set up to call the
            function.
        '''
        self.editor.savecurrent()
        docname = unicode(self.ui.mselect.currentText())
        idx = self.ui.mselect.currentIndex()
        docid = unicode(self.ui.mselect.itemData(idx).toString())
        code = unicode(self.editor.documents[docid])

        code = self.cleancode(code)

        try:
            compile(code, 'current file', 'exec')
        except SyntaxError, e:
            self.editor.selectline(e.lineno)
            self.interpretereditor.write('Syntax Error in line %s\n' % e.lineno)
            self.interpretereditor.write('>>> ')
            self.editor.setFocus()
        else:
            self.interpretereditor.setFocus()
            if self.interpretereditor.cmdthread is None:
                self.interpretereditor.cmdthread = CmdThread(self.interpretereditor, code)
                cmdthread = self.interpretereditor.cmdthread
                cmdthread.finished.connect(self.interpretereditor.testthreaddone)
                cmdthread.start()

                line0 = code.split('\n')[0]
                if line0.startswith('def ') and line0.endswith(':'):
                    self.interpretereditor.movetoend()
                    self.interpretereditor.erasetostart()

                    firstparen = line0.find('(')
                    lastparen = line0.rfind(')')
                    if firstparen > -1 and lastparen > -1:
                        tocall = line0[4:lastparen+1]
                        funcname = line0[4:firstparen]
                        if funcname == 'onclick':
                            self.pynguin.__class__.onclick = self.interpreter_locals['onclick']
                            self.interpretereditor.write('# set onclick handler\n')
                            self.interpretereditor.write('>>> ')
                        else:
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
            r, g, b, a = ncolor.getRgb()
            self.pynguin.color(r, g, b)
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
        Pynguin._drawspeed_pending = 2 * speed
        Pynguin._turnspeed_pending = 4 * speed
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

    def wordwrap(self):
        checked = self.ui.actionWordwrap.isChecked()
        if not checked:
            self.editor.setWordWrapMode(QtGui.QTextOption.NoWrap)
        else:
            self.editor.setWordWrapMode(QtGui.QTextOption.WrapAtWordBoundaryOrAnywhere)
        settings = QtCore.QSettings()
        settings.setValue('editor/wordwrap', checked)

    def zoomineditor(self):
        self.editor.zoomin()

    def zoomouteditor(self):
        self.editor.zoomout()

    def about(self):
        AboutDialog(self.app).exec_()

    def reportbug(self):
        QtGui.QDesktopServices().openUrl(QtCore.QUrl(bug_url))


class Scene(QtGui.QGraphicsScene):
    def __init__(self):
        left = -300
        top = -300
        width = 600
        height = 600

        QtGui.QGraphicsScene.__init__(self)
        self.setSceneRect(left, top, width, height)
        color = QtGui.QColor(130, 130, 160)
        brush = QtGui.QBrush(color)
        self.setBackgroundBrush(brush)

    #def drawBackground(self, painter, rect):
        #QtGui.QGraphicsScene.drawBackground(self, painter, rect)
        #painter.drawEllipse(rect)
