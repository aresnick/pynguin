# Copyright 2010-2013 Lee Harr
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

from PyQt4 import QtGui, QtCore


# Need to use logging when debugging, since stdout and stderr
#  are redirected to the internal console.

def setup_logging(level='debug'):
    import logging
    import logging.handlers
    from .conf import LOG_FILENAME

    levels = {'debug': logging.DEBUG,
                'info': logging.INFO,
                'critical': logging.CRITICAL,
            }
    if level not in levels:
        loglevel_error = level
        level = 'debug'
    elif not level:
        loglevel_error = '<empty>'
        level = 'debug'
    else:
        loglevel_error = False
    loglevel = levels[level]

    logger = logging.getLogger('PynguinLogger')
    logger.setLevel(loglevel)
    handler = logging.handlers.RotatingFileHandler(
              LOG_FILENAME, maxBytes=1000000, backupCount=3)
    logger.addHandler(handler)

    if loglevel_error:
        logger.debug('Log level error: level %s not available.' % loglevel_error)
    logger.critical('Logging started at level "%s".' % level)


from .mw import MainWindow
from .splash import Splash


def run(pynfile=None):
    translator = QtCore.QTranslator()
    localename = QtCore.QLocale.system().name()
    translation = 'data/translations/pynguin_' + localename
    translator.load(translation)

    app = QtGui.QApplication(sys.argv)
    app.installTranslator(translator)

    splash = Splash(app)
    splash.show()
    app.processEvents()

    win = MainWindow(app)
    splash.win = win
    win.show()
    splash.raise_()

    if pynfile is not None:
        loader = Loader(win, pynfile)
        QtCore.QTimer.singleShot(250, loader.loadlater)

    app.exec_()

class Loader:
    def __init__(self, win, pynfile):
        self.win = win
        self.pynfile = pynfile

    def loadlater(self):
        abspath = os.path.abspath(self.pynfile)
        self.win.open(self.pynfile)


def dumpfile():
    fp = sys.argv[-1]
    app = QtGui.QApplication(sys.argv)
    win = MainWindow(app)
    sys.stdout = win.interpretereditor.save_stdout
    sys.stderr = win.interpretereditor.save_stderr
    win._openfile(fp, add_to_recent=False, dump=True)


if __name__ == "__main__":
    if len(sys.argv) > 1:
        if sys.argv[1] == '-D':
            if len(sys.argv) > 2:
                level = sys.argv[2]
                setup_logging(level)
            else:
                setup_logging()

    run()
