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


from PyQt4 import QtGui, QtCore
from PyQt4.Qsci import QsciScintilla, QsciLexerPython

import logging
logger = logging.getLogger('PynguinLogger')


class PythonEditor(QsciScintilla):
    def __init__(self, parent=None):
        super(PythonEditor, self).__init__(parent)

        #self.editor = parent
        self.mw = parent

        self.title = None
        self.docid = None

        self._filepath = None # not None for external file

        self.setup()

    def setup(self):
        self.setup_font()
        self.setup_margin0()
        self.setup_margin1()
        self.setup_cursor()
        self.setup_lexer()
        self.setup_custom()

    def setup_custom(self):
        pass

    def setup_font(self):
        # Set the default font
        fontsize = 16
        font = QtGui.QFont()
        font.setFamily('Courier')
        font.setBold(True)
        font.setFixedPitch(True)
        font.setPointSize(fontsize)
        self._font = font
        self.setFont(font)
        self.setMarginsFont(font)

    def setup_margin0(self):
        # Margin 0 is used for line numbers
        settings = QtCore.QSettings()
        numbers = settings.value('editor/linenumbers', True, bool)
        if numbers:
            self.show_line_numbers()
        else:
            self.hide_line_numbers()
        self.setMarginsBackgroundColor(QtGui.QColor("#444444"))
        self.setMarginsForegroundColor(QtGui.QColor('#999999'))

    def setup_margin1(self):
        # Disable 2nd margin (line markers)
        self.setMarginWidth(1, 0)

        # Match parentheses
        self.setBraceMatching(QsciScintilla.SloppyBraceMatch)
        self.setUnmatchedBraceBackgroundColor(QtGui.QColor('#000000'))
        self.setUnmatchedBraceForegroundColor(QtGui.QColor('#FF4444'))
        self.setMatchedBraceBackgroundColor(QtGui.QColor('#000000'))
        self.setMatchedBraceForegroundColor(QtGui.QColor('#44FF44'))

    def setup_cursor(self):
        # Current line visible with special background color
        self.setCaretLineVisible(True)
        self.setCaretForegroundColor(QtGui.QColor('#8888FF'))
        self.setCaretLineBackgroundColor(QtGui.QColor("#222222"))

    def setup_lexer(self):
        # Set Python lexer
        lexer = QsciLexerPython(self)
        lexer.setDefaultFont(self._font)
        self.setLexer(lexer)
        lexer.setDefaultPaper(QtGui.QColor("#000000"))
        lexer.setPaper(QtGui.QColor("#000000"))
        lexer.setAutoIndentStyle(QsciScintilla.AiOpening)
        self.setstyle()

        self.setIndentationsUseTabs(False)
        self.setBackspaceUnindents(True)
        self.setIndentationWidth(4)

    def hide_line_numbers(self):
        self.setMarginWidth(0, 0)

    def show_line_numbers(self):
        fontmetrics = QtGui.QFontMetrics(self._font)
        self.setMarginWidth(0, fontmetrics.width("00") + 6)
        self.setMarginLineNumbers(0, True)

    def wrap(self):
        self.setWrapMode(QsciScintilla.SC_WRAP_WORD)
    def nowrap(self):
        self.setWrapMode(QsciScintilla.SC_WRAP_NONE)

    def setstyle(self):
        styles = dict(Default = 0, Comment = 1, Number = 2,
                    DoubleQuotedString = 3, SingleQuotedString = 4,
                    Keyword = 5,TripleSingleQuotedString = 6,
                    TripleDoubleQuotedString = 7, ClassName = 8,
                    FunctionMethodName = 9, Operator = 10,
                    Identifier = 11, CommentBlock = 12,
                    UnclosedString = 13, HighlightedIdentifier = 14,
                    Decorator = 15)

        style = dict(Default = '#FFFFFF',
                        Comment = '#9999FF',
                        Identifier = '#CCFF99',
                        SingleQuotedString = '#FF6666',
                        DoubleQuotedString = '#FF6666',
                        TripleSingleQuotedString = '#FF6666',
                        TripleDoubleQuotedString = '#FF6666',
                        FunctionMethodName = '#77DDFF',
                        ClassName = '#CC44FF',
                        Number = '#44FFBB',

                        )

        lexer = self.lexer()
        for k in styles.keys():
            colorname = style.get(k, '#FFFFFF')
            color = QtGui.QColor(colorname)
            n = styles[k]
            lexer.setColor(color, n)
            lexer.setFont(self._font)

    def keyPressEvent(self, ev):
        k = ev.key()
        mdf = ev.modifiers()

        Return = QtCore.Qt.Key_Return
        Control = QtCore.Qt.ControlModifier
        Shift = QtCore.Qt.ShiftModifier
        Slash = QtCore.Qt.Key_Slash
        Question = QtCore.Qt.Key_Question
        Minus = QtCore.Qt.Key_Minus
        V = QtCore.Qt.Key_V
        Z = QtCore.Qt.Key_Z

        passthru = True

        lead = 0
        if k == Return:
            lineno, linedex = self.getCursorPosition()
            line = self.text(lineno).strip()
            indent = self.indentation(lineno)
            char = line[-1:]
            colon = ':'
            if char == colon:
                # auto indent
                indent += 4
            QsciScintilla.keyPressEvent(self, ev)
            self.insert(' '*indent)
            self.setCursorPosition(lineno+1, indent)
            passthru = False

        elif mdf & Control and k==Slash:
            self.commentlines()
            passthru = False

        elif mdf & Control and k==Question:
            self.commentlines(un=True)
            passthru = False

        elif mdf & Control and k==Minus:
            self.editor.zoomout()
            passthru = False

        elif mdf & Control and k==V:
            self.paste()
            passthru = False

        elif mdf & Control and mdf & Shift and k==Z:
            self.redo()
            passthru = False

        if passthru:
            QsciScintilla.keyPressEvent(self, ev)

        self.editor.settitle()
        self.update_window_modified()

    def update_window_modified(self):
        self.mw.show_modified_status()

    def commentlines(self, un=False):
        if self.hasSelectedText():
            linenostart, _, linenoend, _ = self.getSelection()
        else:
            linenostart, _ = self.getCursorPosition()
            linenoend = linenostart + 1

        for lineno in range(linenostart, linenoend):
            line = self.text(lineno)
            if line and not line.isspace():
                indent = self.indentation(lineno)
                if not un:
                    self.insertAt('#', lineno, indent)
                elif line[indent] == '#':
                    self.setSelection(lineno, indent, lineno, indent+1)
                    self.replaceSelectedText('')

    def paste(self):
        clipboard = QtGui.QApplication.clipboard()
        txt = clipboard.text()
        md = clipboard.mimeData()
        logger.info(md)

        newtxt = []
        for line in txt.split('\n'):
            line = str(line)
            if line.startswith('>>> ') or line.startswith('... '):
                line = line[4:]
            newtxt.append(line)
        txt = '\n'.join(newtxt)

        self.insert(txt)

    def contextMenuEvent(self, ev):
        '''Switch Redo to Ctrl-Shift-Z

        Connection of actual typed shortcut is in keyPressEvent()
        '''

        menu = self.createStandardContextMenu()
        actions = menu.actions()
        redo = actions[1]
        sep0 = actions[2]

        menu.removeAction(redo)
        redoaction = QtGui.QAction('Redo', menu)
        redoshortcut = QtGui.QKeySequence(QtCore.Qt.CTRL +
                                            QtCore.Qt.SHIFT +
                                            QtCore.Qt.Key_Z)
        redoaction.setShortcut(redoshortcut)
        redoaction.triggered.connect(self.redo)
        if not self.isRedoAvailable():
            redoaction.setDisabled(True)
        menu.insertAction(sep0, redoaction)

        menu.exec_(ev.globalPos())
