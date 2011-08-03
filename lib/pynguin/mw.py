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
import time
from math import pi
import glob
import zipfile
import logging
logger = logging.getLogger('PynguinLogger')

from bidict import bidict


from PyQt4 import QtGui, QtCore, uic
from PyQt4.Qt import QHBoxLayout

from pynguin import Pynguin, pynguin_functions, interpreter_protect
import util
from util import sign, get_datadir, get_docdir
from codearea import CodeArea
from interpreter import Interpreter, CmdThread, Console
from about import AboutDialog
import conf

datadir = get_datadir()
uidir = os.path.join(datadir, 'ui')
docdir = get_docdir()


class MainWindow(QtGui.QMainWindow):
    def __init__(self, app):
        self.app = app
        self.paused = False
        self.svgrenderer = util.SvgRenderer(self.app)
        self.rend = self.svgrenderer.getrend()

        self._fdir = os.path.expanduser('~')
        self._filepath = None
        self._modified = False

        self._mainthread = QtCore.QThread.currentThread()

        uifile = 'pynguin.ui'
        uipath = os.path.join(uidir, uifile)
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
        view.mouseReleaseEvent = self.mouserelease

        self.setup_speed_choices()
        self.speedgroup = QtGui.QActionGroup(self)
        self.speedgroup.addAction(self.ui.actionSlow)
        self.speedgroup.addAction(self.ui.actionMedium)
        self.speedgroup.addAction(self.ui.actionFast)
        self.speedgroup.addAction(self.ui.actionInstant)
        self.speedgroup.setExclusive(True)
        self.speedgroup.triggered.connect(self.speedMenuEvent)

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

        self._setup_pendown_choices()
        self.pengroup = QtGui.QActionGroup(self)
        self.pengroup.addAction(self.ui.actionPenUp)
        self.pengroup.addAction(self.ui.actionPenDown)
        self.pengroup.setExclusive(True)
        self.pengroup.triggered.connect(self.setPen)

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

        self.setup_avatar_choices()
        self.viewgroup = QtGui.QActionGroup(self)
        self.viewgroup.addAction(self.ui.actionPynguin)
        self.viewgroup.addAction(self.ui.actionArrow)
        self.viewgroup.addAction(self.ui.actionRobot)
        self.viewgroup.addAction(self.ui.actionTurtle)
        self.viewgroup.addAction(self.ui.actionHidden)
        self.viewgroup.setExclusive(True)
        self.viewgroup.triggered.connect(self.setImageEvent)

        self._setup_pendown_choices()
        self.pengroup = QtGui.QActionGroup(self)
        self.pengroup.addAction(self.ui.actionPenUp)
        self.pengroup.addAction(self.ui.actionPenDown)
        self.pengroup.setExclusive(True)
        self.pengroup.triggered.connect(self.setPen)

        self._setup_fill_choices()
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
        self._leftdragstart = None

        self.watcher = QtCore.QFileSystemWatcher(self)
        self.watcher.fileChanged.connect(self._filechanged)
        self._watchdocs = {}
        self._writing_external = None

    def setup_interpreter_locals(self):
        ilocals = self.interpreter_locals
        ilocals.update(PI=pi,
                        Pynguin=Pynguin,
                        pynguin=self.pynguin,
                        p=self.pynguin,
                        pynguins=self.pynguins,
                        history=self.history,
                        util=util,)
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

        if self._leftdragstart is None:
            ev.accept()
            return

        buttons = ev.buttons()
        if buttons & QtCore.Qt.LeftButton:
            pos = ev.posF()
            dpos = self._leftdragstart - pos
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
        'return the current center of the view'
        ctr = self._viewrect().center()
        return ctr

    def _centerview(self, ctr=None):
        'set _cx and _cy to the given coord or to the current view center'
        if ctr is None:
            ctr = self._viewcenter()
        self._cx = ctr.x()
        self._cy = ctr.y()

    def settrack(self):
        track = self.ui.actionTrack.isChecked()

        if track:
            Pynguin.track_main_pynguin = True
            self.pynguin.gitem.track()
        else:
            Pynguin.track_main_pynguin = False

        settings = QtCore.QSettings()
        settings.setValue('pynguin/track', track)

    def onclick(self, ev):
        QtGui.QGraphicsView.mousePressEvent(self.scene.view, ev)

        button = ev.button()
        if not ev.isAccepted() and button==QtCore.Qt.LeftButton:
            self.leftclick(ev)

        elif button==QtCore.Qt.RightButton:
            self.rightclick(ev)

        self.interpretereditor.setFocus()

    def leftclick(self, ev):
        if not ev.isAccepted():
            self._leftdragstart = ev.posF()
            self._dragstartcenter = self._viewcenter()
        else:
            self._leftdragstart = None

    def mouserelease(self, ev):
        QtGui.QGraphicsView.mouseReleaseEvent(self.scene.view, ev)
        self._leftdragstart = None

    def rightclick(self, ev):
        evpos = ev.pos()
        scpos = self.scene.view.mapToScene(evpos)
        for pyn in self.pynguins:
            if pyn.respond_to_mouse_click:
                if pyn is self.pynguin and 'onclick' in self.interpreter_locals:
                    onclick = self.interpreter_locals['onclick']
                else:
                    onclick = pyn.onclick
                onclick(scpos.x(), scpos.y())
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

        examplesrel = 'examples'
        examplespath = os.path.join(docdir, examplesrel)
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

    def settings(self):
        'open the settings dialog'
        import settings
        s = settings.Settings(self)
        r = s.exec_()
        if r:
            settings = QtCore.QSettings()
            ui = s.ui

            savesingle = ui.savesingle.isChecked()
            settings.setValue('file/savesingle', savesingle)

            reloadexternal = ui.reloadexternal.isChecked()
            settings.setValue('file/reloadexternal', reloadexternal)
            autorun = ui.autorun.isChecked()
            settings.setValue('file/autorun', autorun)

            bfp = ui.backupfolderpath.text()
            settings.setValue('file/backupfolderpath', bfp)
            bfn = ui.backupfilename.text()
            settings.setValue('file/backupfilename', bfn)
            brate = ui.backuprate.value()
            settings.setValue('file/backuprate', brate)
            # hold on to the old backupkeep value. If it was zero
            # need to start the autosave timer
            bkeep0, ok = settings.value('file/backupkeep', 5).toInt()
            if not ok:
                bkeep0 = 5
            bkeep = ui.backupkeep.value()
            settings.setValue('file/backupkeep', bkeep)
            if not bkeep0:
                QtCore.QTimer.singleShot(brate*60000, self.autosave)

            reset = ui.testrun_reset.isChecked()
            settings.setValue('editor/testrun_reset', reset)
            mainfirst = ui.editor_mainfirst.isChecked()
            settings.setValue('editor/mainfirst', mainfirst)
            rev = ui.testall_reverse.isChecked()
            settings.setValue('editor/testall_reverse', rev)
            autocall = ui.testall_autocall.isChecked()
            settings.setValue('editor/testall_autocall', autocall)

            quiet = ui.quietinterrupt.isChecked()
            settings.setValue('console/quietinterrupt', quiet)

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

        speed, ok = settings.value('pynguin/speed', 10).toInt()
        if ok:
            self.set_speed(speed)
            self.sync_speed_menu(speed)

        # remember the saved avatar
        imageid = settings.value('pynguin/avatar', 'pynguin').toString()

        # set up any custom avatars
        n = settings.beginReadArray('pynguin/custom_avatars')
        for i in range(n):
            settings.setArrayIndex(i)
            idp = settings.value('idpath').toString()
            self.set_pynguin_avatar(idp)
        settings.endArray()

        # then set the saved avatar that we remembered earlier
        self.set_pynguin_avatar(imageid)
        self._sync_avatar_menu(imageid)

        track = settings.value('pynguin/track', False).toBool()
        if track:
            self.ui.actionTrack.setChecked(True)
            self.settrack()

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
        if fp.endswith('.pyn'):
            self._new()
            self._filepath = fp
            self._openfile(fp)
        elif fp.endswith('.py'):
            self._openfile(fp)
        elif fp.endswith('_pynd'):
            self._new()
            self._filepath = fp
            self._opendir(fp)
        else:
            try:
                self._openfile(fp)
            except:
                try:
                    self._opendir(fp)
                except:
                    QtGui.QMessageBox.information(self,
                            'Open failed',
                            'Unable to open file:\n\n%s' % fp)

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
            ret = QtGui.QMessageBox.warning(self,
                    self.tr('Save Changes?'),
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
        settings = QtCore.QSettings()
        backupkeep, ok = settings.value('file/backupkeep', 5).toInt()
        if not ok or not backupkeep:
            return

        bfp = str(settings.value('file/backupfolderpath', '').toString())
        bfp = bfp or self._fdir
        bfn = str(settings.value('file/backupfilename', 'backup~%s.pyn').toString())
        fp = os.path.join(bfp, bfn % '')
        if self.writeable(fp, savesingle=True):
            self.editor.savecurrent()
            self._writefile01(fp, backup=True)
        else:
            QtGui.QMessageBox.warning(self,
                    'Autosave failed',
                    '''Cannot complete autosave.
Autosave disabled.
Check configuration!''')
            settings.setValue('file/backupkeep', 0)
            return

        if backupkeep > 1:
            for fn in range(backupkeep, 1, -1):
                fpsrc = os.path.join(bfp, bfn % (fn-1))
                fpdst = os.path.join(bfp, bfn % fn)
                if os.path.exists(fpsrc):
                    os.rename(fpsrc, fpdst)
        else:
            fpsrc = os.path.join(bfp, bfn % 1)

        os.rename(fp, fpsrc)

        brate, ok = settings.value('file/backuprate', 3).toInt()
        if not ok:
            brate = 3
        QtCore.QTimer.singleShot(brate*60000, self.autosave)

    def _correct_filename(self, fp=None):
        'make sure file name ends with .pyn'
        if fp is None:
            fp = self._filepath
        r, ext = os.path.splitext(fp)
        if ext != '.pyn':
            ext = '.pyn'
        return r + ext

    def _writefile(self, fp):
        'Write file list files and history as a zip file called .pyn'
        z = zipfile.ZipFile(fp, 'w')

        mselect = self.ui.mselect
        for n in range(mselect.count()):
            docid = unicode(mselect.itemData(n).toString())
            code = unicode(self.editor.documents[docid])
            arcname = '##%05d##__%s' % (n, docid)
            code = self.cleancode(code)
            self.editor.documents[docid] = code
            z.writestr(arcname, code.encode('utf-8'))

        historyname = '@@history@@'
        history = '\n'.join(self.interpretereditor.history)
        z.writestr(historyname, history.encode('utf-8'))

        z.close()

    def _writefile01(self, fp, backup=False):
        '''Write file list files and history as a zip file called .pyn

        Version 01

        Puts all files in to a folder to make it match the writedir
        method better.

        '''
        VERSION = 'pyn01'

        _, fn = os.path.split(fp)
        fbase, _ = os.path.splitext(fn)
        if not fbase.endswith('_pynd'):
            fbase = fbase + '_pynd'

        z = zipfile.ZipFile(fp, 'w')

        manifest = []

        mselect = self.ui.mselect
        for n in range(mselect.count()):
            docid = unicode(mselect.itemData(n).toString())
            textdoc = self.editor.textdocuments[docid]
            code = unicode(self.editor.documents[docid])
            code = self.cleancode(code)
            self.editor.documents[docid] = code

            if not backup and hasattr(textdoc, '_filepath'):
                efp = textdoc._filepath
                manifest.append(efp)

                if efp.startswith('_@@'):
                    dirname, _ = os.path.split(fp)
                    efp = efp.replace('_@@', dirname)
                logger.info('external: %s' % efp)
                self._writing_external = efp
                f = open(efp, 'w')
                f.write(code.encode('utf-8'))
                f.close()
                self._writing_external = None
                continue

            arcname = '%05d.py' % n

            zipi = zipfile.ZipInfo()
            zipi.filename = os.path.join(fbase, arcname)
            manifest.append(zipi.filename)
            zipi.compress_type = zipfile.ZIP_DEFLATED
            zipi.date_time = time.localtime()
            zipi.external_attr = 0644 << 16
            zipi.comment = VERSION
            z.writestr(zipi, code.encode('utf-8'))

        historyname = '@@history@@'
        history = '\n'.join(self.interpretereditor.history)

        zipi = zipfile.ZipInfo()
        zipi.filename = os.path.join(fbase, historyname)
        zipi.compress_type = zipfile.ZIP_DEFLATED
        zipi.date_time = time.localtime()
        zipi.external_attr = 0644 << 16
        zipi.comment = VERSION
        z.writestr(zipi, history.encode('utf-8'))

        manifestname = '@@manifest@@'
        zipi = zipfile.ZipInfo()
        zipi.filename = os.path.join(fbase, manifestname)
        zipi.compress_type = zipfile.ZIP_DEFLATED
        zipi.date_time = time.localtime()
        zipi.external_attr = 0644 << 16
        zipi.comment = VERSION
        manifeststr = '\n'.join(manifest)
        z.writestr(zipi, manifeststr.encode('utf-8'))

        z.close()

    def _related_dir(self, fp=None):
        '''return the directory name related to path fp
        This is the directory that will be used for storing
            the files when not in savesingle mode.
        '''
        if fp is None:
            fp = self._filepath

        dirname, fname = os.path.split(fp)
        fbase, fext = os.path.splitext(fname)
        fpd = os.path.join(dirname, fbase+'_pynd')

        return fpd

    def _writedir(self, fp):
        'Write file list files and history file in to a directory'

        fpd = self._related_dir(fp)
        _, dirname = os.path.split(fpd)

        mselect = self.ui.mselect
        count = mselect.count()
        for n in range(count):
            docid = unicode(mselect.itemData(n).toString())
            textdoc = self.editor.textdocuments[docid]
            if not hasattr(textdoc, '_filepath'):
                arcname = '%05d.py' % n
                textdoc._filepath = os.path.join('_@@', dirname, arcname)
                logger.info('dfp %s' % textdoc._filepath)
            else:
                logger.info('DFP %s' % textdoc._filepath)

        self._writefile01(fp)

        for n in range(count):
            docid = unicode(mselect.itemData(n).toString())
            textdoc = self.editor.textdocuments[docid]
            if hasattr(textdoc, '_filepath'):
                if textdoc._filepath.startswith('_@@'):
                    del textdoc._filepath

    def _savestate(self):
        '''write out the files in the editor window, and keep the list
            of history entries.

        if configured to use a single file:
            All of this is packed up in to a zip
            file and given a .pyn filename ending.

        if configured for directory of files:
            The files will be saved in a separate directory.
            The directory will end in _pynd
            A .pyn file will also be saved indexing the contents and
                allowing the files to be easily re-loaded.

        '''

        self.editor.savecurrent()

        settings = QtCore.QSettings()
        savesingle = settings.value('file/savesingle', True).toBool()

        if self.writeable(self._filepath):
            if savesingle:
                self._writefile01(self._filepath)
            else:
                self._writedir(self._filepath)
        else:
            QtGui.QMessageBox.warning(self,
                    'Save failed',
                    '''Cannot write to selected file.''')
            self._filepath = None
            return False

        self._modified = False
        for tdoc in self.editor.textdocuments.values():
            tdoc.setModified(False)
        self.setWindowModified(False)

        self.addrecentfile(self._filepath)

        if savesingle:
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

        fp = unicode(QtGui.QFileDialog.getSaveFileName(self,
                        'Save As', fdir,
                        'Text files (*.pyn)'))

        if fp:
            settings = QtCore.QSettings()
            savesingle = settings.value('file/savesingle', True).toBool()

            fp = self._correct_filename(fp)
            dirname, fname = os.path.split(fp)
            if not savesingle:
                fpd = self._related_dir(fp)
                if not os.path.exists(fpd):
                    os.mkdir(fpd)
                elif os.path.exists(fpd) and not self.overwrite(fpd):
                    return False
                elif os.listdir(fpd):
                    import shutil
                    shutil.rmtree(fpd)
                    os.mkdir(fpd)

            self._filepath = fp
            self._fdir = dirname

        else:
            return False

        retval = self._savestate()

        if retval:
            fdir, fname = os.path.split(self._filepath)
            windowtitle = '%s [*] - Pynguin' % fname
            self.setWindowTitle(windowtitle)
            self.setWindowModified(False)

        return retval

    def overwrite(self, fname):
        '''ask the user if they want to overwrite an existing file
            or directory.

        '''
        ret = QtGui.QMessageBox.warning(self,
                self.tr('Overwrite?'),
                self.tr("The Directory already exists:\n%s\n"
                        "Do you want to delete it and all contents?" % fname),
                QtGui.QMessageBox.Yes | QtGui.QMessageBox.Default,
                QtGui.QMessageBox.No,
                QtGui.QMessageBox.Cancel | QtGui.QMessageBox.Escape)
        if ret == QtGui.QMessageBox.Yes:
            return True
        elif ret == QtGui.QMessageBox.Cancel:
            return False

    def writeable(self, fp, savesingle=None):
        'try to write to the given path. return True if sucessful.'
        try:
            fd = open(fp, 'w')
            fd.write('test')
            fd.close()
            os.remove(fp)
        except IOError:
            return False
        else:
            return True

        if savesingle is not None and savesingle:
            savesingle = True
        else:
            settings = QtCore.QSettings()
            savesingle = settings.value('file/savesingle', True).toBool()

        if not savesingle:
            fpd = self._related_dir(fp)
            if not os.path.exists(fpd):
                return False
            fp = os.path.join(fpd, 'test')
            return self.writeable(fp, False)
        else:
            return True

    def open(self):
        '''read in a previously written set of files,
            or a single python source file.

        If the file is a lone python source file, no further processing
            will occur. However, if the file has been loaded in pynguin
            previously (it is being loaded from a .pyn or a _pynd):

        Any documents that look like function or class definitions will
            be exec'd to load them in to the interpreter local namespace.
        Any current history will be lost and replaced with the
            history loaded from the file.
        '''
        if not self.maybe_save():
            return

        if self._fdir is None:
            fdir = QtCore.QString(os.path.abspath(os.path.curdir))
        else:
            fdir = self._fdir

        logger.info('open at %s' % fdir)

        fp = unicode(QtGui.QFileDialog.getOpenFileName(self, 'Open file', fdir, 'Text files (*.pyn *.py)'))

        if fp:
            if not os.path.exists(fp):
                QtGui.QMessageBox.information(self,
                            'Does not exist',
                            'File does not exist:\n\n%s' % fp)
                return

            self._fdir, _ = os.path.split(fp)

            if not fp.endswith('.py'):
                self._new()
                self._filepath = fp

            self._openfile(fp)

    def _update_after_open(self, fp, add_to_recent=False):
        self.ui.mselect.setCurrentIndex(0)
        self.changedoc(0)

        self._modified = False
        fdir, fname = os.path.split(fp)
        windowtitle = '%s [*] - Pynguin' % fname
        self.setWindowTitle(windowtitle)
        self.setWindowModified(False)

        if add_to_recent:
            self.addrecentfile(self._filepath)

    def _openfile(self, fp, add_to_recent=True):
        '''Open the selected file.

        If the file is python source (.py) open the file and
            add it as a new page in the editor window.

        If the file is a pynguin archive (.pyn) open it and load
            its contents to the correct places.

            First determine which file format version is used in
            the file, then dispatch to the correct function.

        '''
        if fp.endswith('.pyn'):
            z = zipfile.ZipFile(fp, 'r')
            infos = z.infolist()
            info = infos[0]

            logger.info('Opening file with version: "%s"' % info.comment)

            if not info.comment:
                self._openfile00(fp)
            else:
                if info.comment == 'pyn01':
                    self._openfile01(fp)
                else:
                    QtGui.QMessageBox.information(self,
                            'Unknown Format',
                            'Unknown file format:\n\n"%s"' % info.comment)
                    return

        if fp.endswith('.py'):
            doc = self.editor.addexternal(fp)
            self.addrecentfile(fp)
            self._modified = True
            self.setWindowModified(True)
            self._addwatcher(fp, doc)
        else:
            self._update_after_open(fp, add_to_recent)

    def _addwatcher(self, fp, doc):
            self.watcher.addPath(fp)
            self._watchdocs[str(fp)] = doc

    def _remwatcher(self, fp):
        self.watcher.removePath(fp)

    def _filechanged(self, fp):
        '''called when an external file has changed on disk.
        '''
        logger.info('_fc %s' % fp)
        if str(fp) == str(self._writing_external):
            # Ignore notification when saving the file
            return

        settings = QtCore.QSettings()
        autorefresh = settings.value('file/reloadexternal', True).toBool()
        if autorefresh:
            doc = self._watchdocs[str(fp)]
            txt = open(fp).read()
            txt = txt.decode('utf-8')
            doc.setPlainText(txt)
            autorun = settings.value('file/autorun', False).toBool()
            if autorun:
                self.interpreter.runcode(txt)

    def _loaddata(self, data):
        self.editor.add(data)
        if data.startswith('def ') or data.startswith('class '):
            if data[4:12] == 'onclick(':
                # don't install onclick handlers when loading
                pass
            else:
                try:
                    exec data in self.interpreter_locals
                except Exception, e:
                    print 'problem', e
                    print 'in...'
                    line1 = data.split('\n')[0]
                    print unicode(line1)

    def _loadhistory(self, data):
        history = data.split('\n')
        self.interpretereditor.history = history

    def _shouldload00(self, ename):
        '''tries to load both original file format and any
            unknown format file.
        '''
        return ename.startswith('##')

    def _openfile00(self, fp):
        'Used to open files from version < 0.10'
        z = zipfile.ZipFile(fp, 'r')
        for ename in z.namelist():
            fo = z.open(ename, 'rU')
            data = fo.read()
            data = data.decode('utf-8')
            if self._shouldload00(ename):
                self._loaddata(data)
            elif ename.startswith('@@history@@'):
                self._loadhistory(data)

    def _shouldload01(self, fp):
        'return true if _openfile01 should load the file contents'
        edir, ename = os.path.split(fp)
        return len(ename)==8 and \
                ename[:5].isdigit() and \
                ename.endswith('.py')

    def _openfile01(self, fp):
        'used to open files in version 0.10 (file vers. pyn01)'
        fpd, _ = os.path.split(fp)
        z = zipfile.ZipFile(fp, 'r')
        namelist = z.namelist()
        hasmanifest = False
        for ename in namelist:
            if '@@manifest@@' in ename:
                fo = z.open(ename, 'rU')
                data = fo.read()
                data = data.decode('utf-8')
                namelist = data.split('\n')
                hasmanifest = True

        if not hasmanifest:
            namelist.sort()

        for ename in namelist:
            logger.info('loading %s' % ename)
            if ename.startswith('_@@'):
                n = ename[4:]
                np = os.path.join(fpd, n)
                logger.info('NP %s' % np)
                fo = open(np, 'rU')

            elif os.path.isabs(ename):
                try:
                    self._openfile(ename)
                except IOError:
                    self._loaddata('Could not load:\n%s' % ename)
                    self.editor._doc._title = 'NOT LOADED'
                    self.editor._doc._filepath = ename
                    self.editor.settitle('NOT LOADED')
                    continue
            else:
                fo = z.open(ename, 'rU')

            data = fo.read()
            data = data.decode('utf-8')
            if self._shouldload01(ename):
                self._loaddata(data)
            elif '@@history@@' in ename:
                self._loadhistory(data)

    def _opendir(self, d):
        files = os.listdir(d)
        manifestname = '@@manifest@@'
        if manifestname in files:
            manifp = os.path.join(d, manifestname)
            maniff = open(manifp)
            manifest = maniff.read()
            files = manifest.split('\n')
            files = [os.path.join(d, f) for f in files if f]
        else:
            files.sort()

        for ename in files:
            fp = os.path.join(d, ename)
            fo = open(fp, 'rU')
            data = fo.read()
            data = data.decode('utf-8')
            if self._shouldload01(ename):
                self._loaddata(data)
            elif ename == '@@history@@':
                self._loadhistory(data)

        self._update_after_open(d)

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

        if hasattr(self.editor._doc, '_title'):
            external = True
            fp = self.editor._doc._filepath
        else:
            external = False

        if not external:
            ret = QtGui.QMessageBox.warning(self, 'Are you sure?',
                    'This page will be removed permanently.\n'
                    'Are you sure you want to remove this page?',
                    QtGui.QMessageBox.Yes | QtGui.QMessageBox.Default,
                    QtGui.QMessageBox.No,
                    QtGui.QMessageBox.Cancel | QtGui.QMessageBox.Escape)

        if not external and ret in (QtGui.QMessageBox.No,
                                        QtGui.QMessageBox.Cancel):
            return
        elif external or ret == QtGui.QMessageBox.Yes:
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

            if external:
                self._remwatcher(fp)

    def nextdoc(self):
        self.editor.shownext()

    def prevdoc(self):
        self.editor.showprev()

    def promotedoc(self):
        self.editor.promote()

    def demotedoc(self):
        self.editor.demote()

    def toggle_editor(self):
        if self.interpretereditor.hasFocus():
            self.editor.setFocus()
        else:
            self.interpretereditor.setFocus()

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

    def findmain(self, code):
        '''returns information about the main function or class in
            the given code.

        "Main" will depend on the settings and will either be the first
            function or class defined on the page, or the last one.

        returns a dictionary of:
            kind: 'function', 'class'
            name: function or class name
            params: string containing all parameters
            nodefault: list of params that do not have a default value
        '''

        settings = QtCore.QSettings()
        mainfirst = settings.value('editor/mainfirst').toBool()
        lines = code.split('\n')
        if not mainfirst:
            lines.reverse()
        for line in lines:
            firstparen = line.find('(')
            lastparen = line.rfind(')')
            if line.startswith('def ') and line.endswith(':'):
                kind = 'function'
                name = line[4:firstparen]
            elif line.startswith('class ') and line.endswith(':'):
                kind = 'class'
                name = line[6:firstparen]
            else:
                continue

            if kind=='function' and firstparen > -1 and lastparen > -1:
                params = line[firstparen+1:lastparen]
                func = self.interpreter_locals.get(name, None)
                nodefault = []
                if func is not None:
                    defaults = self._plist(func)
                    if defaults:
                        for param, d in defaults:
                            if d is None:
                                nodefault.append(param)
            elif kind == 'class':
                c = self.interpreter_locals.get(name, None)
                nodefault = []
                params = ''
                if c is not None:
                    func = getattr(c, '__init__', None)
                    if func is not None:
                        defaults = self._plist(func)
                        if defaults:
                            del defaults[0] # self
                            count = len(defaults)
                            for i, (param, d) in enumerate(defaults):
                                params += param
                                if d is None:
                                    nodefault.append(param)
                                else:
                                    params += '=%s' % d
                                if i < count-1:
                                    params += ', '

            return (kind, name, params, nodefault)

        return None, None, None, None

    def _plist(self, f):
        '''given function object,
            return a list of [(arg name: default value or None), ...]
        '''
        parameter_defaults = []
        defaults = f.func_defaults
        if defaults is not None:
            defaultcount = len(defaults)
        else:
            defaultcount = 0
        argcount = f.func_code.co_argcount
        for i in xrange(f.func_code.co_argcount):
            name = f.func_code.co_varnames[i]
            value = None
            if i >= argcount - defaultcount:
                value = defaults[i - (argcount - defaultcount)]
            parameter_defaults.append((name, value))
        return parameter_defaults

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

        error = None

        try:
            compile(code, 'current file', 'exec')
        except SyntaxError, e:
            self.editor.selectline(e.lineno)
            self.interpretereditor.clearline()
            self.interpretereditor.write('Syntax Error in line %s\n' % e.lineno)
            self.interpretereditor.write('>>> ')
            self.editor.setFocus()
            error = 1
        else:
            self.interpretereditor.setFocus()
            if self.interpretereditor.cmdthread is None:
                self.interpretereditor.cmdthread = CmdThread(self.interpretereditor, code)
                cmdthread = self.interpretereditor.cmdthread
                cmdthread.finished.connect(self.interpretereditor.testthreaddone)
                cmdthread.start()

                kind, name, params, nodefault = self.findmain(code)
                if kind is not None:
                    self.interpretereditor.clearline()
                    if kind == 'function':
                        tocall = '%s(%s)' % (name, params)
                    elif kind == 'class':
                        varname = name.lower()
                        if varname == name:
                            self.interpretereditor.write('# Class names should be capitalized \n')
                            self.interpretereditor.write('>>> ')
                            varname = varname[0]
                        tocall = '%s = %s(%s)' % (varname, name, params)

                    if kind=='function' and name == 'onclick':
                        self.interpretereditor.write('# set onclick handler\n')
                        self.interpretereditor.write('>>> ')
                    else:
                        self.interpretereditor.addcmd(tocall, force=True)
            else:
                self.interpretereditor.write('not starting...\n')
                self.interpretereditor.write('code already running\n')
                self.interpretereditor.write('>>> ')

        self.interpretereditor.setFocus()
        return error

    def testall(self):
        '''Test/Run each editor page in order.

        If any page throws an error, progress stops, the editor
        switches to that page and highlights the error.
        '''

        ie = self.interpretereditor
        settings = QtCore.QSettings()
        rev = settings.value('editor/testall_reverse', False).toBool()
        autorun = settings.value('editor/testall_autocall', False).toBool()
        reset = settings.value('editor/testrun_reset', True).toBool()

        count = self.ui.mselect.count()
        for i in range(count):
            if not rev:
                idx = i
            else:
                idx = count - i - 1
            docid = unicode(self.ui.mselect.itemData(idx).toString())
            if docid in self.editor.documents:
                ie.spin(0)
                self.editor.switchto(docid)
                self.editor.setFocus()
                if reset:
                    ie.clearline()
                    ie.addcmd('reset()')
                    ie.spin(5)
                    self.interpretereditor.go()
                ie.spin(0)
                ie.clearline()
                if self.testcode():
                    break
                ie.spin(5, delay=0.1)

                if autorun:
                    code = unicode(self.editor.documents[docid])
                    code = self.cleancode(code)
                    kind, name, params, nodefault = self.findmain(code)
                    missing_vars = []
                    if nodefault:
                        for var in nodefault:
                            if var not in self.interpreter_locals:
                                missing_vars.append(var)

                    if missing_vars:
                        ie.write('\n>>> ')
                        for var in missing_vars:
                            ie.write('# missing %s \n' % var)
                            ie.write('>>> ')
                        ie.spin(5)

                    else:
                        ie.go()

        ie.clearline()

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

    def _setup_pendown_choices(self):
        choices = ((self.ui.actionPenUp, False),
                    (self.ui.actionPenDown, True))
        self._pendowns = bidict(choices)

    def _sync_pendown_menu(self, choice):
        action = self._pendowns.inv.get(choice)
        action.setChecked(True)

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

    def _setup_fill_choices(self):
        choices = ((self.ui.actionFill, 'fill'),
                    (self.ui.actionNofill, 'nofill'))
        self._fills = bidict(choices)

    def _sync_fill_menu(self, choice):
        action = self._fills.inv.get(str(choice))
        action.setChecked(True)

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
            self.pynguin.fill()
            self._sync_fill_menu('fill')
            self.pynguin.fillcolor(r, g, b)
            cmd = 'fill(color=(%s, %s, %s))\n' % (r, g, b)
            self.interpretereditor.addcmd(cmd)

    def setup_avatar_choices(self):
        choices = ((self.ui.actionPynguin, 'pynguin'),
                    (self.ui.actionArrow, 'arrow'),
                    (self.ui.actionRobot, 'robot'),
                    (self.ui.actionTurtle, 'turtle'),
                    (self.ui.actionHidden, 'hidden'))
        self.avatars = bidict(choices)

        custommenu = self.ui.menuCustom
        custommenu.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        custommenu.connect(custommenu, QtCore.SIGNAL('customContextMenuRequested(const QPoint&)'), self.makedeleteaction())

    def _sync_avatar_menu(self, imageid, filepath=None):
        settings = QtCore.QSettings()
        if not filepath:
            # built-in avatar choices
            action = self.avatars.inv.get(str(imageid))
            if action is not None:
                action.setChecked(True)
            idpath = imageid
        else:
            fmt = QtGui.QImageReader.imageFormat(filepath)
            if fmt == 'svg':
                idpathstr = '@@_%s@@%s'
            else:
                idpathstr = '@@%s@@%s'
            idpath = idpathstr % (imageid, filepath)

            action = self.avatars.inv.get(idpath)
            if action is None:
                custommenu = self.ui.menuCustom
                action = custommenu.addAction(imageid)
                action.setCheckable(True)
                self.viewgroup.addAction(action)
                self.avatars[action:] = idpath
                self._save_custom_avatar(idpath)

            action.setChecked(True)

        settings.setValue('pynguin/avatar', idpath)

    def _save_custom_avatar(self, idpath, remove=False):
        settings = QtCore.QSettings()
        cavs = []
        n = settings.beginReadArray('pynguin/custom_avatars')
        for i in range(n):
            settings.setArrayIndex(i)
            cavs.append(settings.value('idpath').toString())
        settings.endArray()
        if not remove and idpath not in cavs:
            cavs.append(idpath)
        elif remove and idpath in cavs:
            cavs.remove(idpath)
        settings.beginWriteArray('pynguin/custom_avatars')
        for i, idp in enumerate(cavs):
            settings.setArrayIndex(i)
            settings.setValue('idpath', idp)
        settings.endArray()

        if remove:
            currid = settings.value('pynguin/avatar', 'pynguin').toString()
            if currid == idpath:
                # Removed the current avatar
                self.set_pynguin_avatar('pynguin')

    def makedeleteaction(self):
        def deleteaction(pt, self=self):
            popup = QtGui.QMenu(self)
            custommenu = self.ui.menuCustom
            action = custommenu.actionAt(pt)
            def dodelete(action=action, menu=custommenu):
                menu.removeAction(action)
                idpath = self.avatars[action]
                self._save_custom_avatar(idpath, remove=True)
            popup.addAction('Remove', dodelete)
            popup.exec_(custommenu.mapToGlobal(pt))
        return deleteaction

    def set_pynguin_avatar(self, imageid):
        '''select which image to show

        sets the image for the primary pynguin only. For other later
            added pynguins, use p.avatar()
        '''
        idpath = str(imageid)
        if idpath.startswith('@@_'):
            # custom svg
            imageid, filepath = idpath[3:].split('@@')
            imid = imageid
        elif idpath.startswith('@@'):
            # custom non-svg
            imageid, filepath = idpath[2:].split('@@')
            imid = None
        else:
            imid = imageid
            filepath = None
        self.pynguin.avatar(imid, filepath)
        self._sync_avatar_menu(imageid, filepath)

        if not imid:
            imid = None
            cmdstr = "avatar(%s, '%s')\n"
            cmd = cmdstr % (imid, filepath)
        elif filepath is None:
            cmdstr = "avatar('%s')\n"
            cmd = cmdstr % imid
        else:
            cmdstr = "avatar('%s', '%s')\n"
            cmd = cmdstr % (imid, filepath)
        return cmd

    def setImageEvent(self, ev):
        imageid = self.avatars[ev]
        cmd = self.set_pynguin_avatar(imageid)
        self.interpretereditor.addcmd(cmd)

    def setcustomavatar(self):
        import avatar
        ad = avatar.CustomAvatar(self)
        r = ad.exec_()
        if r:
            filepath = str(ad.ui.filepath.text())
            element = str(ad.ui.element.text())
            if not element:
                element = None
                cmdstr = "avatar(%s, '%s')\n"
            else:
                cmdstr = "avatar('%s', '%s')\n"
            self.pynguin.avatar(element, filepath)

    def setup_speed_choices(self):
        choices = ((self.ui.actionSlow, 5),
                    (self.ui.actionMedium, 10),
                    (self.ui.actionFast, 20),
                    (self.ui.actionInstant, 0))
        self.speeds = bidict(choices)

    def sync_speed_menu(self, speed):
        action = self.speeds.inv.get(speed)
        if action is not None:
            action.setChecked(True)

            settings = QtCore.QSettings()
            settings.setValue('pynguin/speed', speed)

    def set_speed(self, speed):
        '''speed setting. Sets the speed for _all_ pynguins!'''
        Pynguin._drawspeed_pending = 2 * speed
        Pynguin._turnspeed_pending = 4 * speed

        self.sync_speed_menu(speed)

    def speedMenuEvent(self, ev=None):
        if ev is None:
            ev = self.speedgroup.checkedAction()

        speed = self.speeds[ev]
        self.set_speed(speed)
        choices = { 5: 'slow',
                    10: 'medium',
                    20: 'fast',
                    0: 'instant'}
        choice = choices.get(speed)
        cmd = "speed('%s')\n" % choice
        self.interpretereditor.addcmd(cmd)


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
        QtGui.QDesktopServices().openUrl(QtCore.QUrl(conf.bug_url))


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

        self.bg = QtGui.QPixmap(width+1, height+1)
        self.bg.fill(color)
        self.bgp = QtGui.QPainter(self.bg)
        self.bgp.drawEllipse(QtCore.QRect(0, 0, width, height))

    def drawBackground2(self, painter, rect):
        '''can be used in conjunction with background pixmap and
            painter set up in __init__ to draw an image behind
            the scene items.

            Not currently used.
        '''
        QtGui.QGraphicsScene.drawBackground(self, painter, rect)
        rt = QtCore.QRectF(rect)
        rtl = rect.topLeft()
        x, y = rtl.x(), rtl.y()
        pt = QtCore.QPointF(x+300, y+300)
        rt.moveTopLeft(pt)
        painter.drawPixmap(rect, self.bg, rt)
