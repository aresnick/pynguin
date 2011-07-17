import os

from PyQt4 import QtCore, QtGui, uic

import util
import conf

uidir = 'data/ui'

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

        savesingle = settings.value('file/savesingle', True).toBool()
        if savesingle:
            self.ui.savesingle.setChecked(True)
        else:
            self.ui.savefolder.setChecked(True)

        reloadexternal = settings.value('file/reloadexternal', True).toBool()
        self.ui.reloadexternal.setChecked(reloadexternal)

        autorun = settings.value('file/autorun', False).toBool()
        self.ui.autorun.setChecked(autorun)

    def backupbrowse(self):
        filepath = QtGui.QFileDialog.getExistingDirectory(
                            self,
                            'Choose folder to store backups')
        if filepath:
            self.ui.backupfilepath.setText(filepath)

    def externaloption(self):
        rel = self.ui.reloadexternal.isChecked()
        self.ui.autorun.setEnabled(rel)

    #def accept(self):
        #'Verify'
        #if False:
            #QtGui.QDialog.accept(self)
