# Copyright 2013 Lee Harr
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
import uuid

from PyQt4 import QtGui, QtCore
from PyQt4.Qsci import QsciScintilla, QsciLexerPython

from qsciedit import editor, mde

import logging
logger = logging.getLogger('PynguinLogger')


class Documents(mde.MultiDocumentEditor):
    def setup_selector(self):
        self._selector = self.mw.ui.mselect


class Editor(editor.PythonEditor):
    pass
    # self.editor = Documents() # set by mde.MDE.__init__()
