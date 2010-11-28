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


import sys

from PyQt4 import QtGui


# Need to use logging when debugging, since stdout and stderr
#  are redirected to the internal console.

def setup_logging(level='debug'):
    import logging
    import logging.handlers
    from conf import LOG_FILENAME

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
    if len(sys.argv) > 1:
        if sys.argv[1] == '-D':
            if len(sys.argv) > 2:
                level = sys.argv[2]
                setup_logging(level)
            else:
                setup_logging()

    run()
