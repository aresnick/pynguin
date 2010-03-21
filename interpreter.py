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

from PyQt4 import QtCore, QtGui

from editor import HighlightedTextEdit


class CmdThread(QtCore.QThread):
    def __init__(self, ed, txt):
        '''set up a separate thread to run the code given in txt in the
            InteractiveInterpreter ed.'''
        QtCore.QThread.__init__(self)
        QtCore.QThread.setTerminationEnabled()
        self.ed = ed
        self.txt = txt
    def run(self):
        ed = self.ed
        lines = self.txt.split('\n')
        if len(lines) > 1:
            ed.interpreter.runcode(self.txt)
        else:
            ed.needmore = ed.interpreter.push(self.txt)

class Interpreter(HighlightedTextEdit):
    def __init__(self, parent):
        HighlightedTextEdit.__init__(self)
        self.mw = parent
        self.history = []
        self._outputq = []
        self.historyp = -1

        self.save_stdout = sys.stdout
        self.save_stdin = sys.stdin
        self.save_stderr = sys.stderr

        sys.stdout = self
        sys.stderr = self

        self._check_control_key = False

        self.setWordWrapMode(QtGui.QTextOption.WrapAnywhere)

        self.cmdthread = None
        self.controlC = False

        QtCore.QTimer.singleShot(10, self.writeoutputq)

        self.write('>>> ')

    def clear(self):
        self.history = []
        self._outputq = []
        self._doc.clear()
        self.write('>>> ')

    def addcmd(self, cmd):
        self.write(cmd)
        if cmd[-1] == '\n':
            self.write('>>> ')
            self.history.append(cmd.rstrip())

    def write(self, text):
        '''cannot write directly to the console...
            instead, append this text to the output queue for later use.
        '''
        if text:
            self._outputq.append(text)

    def writeoutputq(self):
        '''process the text output queue. Must be done from the main thread.
        '''
        while self._outputq:
            text = self._outputq.pop(0)
            self.insertPlainText(text)
            QtCore.QTimer.singleShot(100, self.scrolldown)
        QtCore.QTimer.singleShot(10, self.writeoutputq)

    def keyPressEvent(self, ev):
        k = ev.key()
        mdf = ev.modifiers()

        Tab = QtCore.Qt.Key_Tab
        Backtab = QtCore.Qt.Key_Backtab
        Backspace = QtCore.Qt.Key_Backspace
        Left = QtCore.Qt.Key_Left
        Return = QtCore.Qt.Key_Return
        Enter = QtCore.Qt.Key_Enter
        Up = QtCore.Qt.Key_Up
        Down = QtCore.Qt.Key_Down
        Control = QtCore.Qt.Key_Control
        U = QtCore.Qt.Key_U
        C = QtCore.Qt.Key_C
        A = QtCore.Qt.Key_A
        Home = QtCore.Qt.Key_Home
        E = QtCore.Qt.Key_E

        lblk = self._doc.lastBlock()
        cpos = self.textCursor().position()
        cblk = self._doc.findBlock(cpos)
        cblkpos = cblk.position()

        passthru = True

        if k in (Return, Enter):
            self.movetoend()

            cpos = self.textCursor().position()
            cblk = self._doc.findBlock(cpos)
            pos = cblk.position()
            blk = self._doc.findBlockByNumber(pos)
            blk = blk.previous()
            if not blk.text():
                blk = self._doc.firstBlock()

            txt = str(blk.text()[4:]).rstrip()
            if txt:
                if self.history and not self.history[-1]:
                    del self.history[-1]
                self.history.append(txt)
            self.historyp = -1

            self.append('')

            if self.cmdthread is None:
                self.cmdthread = CmdThread(self, txt)
                self.cmdthread.start()
                while not self.cmdthread.wait(0) and not self.controlC:
                    for pynguin in self.mw.pynguins:
                        pynguin._r_process_moves()
                    QtGui.QApplication.processEvents(QtCore.QEventLoop.AllEvents)
                if self.controlC:
                    self.cmdthread.terminate()
                    for pynguin in self.mw.pynguins:
                        pynguin._empty_move_queue()
                        pynguin._r_process_moves()
                        pynguin._sync_items()
                    self.append('KeyboardInterrupt\n')
                    self.controlC = False
                    self.needmore = False
                    self.interpreter.resetbuffer()
                self.cmdthread = None

                if not self.needmore:
                    self.write('>>> ')
                else:
                    self.write('... ')

                passthru = False
            else:
                passthru = True

        elif k in (Backspace, Left):
            lblk = self._doc.lastBlock()
            lpos = lblk.position()
            llpos = lblk.position() + lblk.length() - 1

            cpos = self.textCursor().position()
            cblk = self._doc.findBlock(cpos)
            cblkpos = cblk.position()

            if cpos <= lpos + 4:
                passthru = False
            else:
                passthru = True

        elif k in (Up, Down):
            self.scrolldown()

            cpos = self.textCursor().position()
            cblk = self._doc.findBlock(cpos)
            pos = cblk.position()

            txt = str(cblk.text()[4:]).strip()

            if not self.history:
                QtGui.QApplication.beep()

            else:
                changeline = True
                addthisline = False

                lenhist = len(self.history)

                if k==Up and self.historyp==-1:
                    addthisline = True

                if k==Up and lenhist==1:
                    self.historyp -= 1
                elif k==Up and self.historyp <= -lenhist:
                    QtGui.QApplication.beep()
                    changeline = False
                elif k==Up:
                    self.historyp -= 1
                elif k==Down and self.historyp >= -1:
                    QtGui.QApplication.beep()
                    changeline = False
                elif k==Down:
                    self.historyp += 1

                if addthisline:
                    self.history.append(txt)

                if changeline:
                    txt = self.history[self.historyp]
                    endpos = pos + cblk.length() - 1

                    if self.historyp == -1:
                        del self.history[-1]

                    curs = self.textCursor()
                    curs.setPosition(pos+4, 0)
                    curs.setPosition(endpos, 1)
                    curs.removeSelectedText()

                    self.insertPlainText(txt)

            passthru = False

        elif mdf & QtCore.Qt.ControlModifier and k==U:
            #erase from cursor to beginning of line
            self.erasetostart()

        elif mdf & QtCore.Qt.ControlModifier and k==C:
            #send keyboard interrupt
            if self.cmdthread is not None and self.cmdthread.isRunning():
                self.controlC = True
            else:
                self.write('\nKeyboardInterrupt\n')
                self.interpreter.resetbuffer()
                self.write('>>> ')

        elif (mdf & QtCore.Qt.ControlModifier and k==A) or k == Home:
            self.movetostart()
            passthru = False

        elif mdf & QtCore.Qt.ControlModifier and k==E:
            self.movetoend()
            passthru = False

        self.scrolldown()

        if passthru:
            HighlightedTextEdit.keyPressEvent(self, ev)

    def scrolldown(self):
        '''force the console to scroll all the way down, and put
            the cursor after the last letter.
        '''
        cpos = self.textCursor().position()
        cblk = self._doc.findBlock(cpos)
        lblk = self._doc.lastBlock()
        if cblk != lblk:
            lblk = self._doc.lastBlock()
            lpos = lblk.position() + lblk.length() - 1
            curs = self.textCursor()
            curs.setPosition(lpos, 0)
            self.setTextCursor(curs)

        vbar = self.verticalScrollBar()
        vbar.setValue(vbar.maximum())

    def mousePressEvent(self, ev):
        curs = self.cursorForPosition(ev.pos())
        col = curs.columnNumber()
        cpos = curs.position()
        blk = curs.block()
        #blklen = blk.length()
        blktext = str(blk.text())
        promptblk = blktext.startswith('>>>') or blktext.startswith('...')
        if promptblk and col < 4:
            curs.setPosition(cpos + 4-col)
            self.setTextCursor(curs)
        else:
            HighlightedTextEdit.mousePressEvent(self, ev)

    def movetostart(self):
        '''move the cursor to the start of the line (after the prompt)'''
        cpos = self.textCursor().position()
        cblk = self._doc.findBlock(cpos)
        pos = cblk.position()
        curs = self.textCursor()
        curs.setPosition(pos+4, 0)
        self.setTextCursor(curs)

    def movetoend(self):
        '''move the cursor to the end of the line'''
        cpos = self.textCursor().position()
        cblk = self._doc.findBlock(cpos)
        pos = cblk.position()
        endpos = pos + cblk.length() - 1
        curs = self.textCursor()
        curs.setPosition(endpos, 0)
        self.setTextCursor(curs)

    def erasetostart(self):
        '''erase from the current cursor position to the beginning
            of the line
        '''
        cpos = self.textCursor().position()
        cblk = self._doc.findBlock(cpos)
        pos = cblk.position()

        curs = self.textCursor()
        curs.setPosition(pos+4, 0)
        curs.setPosition(cpos, 1)
        curs.removeSelectedText()
