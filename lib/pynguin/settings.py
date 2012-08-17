import os

from PyQt4 import QtCore, QtGui, uic

from . import util
from . import conf

datadir = util.get_datadir()
uidir = os.path.join(datadir, 'ui')

class Settings(QtGui.QDialog):
    def __init__(self, parent):
        self.parent = parent
        QtGui.QDialog.__init__(self)
        uifile = 'settings.ui'
        uipath = os.path.join(uidir, uifile)
        SClass, _ = uic.loadUiType(uipath)
        self.ui = SClass()
        self.ui.setupUi(self)
        self.setcurrent()

    def setcurrent(self):
        settings = QtCore.QSettings()

        savesingle = settings.value('file/savesingle', True, bool)
        if savesingle:
            self.ui.savesingle.setChecked(True)
        else:
            self.ui.savefolder.setChecked(True)

        reloadexternal = settings.value('file/reloadexternal', True, bool)
        self.ui.reloadexternal.setChecked(reloadexternal)
        autorun = settings.value('file/autorun', False, bool)
        self.ui.autorun.setChecked(autorun)


        bfp = settings.value('file/backupfolderpath', '')
        self.ui.backupfolderpath.setText(bfp)
        bfn = settings.value('file/backupfilename', 'backup~%s.pyn')
        self.ui.backupfilename.setText(bfn)
        brate = settings.value('file/backuprate', 3, int)
        self.ui.backuprate.setValue(brate)
        bkeep = settings.value('file/backupkeep', 5, int)
        self.ui.backupkeep.setValue(bkeep)


        reset = settings.value('editor/testrun_reset', True, bool)
        self.ui.testrun_reset.setChecked(reset)
        mainfirst = settings.value('editor/mainfirst', True, bool)
        if mainfirst:
            self.ui.editor_mainfirst.setChecked(True)
        else:
            self.ui.editor_mainlast.setChecked(True)
        rev = settings.value('editor/testall_reverse', False, bool)
        self.ui.testall_reverse.setChecked(rev)
        autocall = settings.value('editor/testall_autocall', False, bool)
        self.ui.testall_autocall.setChecked(autocall)


        quietinterrupt = settings.value('console/quietinterrupt', False, bool)
        self.ui.quietinterrupt.setChecked(quietinterrupt)

    def backupbrowse(self):
        filepath = QtGui.QFileDialog.getExistingDirectory(
                            self,
                            'Choose folder to store backups')
        if filepath:
            self.ui.backupfolderpath.setText(filepath)

    def externaloption(self):
        rel = self.ui.reloadexternal.isChecked()
        self.ui.autorun.setEnabled(rel)

    def backupoption(self, val):
        backup = bool(val)
        self.ui.backupfolderpath.setEnabled(backup)
        self.ui.backupfilename.setEnabled(backup)
        self.ui.backuprate.setEnabled(backup)

    def defaultsettings(self):
        self.parent.clear_settings()
        self.setcurrent()

    #def accept(self):
        #'Verify'
        #if False:
            #QtGui.QDialog.accept(self)
