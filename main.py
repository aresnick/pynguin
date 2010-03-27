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


import sys

from PyQt4 import QtGui


# Need to use logging when debugging, since stdout and stderr
#  are redirected to the internal console.
#import logging
#LOG_FILENAME = 'logfile.log'
#logging.basicConfig(filename=LOG_FILENAME,level=logging.DEBUG)
#logging.debug('Logging started')


from mw import MainWindow
from splash import Splash


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
