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


        reset_forces_visible = settings.value('pynguin/reset_forces_visible', True, bool)
        self.ui.reset_forces_visible.setChecked(reset_forces_visible)
        allow_start_hidden = settings.value('pynguin/allow_start_hidden', False, bool)
        self.ui.allow_start_hidden.setChecked(allow_start_hidden)
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
