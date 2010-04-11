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


#import logging

from PyQt4 import QtCore, QtGui

from editor import HighlightedTextEdit


class CodeArea(HighlightedTextEdit):
    def __init__(self, mw):
        HighlightedTextEdit.__init__(self)
        self.mw = mw
        self.mselect = mw.ui.mselect
        self.documents = {}
        self.title = None
        self.docid = None
        self.new()

    def clear(self):
        self._doc.clear()
        self.documents = {}
        self.mselect.clear()

    def keyPressEvent(self, ev):
        k = ev.key()
        mdf = ev.modifiers()

        Up = QtCore.Qt.Key_Up
        Down = QtCore.Qt.Key_Down
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

        elif mdf & QtCore.Qt.ControlModifier and k==Up:
            self.promote()
            return

        elif mdf & QtCore.Qt.ControlModifier and k==Down:
            self.demote()
            return

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

    def savecurrent(self):
        '''get the text of the current document and save it in the
            documents dictionary, keyed by title
        '''
        if self.docid is not None:
            self.documents[self.docid] = str(self._doc.toPlainText())

    def new(self):
        '''save the current document and start a new blank document'''
        self.savecurrent()
        self._doc.setPlainText('')

        import uuid
        docid = uuid.uuid4().hex
        self.mselect.addItem('', docid)
        self.documents[docid] = ''
        idx = self.mselect.count() - 1
        self.mselect.setCurrentIndex(idx)
        self.docid = docid

        self.settitle('')

    def switchto(self, docid):
        '''save the current document and switch to the document titled docname'''
        self.savecurrent()
        doctxt = self.documents[docid]
        self.docid = docid
        self._doc.setPlainText(doctxt)
        firstline = str(doctxt.split('\n')[0])
        self.settitle(firstline)

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
