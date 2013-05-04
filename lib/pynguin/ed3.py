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

import logging
logger = logging.getLogger('PynguinLogger')


class Editor:
    def __init__(self, parent):
        self.mw = parent
        self.box = QtGui.QStackedLayout()
        self.mselect = parent.ui.mselect
        self.documents = {} # SimplePythonEditor instances
        self.pages = {} # QStackedLayout pages
        self._doc = None
        self.docid = None
        self.title = None
        self._fontsize = 0
        docid = self.new()
        self.switchto(docid)

    def new(self):
        '''start a new blank document.'''

        doc = SimplePythonEditor(self)
        doc.zoomTo(self._fontsize)
        docid = uuid.uuid4().hex
        logger.info(docid)
        self.documents[docid] = doc
        page = self.box.addWidget(doc)
        self.pages[docid] = page
        doc.docid = docid
        self.mselect.addItem('', docid)
        self.settitle(doc)

        return docid

    def clear_all(self):
        while self.box.count():
            item = self.box.itemAt(0)
            self.box.removeItem(item)
        self.mselect.clear()

    def add(self, txt):
        docid = self.new()
        doc = self.documents[docid]
        doc.setText(txt)
        doc.setModified(False)
        self.settitle(doc)
        self.switchto(docid)

    def addexternal(self, fp):
        '''Add an external python source file.'''
        for docid, doc in list(self.documents.items()):
            if doc._filepath == fp:
                # this external file already added
                self.switchto(docid)
                return
        txt = open(fp).read()
        #txt = str(txt).decode('utf-8')
        self.add(txt)
        self._doc._filepath = fp
        _, title = os.path.split(fp)
        self.settitle()
        return self._doc

    def settitle(self, doc=None):
        '''set the title for the current document.
            Also updates the combobox document selector.

            If this is an external file, use the file path
                for the title.

            Regular files use the first line to determine the title.
            If first line looks like a function definition, use
            the name/ signature of the function as the title,
            otherwise use the whole line.
        '''

        if doc is None:
            doc = self._doc

        txt = doc.text(0).strip()

        if doc._filepath is not None:
            _, title = os.path.split(doc._filepath)
        elif txt.startswith('def ') and txt.endswith(':'):
            title = txt[4:-1]
        elif txt=='':
            title = 'Untitled'
        else:
            title = txt

        if title == doc.title:
            return

        idx = 0
        for idx in range(self.mselect.count()):
            item_docid = self.mselect.itemData(idx)
            if item_docid == doc.docid:
                self.mselect.setItemText(idx, title)
                break

        doc.title = title

    def switchto(self, docid):
        '''switch to document docid'''

        old_doc = self._doc
        doc = self.documents[docid]
        if doc == old_doc:
            return

        page = self.pages[docid]
        self.box.setCurrentIndex(page)
        self.mselect.setCurrentIndex(page)

        self.docid = docid
        self._doc = doc
        self.settitle()

    def shownext(self):
        '''show the next document in the stack.'''

        mselect = self.mselect
        count = mselect.count()
        idx = mselect.currentIndex()
        if idx < count-1:
            mselect.setCurrentIndex(idx+1)
            docid = str(mselect.itemData(idx+1))
            if docid in self.documents:
                self.switchto(docid)
                doc = self.documents[docid]
                doc.setFocus()

    def showprev(self):
        '''show the previous document in the stack.'''

        mselect = self.mselect
        count = mselect.count()
        idx = mselect.currentIndex()
        if idx > 0:
            mselect.setCurrentIndex(idx-1)
            docid = str(mselect.itemData(idx-1))
            if docid in self.documents:
                self.switchto(docid)
                doc = self.documents[docid]
                doc.setFocus()

    def promote(self):
        '''move the current document up 1 place in the stack'''

        mselect = self.mselect
        idx = mselect.currentIndex()
        title = mselect.itemText(idx)
        docid = mselect.itemData(idx)
        if idx > 0:
            self.box.takeAt(idx)
            page = self.pages[docid]
            doc = self._doc
            otherdocid = str(mselect.itemData(idx-1))
            otherdoc = self.documents[otherdocid]
            otherpage = self.pages[otherdocid]
            self.pages[docid] = otherpage
            self.pages[otherdocid] = page
            self.box.insertWidget(idx-1, self._doc)

            mselect.removeItem(idx)
            mselect.insertItem(idx-1, title, docid)
            self.mw._modified = True
            self.mw.setWindowModified(True)

            self._doc = None # Force switch
            self.switchto(docid)

    def demote(self):
        '''move the current document down 1 place in the stack'''

        mselect = self.mselect
        idx = mselect.currentIndex()
        title = mselect.itemText(idx)
        docid = mselect.itemData(idx)
        count = self.mselect.count()
        if idx < count-1:
            self.box.takeAt(idx)
            page = self.pages[docid]
            doc = self._doc
            otherdocid = str(mselect.itemData(idx+1))
            otherdoc = self.documents[otherdocid]
            otherpage = self.pages[otherdocid]
            self.pages[docid] = otherpage
            self.pages[otherdocid] = page
            self.box.insertWidget(idx+1, self._doc)

            mselect.removeItem(idx)
            mselect.insertItem(idx+1, title, docid)
            self.mw._modified = True
            self.mw.setWindowModified(True)

            self._doc = None # Force switch
            self.switchto(docid)

    def setfontsize(self, size):
        self._fontsize = size
        for doc in self.documents.values():
            doc.zoomTo(size)
        settings = QtCore.QSettings()
        settings.setValue('editor/fontsize', size)

    def zoomin(self):
        self.setfontsize(self._fontsize + 1)

    def zoomout(self):
        self.setfontsize(self._fontsize - 1)

    def setFocus(self):
        self._doc.setFocus()

    def wrap(self, on=True):
        for doc in self.documents.values():
            if on:
                doc.setWrapMode(QsciScintilla.SC_WRAP_WORD)
            else:
                doc.setWrapMode(QsciScintilla.SC_WRAP_NONE)

    def line_numbers(self, on=True):
        for doc in self.documents.values():
            if on:
                doc.show_line_numbers()
            else:
                doc.hide_line_numbers()

    def selectline(self, n):
        '''highlight line number n'''

        lineno = n - 1
        doc = self._doc
        line = doc.text(lineno)
        self._doc.setSelection(lineno, 0, lineno, len(line))


class SimplePythonEditor(QsciScintilla):
    def __init__(self, parent=None):
        super(SimplePythonEditor, self).__init__(parent.mw)

        self.editor = parent
        self.mw = parent.mw

        self.title = None
        self.docid = None

        self._filepath = None # not None for external file

        self.setup()

    def setup(self):
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

        # Margin 0 is used for line numbers
        settings = QtCore.QSettings()
        numbers = settings.value('editor/linenumbers', True, bool)
        if numbers:
            self.show_line_numbers()
        else:
            self.hide_line_numbers()
        self.setMarginsBackgroundColor(QtGui.QColor("#444444"))
        self.setMarginsForegroundColor(QtGui.QColor('#999999'))

        # Disable 2nd margin (line markers)
        self.setMarginWidth(1, 0)

        # Match parentheses
        self.setBraceMatching(QsciScintilla.SloppyBraceMatch)
        self.setUnmatchedBraceBackgroundColor(QtGui.QColor('#000000'))
        self.setUnmatchedBraceForegroundColor(QtGui.QColor('#FF4444'))
        self.setMatchedBraceBackgroundColor(QtGui.QColor('#000000'))
        self.setMatchedBraceForegroundColor(QtGui.QColor('#44FF44'))

        # Current line visible with special background color
        self.setCaretLineVisible(True)
        self.setCaretForegroundColor(QtGui.QColor('#8888FF'))
        self.setCaretLineBackgroundColor(QtGui.QColor("#222222"))

        # Set Python lexer
        lexer = QsciLexerPython(self)
        lexer.setDefaultFont(font)
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

        if self.mw._modified or self.isModified():
            self.mw.setWindowModified(True)
        elif not self.mw._modified and not self.mw.check_modified():
            self.mw.setWindowModified(False)

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

        if self.hasSelectedText():
            self.replaceSelectedText(txt)
        else:
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
