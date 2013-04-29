# Copyright 2010-2012 Lee Harr
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
from PyQt4.Qsci import QsciScintilla, QsciLexerPython

from . import pynguin
from . import conf

from . import thread2a


class Console(code.InteractiveConsole):
    def __init__(self, ilocals, editor):
        code.InteractiveConsole.__init__(self, ilocals)
        self.editor = editor

    def showtraceback(self):
        logger.info('showtraceback')
        settings = QtCore.QSettings()
        quiet = settings.value('console/quietinterrupt', False, bool)
        exc_type, exc_value, exc_traceback = sys.exc_info()
        logger.info(exc_type)
        logger.info(exc_value)
        logger.info(exc_traceback)
        if exc_type is KeyboardInterrupt and quiet:
            pass
        else:
            code.InteractiveConsole.showtraceback(self)
        #logging.debug('foo')


class WatcherThread(QtCore.QThread):
    def __init__(self, t):
        QtCore.QThread.__init__(self)
        self.t = t

    def run(self):
        #logger.info('WT start')
        self.t.join()
        #logger.info('WT finish')

class CmdThread(thread2a.Thread):
    def __init__(self, ed, txt):
        '''set up a separate thread to run the code given in txt in the
            InteractiveInterpreter ed.'''
        thread2a.Thread.__init__(self)
        self.ed = ed
        self.txt = txt
    def run(self):
        ed = self.ed
        lines = self.txt.split('\n')
        if len(lines) > 1:
            ed.interpreter.runcode(self.txt)
        else:
            ed.needmore = ed.interpreter.push(self.txt)

        #logger.debug('THREAD DONE')

class Interpreter(QsciScintilla):
    def __init__(self, parent):
        QsciScintilla.__init__(self)
        self.mw = parent
        self.history = []
        self._outputq = []
        self.historyp = -1

        self.reading = False
        self.pt = None

        self.save_stdout = sys.stdout
        self.save_stdin = sys.stdin
        self.save_stderr = sys.stderr

        sys.stdout = self
        sys.stderr = self
        sys.stdin = self

        self.setup()

        self.needmore = False
        self.cmdthread = None

        QtCore.QTimer.singleShot(10, self.writeoutputq)

        self.write('>>> ')

        self.col0 = 4

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

        ## Margin 0 is used for prompts
        #self.setMarginsBackgroundColor(QtGui.QColor("#444444"))
        #self.setMarginsForegroundColor(QtGui.QColor('#999999'))
        #self.setMarginType(QsciScintilla.SC_MARGIN_TEXT)
        #fontmetrics = QtGui.QFontMetrics(self._font)
        #self.setMarginWidth(0, fontmetrics.width(">>>"))

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

    def flush(self):
        # to suppress AttributeError ...
        # Not sure why that is happening and why it is not crashing, but...
        pass

    def clear(self):
        self.history = []
        self._outputq = []
        QsciScintilla.clear(self)
        self.write('>>> ')

    def addcmd(self, cmd, force=False):
        '''clear the current line and write the given command to the interpreter'''

        if not force and self.cmdthread is not None:
            # Don't bother writing cmd if there is already
            #   a thread in progress...
            # force=True forces write even if cmd in progress.
            return

        self.clearline()
        self.write(cmd)
        if cmd[-1] == '\n':
            self.write('>>> ')
            self.history.append(cmd.rstrip())

    def readline(self):
        self.reading = True
        while self.reading:
            time.sleep(0.1)

        pt2 = self.pt
        self.pt = None

        lenbefore = len(pt2)
        pt = self.text()
        r = pt[lenbefore:]
        r = r.rstrip('\n')
        if not r:
            r = '\n'
        return r

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
            cline, ccol = self.getCursorPosition()
            self.insert(text)
            self.setCursorPosition(cline, ccol+len(text))
            QtCore.QTimer.singleShot(100, self.scrolldown)

        QtCore.QTimer.singleShot(10, self.writeoutputq)

    def checkprompt(self):
        cline, ccol = self.getCursorPosition()
        txt = self.text(cline)
        if not txt:
            self.write('>>> ')

    def cleanup_ControlC(self):
        pynguin.Pynguin.ControlC = False
        self.cmdthread = None

        to_remove = []
        for pyn in self.mw.pynguins:
            if not hasattr(pyn, 'gitem') or pyn.gitem is None:
                to_remove.append(pyn)

        for pyn in to_remove:
            self.mw._defunct_pynguins.append(pyn)
            self.mw.pynguins.remove(pyn)

    def testthreaddone(self):
        self.cleanup_ControlC()
        QtCore.QTimer.singleShot(100, self.checkprompt)


    def threaddone(self):
        self.cleanup_ControlC()

        if not self.needmore:
            self.checkprompt()
        else:
            self.write('... ')
            self.write(' ' * self._indent_level)
            self._indent_level = 0


    def go(self):
        'react as if the ENTER key has been pressed on the keyboard'
        ev = QtGui.QKeyEvent(QtCore.QEvent.KeyPress,
                                QtCore.Qt.Key_Enter,
                                QtCore.Qt.NoModifier, '\n')
        self.keyPressEvent(ev)

    def spin(self, n, delay=0.01):
        '''call processEvents n times.
            If n is 0, continue until cmdthread is None
        '''
        if n:
            for i in range(n):
                time.sleep(delay)
                QtGui.QApplication.processEvents(QtCore.QEventLoop.AllEvents)
        else:
            self.spin(1)
            cs = 500
            while self.cmdthread is not None:
                if not cs:
                    logger.info('spin fail')
                    self.ctrl_c_thread_running()
                    return False
                cs -= 1
                time.sleep(delay)
                QtGui.QApplication.processEvents(QtCore.QEventLoop.AllEvents)

        return True

    def indentation(self, linen):
        i = 0
        txt = self.text(linen)[4:]
        if txt.isspace():
            return len(txt)

        for i, c in enumerate(txt):
            if c != ' ':
                break
        return i

    def keyPressEvent(self, ev):
        k = ev.key()
        mdf = ev.modifiers()

        if self.reading and self.pt is None:
            self.pt = self.text()

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
        V = QtCore.Qt.Key_V
        X = QtCore.Qt.Key_X
        A = QtCore.Qt.Key_A
        Home = QtCore.Qt.Key_Home
        E = QtCore.Qt.Key_E
        D = QtCore.Qt.Key_D
        H = QtCore.Qt.Key_H
        Z = QtCore.Qt.Key_Z

        passthru = True
        scrolldown = True

        if k in (Return, Enter):
            if self.reading:
                self.reading = False

            self.movetoend()

            cline, ccol = self.getCursorPosition()
            txt = self.text(cline)
            txt = txt[4:].rstrip()
            if txt:
                if self.history and not self.history[-1]:
                    # last history entry is blank line
                    del self.history[-1]
                self.history.append(txt)
            self.historyp = -1

            self.append('\n')

            if self.cmdthread is None:
                i = self.indentation(cline)
                if txt.endswith(':'):
                    i += 4
                self._indent_level = i

                self.mw.pynguin._mark_undo()

                self.cmdthread = CmdThread(self, txt)
                self.cmdthread.start()
                self.watcherthread = WatcherThread(self.cmdthread)
                self.watcherthread.finished.connect(self.threaddone)
                self.watcherthread.start()

                passthru = False
            else:
                passthru = True

        elif k in (Backspace, Tab, Backtab):
            cline, ccol = self.getCursorPosition()
            i = self.indentation(cline)

            if ccol < 4:
                passthru = False
                self.scroll_left()
            elif ccol <= i + 4:
                passthru = False
                spaces = ccol % 4
                if not spaces:
                    spaces = 4
                if k != Tab:
                    self.setSelection(cline, 4, cline, 4+spaces)
                    self.replaceSelectedText('')
                    self.setCursorPosition(cline, ccol-spaces)
                else:
                    self.insert(' ' * spaces)
                    self.setCursorPosition(cline, 4+i+spaces)
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

            cline, ccol = self.getCursorPosition()

            txt = self.text(cline)[4:].strip()

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
                    endpos = len(self.text(cline))

                    if self.historyp == -1:
                        del self.history[-1]

                    self.setSelection(cline, 4, cline, endpos)
                    self.replaceSelectedText(txt)

            passthru = False

        elif mdf & Control and k==U:
            #erase from cursor to beginning of line
            self.scroll_left()
            self.erasetostart()

        elif mdf & Control and k==X:
            # Cut # No action. Disabled.
            scrolldown = False
            passthru = False

        elif mdf & Control and mdf & Shift and k==X:
            # Cut
            self.cut() # No action. Disabled.
            scrolldown = False
            passthru = False

        elif mdf & Control and mdf & Shift and k==C:
            # Copy
            self.copy()
            scrolldown = False
            passthru = False

        elif mdf & Control and mdf & Shift and k==V:
            # Paste
            self.paste()
            scrolldown = False
            passthru = False

        elif mdf & Control and k==Z:
            self.mw.pynguin._undo()
            scrolldown = True
            passthru = False

        elif mdf & Control and k==C:
            #send keyboard interrupt
            logger.info('Ctrl-C pressed')

            import threading
            if hasattr(threading, 'threads'):
                for pyn in threading.threads:
                    threading.threads[pyn] = 0

            if self.cmdthread is not None and self.cmdthread.isAlive():
                self.ctrl_c_thread_running()

            else:
                self.ctrl_c_no_thread_running()

            self.sync_pynguins_lists()

        elif (mdf & Control and k==A) or k == Home:
            self.movetostart()
            self.scroll_left()
            passthru = False
            scrolldown = False

        elif mdf & Control and k==E:
            self.movetoend()
            passthru = False

        elif mdf & Control and k==D:
            self.mw.close()
            passthru = False

        elif mdf & Control and mdf & Shift and k==H:
            # Clear history
            self.history = []

        if scrolldown and ev.text():
            self.scrolldown()

        if passthru:
            QsciScintilla.keyPressEvent(self, ev)

    def ctrl_c_thread_running(self):
        pynguin.Pynguin.ControlC = True
        pynguin.Pynguin._stop_testall = True
        self.mw.pynguin._empty_move_queue(lock=True)
        for pyn in self.mw.pynguins:
            pyn._sync_items()
        self.needmore = False
        self.interpreter.resetbuffer()

    def ctrl_c_no_thread_running(self):
        pynguin.Pynguin.ControlC = False
        pynguin.Pynguin._stop_testall = True
        self.cmdthread = None

        self.mw.pynguin._empty_move_queue(lock=True)

        settings = QtCore.QSettings()
        quiet = settings.value('console/quietinterrupt', False, bool)

        self.movetoend()
        if not quiet:
            self.write('\nKeyboardInterrupt\n')
        else:
            self.write('\n')
        self.interpreter.resetbuffer()
        self.write('>>> ')

    def sync_pynguins_lists(self):
        for p in self.mw._pynguins:
            if p not in self.mw.pynguins:
                p.remove()

        if self.mw.pynguin not in self.mw.pynguins:
            self.mw.pynguins.append(self.mw.pynguin)

    def scrolldown(self):
        '''force the console to scroll all the way down.

            If the cursor is already in the last line,
                do not change location of the cursor.

            If not, move the cursor to the last position
                in the line.
        '''

        txt = self.text()
        nlines = len(txt.split('\n'))
        lastlinen = nlines - 1
        lastline = self.text(lastlinen)

        cline, ccol = self.getCursorPosition()

        if cline != lastlinen:
            self.setCursorPosition(lastlinen, len(lastline))

        if ccol < 4:
            self.setCursorPosition(lastlinen, 4)

        vbar = self.verticalScrollBar()
        vbar.setValue(vbar.maximum())

    def scroll_left(self):
        hbar = self.horizontalScrollBar()
        hbar.setValue(hbar.minimum())

    def mouseReleaseEvent(self, ev):
        QsciScintilla.mouseReleaseEvent(self, ev)

        cline, ccol = self.getCursorPosition()
        txt = self.text(cline)
        if ccol < 4 and not self.hasSelectedText():
            if txt.startswith('>>>') or txt.startswith('...'):
                self.setCursorPosition(cline, 4)

    def contextMenuEvent(self, ev):
        '''right-click to pop up the context menu.
        Adjust displayed shortcut key combo since this is an interactive
            shell and ctrl-c is needed for stopping running code.

        Connection of actual typed shortcuts is in keyPressEvent()
        '''

        menu = self.createStandardContextMenu()
        actions = menu.actions()
        undo = actions[0]
        redo = actions[1]
        sep0 = actions[2]
        cut = actions[3]
        copy = actions[4]
        paste = actions[5]
        delete = actions[6]
        menu.removeAction(undo)
        menu.removeAction(redo)
        menu.removeAction(sep0)
        menu.removeAction(cut)

        menu.removeAction(copy)
        copyaction = QtGui.QAction('Copy', menu)
        copyshortcut = QtGui.QKeySequence(QtCore.Qt.CTRL +
                                            QtCore.Qt.SHIFT +
                                            QtCore.Qt.Key_C)
        copyaction.setShortcut(copyshortcut)
        copyaction.triggered.connect(self.copy)
        menu.insertAction(paste, copyaction)

        menu.removeAction(paste)
        pasteaction = QtGui.QAction('Paste', menu)
        pasteshortcut = QtGui.QKeySequence(QtCore.Qt.CTRL +
                                            QtCore.Qt.SHIFT +
                                            QtCore.Qt.Key_V)
        pasteaction.setShortcut(pasteshortcut)
        pasteaction.triggered.connect(self.paste)
        menu.insertAction(delete, pasteaction)

        menu.removeAction(delete)
        menu.exec_(ev.globalPos())

    def cut(self):
        # cut disabled
        pass

    def insertFromMimeData(self, data):
        self.scrolldown()
        QsciScintilla.insertFromMimeData(self, data)

    def movetostart(self):
        '''move the cursor to the start of the line (after the prompt)'''
        cline, ccol = self.getCursorPosition()
        self.setCursorPosition(cline, 4)

    def movetoend(self):
        '''move the cursor to the end of the line'''
        cline, ccol = self.getCursorPosition()
        self.setCursorPosition(cline, len(self.text(cline)))

    def erasetostart(self):
        '''erase from the current cursor position to the beginning
            of the line
        '''
        cline, ccol = self.getCursorPosition()
        if ccol == 4:
            # line is already empty
            return
        self.setSelection(cline, 4, cline, ccol)
        self.replaceSelectedText('')
        self.setCursorPosition(cline, 4)

    def clearline(self):
        self.scrolldown()
        self.movetoend()
        self.erasetostart()
