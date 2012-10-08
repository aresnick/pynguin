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


import os
import logging
logger = logging.getLogger('PynguinLogger')
import time

from PyQt4 import QtCore, QtGui

from .editor import HighlightedTextEdit

try:
    from .highlighter import Highlighter, QFormatter, Formatter
    from .highlighter import get_lexer_by_name, hex2QColor
    from pygments.style import Style
    from pygments.token import Keyword, Name, Comment, String, Error
    from pygments.token import  Number, Operator, Generic, Literal

    class CodeFormatter(QFormatter):
        custom_colors = {
            Operator: 'FFFFFF',
            Literal.Number.Integer: 'AAAA22',
            Literal.Number.Float: 'AAAA55',
            Keyword: '80F080',
            Name.Builtin.Pseudo: 'F0F060',
            Name.Function: '8080FF',}

        def __init__(self, fontsize):
            Formatter.__init__(self, style='default')
            self.data=[]

            self.customize()

            # Create a dictionary of text styles, indexed
            # by pygments token names, containing QTextCharFormat
            # instances according to pygments' description
            # of each style

            self.styles={}
            for token, style in self.style:
                font = QtGui.QFont('Courier')
                font.setFixedPitch(True)
                font.setWeight(QtGui.QFont.DemiBold)
                qtf=QtGui.QTextCharFormat()
                qtf.setFontPointSize(fontsize)
                qtf.setFont(font)
                qtf.setFontPointSize(fontsize)

                if style['color']:
                    qtf.setForeground(hex2QColor(style['color']))
                if style['bgcolor']:
                    qtf.setBackground(hex2QColor(style['bgcolor']))
                if style['bold']:
                    qtf.setFontWeight(QtGui.QFont.Bold)
                if style['italic']:
                    qtf.setFontItalic(True)
                if style['underline']:
                    qtf.setFontUnderline(True)
                self.styles[str(token)]=qtf

        def setfontsize(self, pt):
            for nm, qtf in list(self.styles.items()):
                qtf.setFontPointSize(pt)

        def show_all_styles(self):
            z = sorted(list(self.style._styles.keys()))
            for a in z:
                print(a, self.style._styles[a])

        def custom_color(self, style, color):
            self.style._styles[style][0] = color

        def customize(self):
            for style, color in list(self.custom_colors.items()):
                self.custom_color(style, color)

    class CodeHighlighter(Highlighter):
        def __init__(self, parent, mode, fontsize):
            Highlighter.__init__(self, parent, mode)
            self.tstamp=time.time()

            # Keep the formatter and lexer, initializing them
            # may be costly.
            self.fontsize = fontsize
            self.formatter=CodeFormatter(fontsize)
            self.lexer=get_lexer_by_name(mode)

        def setfontsize(self, pt):
            if pt != self.fontsize:
                self.fontsize = pt
                self.formatter.setfontsize(pt)


except ImportError:
    # probably caused by missing pygments library
    from .editor import PythonHighlighter
    class CodeHighlighter(PythonHighlighter):
        def __init__(self, document, mode, fontsize):
            char_format = QtGui.QTextCharFormat()
            PythonHighlighter.__init__(self, document, char_format)
            self.fontsize = -1
            self.setfontsize(fontsize)

        def setfontsize(self, pt):
            if pt != self.fontsize:
                self.fontsize = pt
                char_format = QtGui.QTextCharFormat()
                font = QtGui.QFont('Courier')
                font.setFixedPitch(True)
                font.setWeight(QtGui.QFont.DemiBold)
                char_format.setFont(font)
                char_format.setFontPointSize(pt)
                self.base_format = char_format
                self.updateHighlighter(char_format.font())

class CodeArea(HighlightedTextEdit):
    def __init__(self, mw):
        HighlightedTextEdit.__init__(self)
        self.mw = mw
        self.mselect = mw.ui.mselect
        self.textdocuments = {}
        self.documents = {}
        self.highlighters = {}
        self.title = None
        self.docid = None
        self.fontsize = 16
        self.new()

    def setdoc(self, doc):
        self.setDocument(doc)
        self._doc = doc
        highlighter = self.highlighters[doc]
        self.highlighter = highlighter
        if highlighter.fontsize != self.fontsize:
            self.setfontsize(self.fontsize)
            self.rehi()

    def setfontsize(self, pt):
        if pt != self.highlighter.fontsize:
            self.fontsize = pt
            self.highlighter.setfontsize(self.fontsize)
            self.rehi()
            settings = QtCore.QSettings()
            settings.setValue('editor/fontsize', pt)

    def zoomin(self):
        self.setfontsize(self.fontsize + 1)

    def zoomout(self):
        self.setfontsize(self.fontsize - 1)

    def rehi(self):
        doc = self.document()
        b = doc.begin()
        last = doc.lastBlock()

        c = self.textCursor()
        p0 = c.position()

        while b != last:
            self._rehibump(b, c)
            b = b.next()
        self._rehibump(last, c)

        c.setPosition(p0)
        self.setTextCursor(c)

    def _rehibump(self, b, c):
        p = b.position()
        c.setPosition(p)
        self.setTextCursor(c)
        c.insertText(' ')
        self.undo()

    def clear(self):
        self._doc.clear()
        self.textdocuments = {}
        self.documents = {}
        self.mselect.clear()

    def keyPressEvent(self, ev):
        k = ev.key()
        mdf = ev.modifiers()

        Return = QtCore.Qt.Key_Return
        Control = QtCore.Qt.ControlModifier
        Shift = QtCore.Qt.ShiftModifier
        Slash = QtCore.Qt.Key_Slash
        Question = QtCore.Qt.Key_Question

        passthru = True

        lead = 0
        if k == Return:
            curs = self.textCursor()
            cpos = curs.position()
            cblk = self._doc.findBlock(cpos)
            atstart = curs.atBlockStart()
            if atstart:
                lead = 0
            else:
                cblktxt = str(cblk.text())
                ts = cblktxt.split()
                if ts:
                    lead = cblktxt.find(ts[0])

                char = self._doc.characterAt(cpos-1)
                colon = ':'
                if char == colon:
                    # auto indent
                    lead += 4

        elif mdf & Control and k==Slash:
            self.commentlines()

        elif mdf & Control and k==Question:
            self.commentlines(un=True)
            passthru = False

        if passthru:
            HighlightedTextEdit.keyPressEvent(self, ev)
        if lead:
            self.insertPlainText(' '*lead)

        if hasattr(self._doc, '_title'):
            title = self._doc._title
        else:
            fblk = self._doc.firstBlock()
            title = str(fblk.text())
        self.settitle(title)
        if self.mw._modified or self._doc.isModified():
            self.mw.setWindowModified(True)
        elif not self.mw._modified and not self.mw.check_modified():
            self.mw.setWindowModified(False)

    def settitle(self, txt):
        '''set the title for the current document to txt
            Also updates the combobox document selector.

            If txt looks like a function definition, uses
            the name/ signature of the function as the
            title instead of the whole line.
        '''
        if txt.startswith('def ') and txt.endswith(':'):
            title = txt[4:-1]
        elif txt=='':
            title = 'Untitled'
        else:
            title = txt

        if title == self.title:
            return

        idx = 0
        for idx in range(self.mselect.count()):
            item_docid = self.mselect.itemData(idx)
            if item_docid == self.docid:
                self.mselect.setItemText(idx, title)
                break

        self.mselect.setCurrentIndex(idx)

    def commentlines(self, un=False):
        '''comment (add # to beginning) of all selected lines

        if un=True uncomment the lines instead of commenting them
        '''
        curs = self.textCursor()
        if curs.hasSelection():
            start = curs.selectionStart()
            end = curs.selectionEnd()
            poss = list(range(start, end))
        else:
            start = curs.position()
            poss = [start]
            end = None

        blks = []
        for pos in poss:
            blk = self._doc.findBlock(pos)
            if blk not in blks:
                blks.append(blk)

        added = 0
        for blk in blks:
            blk0 = blk.position()
            txt = blk.text()
            firstnonspace = 0
            firstchar = ''
            for c in txt[self.col0:]:
                if c != ' ':
                    firstchar = c
                    break
                firstnonspace += 1
            pos = blk0 + self.col0 + firstnonspace
            curs.setPosition(pos, 0)
            self.setTextCursor(curs)
            if not un:
                self.insertPlainText('#')
                added += 1
            else:
                if firstchar == '#':
                    curs.deleteChar()
                    added -= 1

        if end is not None:
            curs.setPosition(start, 0)
            curs.setPosition(end+added, 1)
            self.setTextCursor(curs)

    def savecurrent(self):
        '''get the text of the current document and save it in the
            documents dictionary, keyed by title
        '''
        if self.docid is not None:
            self.textdocuments[self.docid] = self.document()
            self.documents[self.docid] = str(self._doc.toPlainText())

    def new(self):
        '''save the current document and start a new blank document'''
        self.savecurrent()

        doc = QtGui.QTextDocument(self)
        self.highlighters[doc] = CodeHighlighter(doc, 'python', self.fontsize)
        self.setdoc(doc)

        import uuid
        docid = uuid.uuid4().hex
        self.mselect.addItem('', docid)
        self.documents[docid] = ''
        self.textdocuments[docid] = doc
        idx = self.mselect.count() - 1
        self.mselect.setCurrentIndex(idx)
        self.docid = docid

        self.settitle('')

    def switchto(self, docid):
        '''save the current document and switch to the document titled docname'''
        self.savecurrent()
        doctxt = self.documents[docid]
        self.docid = docid
        doc = self.textdocuments[docid]
        self.setdoc(doc)
        if hasattr(self._doc, '_title'):
            title = self._doc._title
        else:
            title = str(doctxt.split('\n')[0])
        self.settitle(title)

    def add(self, txt):
        '''add a new document with txt as the contents'''
        self.new()
        self._doc.setPlainText(txt)
        title = txt.split('\n')[0]
        self.settitle(title)
        self.savecurrent()
        self._doc.setModified(False)

    def addexternal(self, fp):
        '''Add an external python source file.'''
        for docid, doc in list(self.textdocuments.items()):
            if hasattr(doc, '_filepath') and doc._filepath == fp:
                # this external file already added
                self.switchto(docid)
                return
        txt = open(fp).read()
        #txt = str(txt).decode('utf-8')
        self.new()
        self._doc.setPlainText(txt)
        self._doc._filepath = fp
        _, title = os.path.split(fp)
        self._doc._title = title
        self.settitle(title)
        self.savecurrent()
        self._doc.setModified(False)
        return self._doc

    def selectline(self, n, align=True):
        '''highlight line number n'''
        if align:
            self.selectline(n+10, False)

        docline = 1
        blk = self._doc.begin()
        end = self._doc.end()
        while docline < n:
            blk = blk.next()
            if blk == end:
                blk = self._doc.lastBlock()
                break
            docline += 1

        linestart = blk.position()
        linelen = blk.length()
        lineend = linestart + linelen

        curs = QtGui.QTextCursor(self._doc)
        curs.setPosition(lineend-1, 0)
        curs.setPosition(linestart, 1)
        self.setTextCursor(curs)

    def promote(self):
        '''move the current document up 1 place in the stack'''
        self.savecurrent()
        idx = self.mselect.currentIndex()
        title = self.mselect.itemText(idx)
        item_docid = self.mselect.itemData(idx)
        if idx > 0:
            self.mselect.removeItem(idx)
            self.mselect.insertItem(idx-1, title, item_docid)
            self.mselect.setCurrentIndex(idx-1)
            self.mw._modified = True
            self.mw.setWindowModified(True)

    def shownext(self):
        '''show the next document in the stack.'''
        mselect = self.mselect
        count = mselect.count()
        idx = mselect.currentIndex()
        if idx < count-1:
            mselect.setCurrentIndex(idx+1)
            docid = str(mselect.itemData(idx+1).toString())
            if docid in self.documents:
                self.switchto(docid)
                self.setFocus()

    def demote(self):
        '''move the current document down 1 place in the stack'''
        self.savecurrent()
        idx = self.mselect.currentIndex()
        title = self.mselect.itemText(idx)
        item_docid = self.mselect.itemData(idx)
        count = self.mselect.count()
        if idx < count-1:
            self.mselect.removeItem(idx)
            self.mselect.insertItem(idx+1, title, item_docid)
            self.mselect.setCurrentIndex(idx+1)
            self.mw._modified = True
            self.mw.setWindowModified(True)

    def showprev(self):
        '''show the previous document in the stack.'''
        mselect = self.mselect
        count = mselect.count()
        idx = mselect.currentIndex()
        if idx > 0:
            mselect.setCurrentIndex(idx-1)
            docid = str(mselect.itemData(idx-1).toString())
            if docid in self.documents:
                self.switchto(docid)
                self.setFocus()

    def insertFromMimeData(self, data):
        txt = data.data('text/plain')
        b = bytes(txt)
        txt = b.decode('utf-8')

        newtxt = []
        for line in txt.split('\n'):
            line = str(line)
            if line.startswith('>>> ') or line.startswith('... '):
                line = line[4:]
            newtxt.append(line)
        txt = '\n'.join(newtxt)

        newdata = QtCore.QMimeData()
        newdata.setText(txt)
        HighlightedTextEdit.insertFromMimeData(self, newdata)

