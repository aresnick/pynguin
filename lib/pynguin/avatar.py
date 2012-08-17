import os

from PyQt4 import QtCore, QtGui, uic
from PyQt4.Qt import QFrame, QWidget, QHBoxLayout, QPainter

from . import util
from . import conf

datadir = util.get_datadir()
uidir = os.path.join(datadir, 'ui')

class CustomAvatar(QtGui.QDialog):
    def __init__(self, parent):
        self.parent = parent
        QtGui.QDialog.__init__(self)
        uifile = 'avatar.ui'
        uipath = os.path.join(uidir, uifile)
        CAClass, _ = uic.loadUiType(uipath)
        self.ui = CAClass()
        self.ui.setupUi(self)
        self.fmt = None

    def browse(self):
        filepath = QtGui.QFileDialog.getOpenFileName(
                            self,
                            'Choose image for avatar')
        if filepath:
            self.ui.filepath.setText(filepath)
            fmt = QtGui.QImageReader.imageFormat(filepath)
            if fmt == 'svg':
                self.ui.element.setEnabled(True)
            self.fmt = fmt

    def accept(self):
        if self.fmt == 'svg' and not self.ui.element.text():
            # Must choose an svg element
            QtGui.QMessageBox.information(
                    self,
                    'Choose SVG Element',
                    'You must choose an SVG element.')
        else:
            QtGui.QDialog.accept(self)
