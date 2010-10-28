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
import code
import time
import logging
logger = logging.getLogger('PynguinLogger')

from PyQt4 import QtCore, QtGui

from editor import HighlightedTextEdit
import pynguin
import conf


class Console(code.InteractiveConsole):
    def __init__(self, ilocals, editor):
        code.InteractiveConsole.__init__(self, ilocals)
        self.editor = editor

    def showtraceback(self):
        logger.info('showtraceback')
        exc_type, exc_value, exc_traceback = sys.exc_info()
        if exc_type is KeyboardInterrupt and conf.KeyboardInterrupt_quiet:
            pass
        else:
            code.InteractiveConsole.showtraceback(self)
        #logging.debug('foo')


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

        #logging.debug('THREAD DONE')

class Interpreter(HighlightedTextEdit):
    def __init__(self, parent):
        HighlightedTextEdit.__init__(self)
        self.mw = parent
        self.history = []
        self._outputq = []
        self.historyp = -1

        self.reading = False

        self.save_stdout = sys.stdout
        self.save_stdin = sys.stdin
        self.save_stderr = sys.stderr

        sys.stdout = self
        sys.stderr = self
        sys.stdin = self

        self.setWordWrapMode(QtGui.QTextOption.WrapAnywhere)

        self.needmore = False
        self.cmdthread = None

        QtCore.QTimer.singleShot(10, self.writeoutputq)

        self.write('>>> ')

        self.col0 = 4

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

    def readline(self):
        self.reading_buffer = []
        self.reading = True
        while self.reading:
            time.sleep(0.1)
        return ''.join(self.reading_buffer)

    def write(self, text):
        '''cannot write directly to the console...
            instead, append this text to the output queue for later use.
        '''
        if text:
            self._outputq.append(text)
            if len(self._outputq) > 10:
                time.sleep(.1)

        if pynguin.Pynguin.ControlC == 1:
            pynguin.Pynguin.ControlC += 1
            raise KeyboardInterrupt

    def writeoutputq(self):
        '''process the text output queue. Must be done from the main thread.
        '''
        while self._outputq:
            text = self._outputq.pop(0)
            self.insertPlainText(text)
            QtCore.QTimer.singleShot(100, self.scrolldown)

        QtCore.QTimer.singleShot(10, self.writeoutputq)

    def checkprompt(self):
        cpos = self.textCursor().position()
        cblk = self._doc.findBlock(cpos)
        blktxt4 = cblk.text()[:4]
        blen = cblk.length()
        if blen == 0:
            self.write('>>> ')
        elif blktxt4 != '>>> ':
            self.write('\n')
            self.write('>>> ')

    def cleanup_ControlC(self):
        pynguin.Pynguin.ControlC = False
        self.cmdthread = None
        for pyn in self.mw.pynguins:
            if not hasattr(pyn, 'gitem') or pyn.gitem is None:
                self.mw.pynguins.remove(pyn)

    def testthreaddone(self):
        self.cleanup_ControlC()
        logger.info('self.testthreaddone')
        QtCore.QTimer.singleShot(100, self.checkprompt)


    def threaddone(self):
        self.cleanup_ControlC()
        logger.info('self.threaddone')

        if not self.needmore:
            self.write('>>> ')
        else:
            self.write('... ')


    def keyPressEvent(self, ev):
        k = ev.key()
        logger.debug('Key: %s' % k)
        mdf = ev.modifiers()

        if self.reading:
            try:
                self.reading_buffer.append(chr(k))
            except:
                pass
            logger.info(self.reading_buffer)

        Tab = QtCore.Qt.Key_Tab
        Backtab = QtCore.Qt.Key_Backtab
        Backspace = QtCore.Qt.Key_Backspace
        Left = QtCore.Qt.Key_Left
        Return = QtCore.Qt.Key_Return
        Enter = QtCore.Qt.Key_Enter
        Up = QtCore.Qt.Key_Up
        PageUp = QtCore.Qt.Key_PageUp
        Down = QtCore.Qt.Key_Down
        PageDown = QtCore.Qt.Key_PageDown
        Control = QtCore.Qt.ControlModifier
        Shift = QtCore.Qt.ShiftModifier
        U = QtCore.Qt.Key_U
        C = QtCore.Qt.Key_C
        A = QtCore.Qt.Key_A
        Home = QtCore.Qt.Key_Home
        E = QtCore.Qt.Key_E
        D = QtCore.Qt.Key_D

        lblk = self._doc.lastBlock()
        cpos = self.textCursor().position()
        cblk = self._doc.findBlock(cpos)
        cblkpos = cblk.position()

        passthru = True
        scrolldown = True

        if k in (Return, Enter):
            if self.reading:
                self.reading = False

            self.movetoend()

            cpos = self.textCursor().position()
            cblk = self._doc.findBlock(cpos)
            pos = cblk.position()
            blk = self._doc.findBlockByNumber(pos)
            blk = blk.previous()
            if not blk.text():
                blk = self._doc.firstBlock()

            txt = unicode(blk.text()[4:]).rstrip()
            if txt:
                if self.history and not self.history[-1]:
                    del self.history[-1]
                self.history.append(txt)
            self.historyp = -1

            self.append('')

            if self.cmdthread is None:
                self.cmdthread = CmdThread(self, txt)
                self.cmdthread.finished.connect(self.threaddone)
                self.cmdthread.start()

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

        elif mdf & Shift and k==Up:
            vbar = self.verticalScrollBar()
            vbar.setValue(vbar.value()-vbar.singleStep())
            passthru = False

        elif mdf & Shift and k==Down:
            vbar = self.verticalScrollBar()
            vbar.setValue(vbar.value()+vbar.singleStep())
            passthru = False

        elif mdf & Shift and k==PageUp:
            vbar = self.verticalScrollBar()
            vbar.setValue(vbar.value()-vbar.pageStep())
            passthru = False

        elif mdf & Shift and k==PageDown:
            vbar = self.verticalScrollBar()
            vbar.setValue(vbar.value()+vbar.pageStep())
            passthru = False

        elif k in (Up, Down):
            self.scrolldown()

            cpos = self.textCursor().position()
            cblk = self._doc.findBlock(cpos)
            pos = cblk.position()

            txt = unicode(cblk.text()[4:]).strip()

            if self.cmdthread is not None:
                pass

            elif not self.history:
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

        elif mdf & Control and k==U:
            #erase from cursor to beginning of line
            self.erasetostart()

        elif mdf & Control and mdf & Shift and k==C:
            # Copy
            self.copy()
            scrolldown = False

        elif mdf & Control and k==C:
            #send keyboard interrupt
            logger.info('Ctrl-C pressed')
            if self.cmdthread is not None and self.cmdthread.isRunning():
                logger.info('Thread running')
                pynguin.Pynguin.ControlC = True
                #logging.debug('CCT')
                self.mw.pynguin._empty_move_queue()
                for pyn in self.mw.pynguins:
                    pyn._sync_items()
                #logging.debug('synced')
                self.needmore = False
                self.interpreter.resetbuffer()

            else:
                pynguin.Pynguin.ControlC = False
                self.cmdthread = None
                logger.info('No thread running')
                if not conf.KeyboardInterrupt_quiet:
                    self.write('\nKeyboardInterrupt\n')
                else:
                    self.write('\n')
                self.interpreter.resetbuffer()
                self.write('>>> ')

        elif (mdf & Control and k==A) or k == Home:
            self.movetostart()
            passthru = False

        elif mdf & Control and k==E:
            self.movetoend()
            passthru = False

        elif mdf & Control and k==D:
            self.mw.close()
            passthru = False

        if scrolldown and ev.text():
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

    def mouseReleaseEvent(self, ev):
        ccurs = self.textCursor()
        hassel = ccurs.hasSelection()

        curs = self.cursorForPosition(ev.pos())
        col = curs.columnNumber()
        cpos = curs.position()
        blk = curs.block()
        #blklen = blk.length()
        blktext = unicode(blk.text())
        promptblk = blktext.startswith('>>>') or blktext.startswith('...')
        if not hassel and promptblk and col < 4:
            curs.setPosition(cpos + 4-col)
            self.setTextCursor(curs)
        else:
            HighlightedTextEdit.mouseReleaseEvent(self, ev)

    def contextMenuEvent(self, ev):
        menu = self.createStandardContextMenu()
        actions = menu.actions()
        undo = actions[0]
        redo = actions[1]
        sep0 = actions[2]
        cut = actions[3]
        delete = actions[6]
        menu.removeAction(undo)
        menu.removeAction(redo)
        menu.removeAction(sep0)
        menu.removeAction(cut)
        menu.removeAction(delete)
        menu.exec_(ev.globalPos())

    def insertFromMimeData(self, data):
        self.scrolldown()
        HighlightedTextEdit.insertFromMimeData(self, data)

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
