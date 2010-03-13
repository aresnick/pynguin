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


from editor import HighlightedTextEdit


class CodeArea(HighlightedTextEdit):
    def __init__(self, mw):
        HighlightedTextEdit.__init__(self)
        self.mw = mw
        self.mselect = mw.ui.mselect
        self.documents = {}
        self.title = ''
        self.settitle('Untitled')

    def clear(self):
        self._doc.clear()
        self.documents = {}
        self.mselect.clear()

    def keyPressEvent(self, ev):
        k = ev.key()

        Return = QtCore.Qt.Key_Return
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
                colon = QtCore.QChar(':')
                if char == colon:
                    # auto indent
                    lead += 4

        HighlightedTextEdit.keyPressEvent(self, ev)
        if lead:
            self.insertPlainText(' '*lead)

        fblk = self._doc.firstBlock()
        txt = str(fblk.text())
        self.settitle(txt)
        if self._doc.isModified():
            self.mw._modified = True
            self.mw.setWindowModified(True)

    def settitle(self, txt):
        '''set the title for the current document to txt
            Also updates the combobox document selector.

            If txt looks like a function definition, uses
            the name/ signature of the function as the
            title instead of the whole line.
        '''
        if txt.startswith('def ') and txt.endswith(':'):
            title = txt[4:-1]
        elif txt=='NEW' or txt=='':
            title = 'Untitled'
        else:
            title = txt

        if title in self.documents and self.title=='Untitled':
            # This is probably a copy/paste of another page
            copyn = 0
            for othertitle in self.documents.keys():
                if othertitle==title or \
                    (title[-5:-4]=='#' and othertitle.startswith(title[4:-6])) or \
                    (othertitle[:-5]==title[:-5]) or \
                    (title == othertitle[4:-6] and othertitle[-5:-4]=='#'):
                    copyn += 1

            if title[-5:-4]=='#':
                title = title[:-5]

            title = txt
            titleadd = '#%04d' % copyn
            fblk = self._doc.firstBlock()
            fblklen = fblk.length()

            fblktxt = str(fblk.text())
            if fblktxt[-5:-4] == '#':
                curs = QtGui.QTextCursor(self._doc)
                curs.setPosition(fblklen-6, 0)
                curs.setPosition(fblklen-1, 1)
                self.setTextCursor(curs)
                curs.removeSelectedText()
                fblklen = fblk.length()
                title = str(fblk.text()).rstrip()

            curs = QtGui.QTextCursor(self._doc)
            curs.setPosition(fblklen-1, 0)
            self.setTextCursor(curs)
            self.insertPlainText(titleadd)
            title = title + titleadd

        if title != self.title:
            if txt != 'NEW':
                idx = self.mselect.findText(self.title)
                if idx > -1:
                    self.mselect.removeItem(idx)
                if self.title in self.documents:
                    self.documents[title] = self.documents[self.title]
                    del self.documents[self.title]
            self.title = title
            self.mselect.addItem(title)

        idx = self.mselect.findText(self.title)
        self.mselect.setCurrentIndex(idx)

    def savecurrent(self):
        '''get the text of the current document and save it in the
            documents dictionary, keyed by title
        '''
        title = self.title
        text = str(self._doc.toPlainText())
        if title != 'Untitled' or text:
            self.documents[title] = text

    def new(self):
        '''save the current document and start a new blank document'''
        self.savecurrent()
        self._doc.setPlainText('')
        self.settitle('NEW')

    def switchto(self, docname):
        '''save the current document and switch to the document titled docname'''
        self.savecurrent()
        self._doc.setPlainText(self.documents[docname])
        self.title = docname

    def add(self, txt):
        '''add a new document with txt as the contents'''
        self.new()
        self._doc.setPlainText(txt)
        title = txt.split('\n')[0]
        self.settitle(title)
        self.savecurrent()

    def selectline(self, n):
        '''highlight line number n'''
        docline = 1
        doccharstart = 0
        blk = self._doc.begin()
        while docline < n:
            txt = blk.text()
            lentxt = len(txt)+1
            doccharstart += lentxt
            blk = blk.next()
            docline += 1
        txt = blk.text()
        lentxt = len(txt)
        doccharend = doccharstart + lentxt

        curs = QtGui.QTextCursor(self._doc)
        curs.setPosition(doccharstart, 0)
        curs.setPosition(doccharend, 1)
        self.setTextCursor(curs)
