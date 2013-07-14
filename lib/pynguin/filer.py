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

def foo(fp):
    return os.path.splitdrive(fp)[0]


def _related_dir(fp):
    '''return the directory name related to path fp
        that should be used for storing files when not in
        savesingle (.pyn) mode.
    '''
    dirname, fname = os.path.split(fp)
    fbase, fext = os.path.splitext(fname)
    fpd = os.path.join(dirname, fbase+'_pynd')

    return fpd

def writeable(fp, savesingle):
    '''try to write to the given path (and the related directory if
        savesingle is False).

    return True if sucessful, False otherwise
    '''

    try:
        fd = open(fp, 'w')
        fd.write('test')
        fd.close()
        os.remove(fp)
    except IOError:
        return False


    if savesingle:
        return True
    else:
        fpd = _related_dir(fp)
        if not os.path.exists(fpd):
            return False
        fp = os.path.join(fpd, 'test')
        return writeable(fp, True)


def writefile02(self, fp, docs, backup=False):
    '''Write out open files (docs) to file path fp.

    Version 02


    Knows how to deal with 3 kinds of files:
        EXTERNAL files start with '_@@EXTERNAL@@_'
        PYND files (stored in related _pynd directory)
        INTERNAL files

    Creates a zip file called *.pyn and if necessary the related
        directory (like fp with name modified to end with _pynd)
    Also saves file manifest and history in .pyn zipfile.


    When saving INTERNAL files, puts all files in to a folder first
        to make it match the EXTERNAL file saves better.

    '''
    VERSION = b'pyn02'
    
    _, fn = os.path.split(fp)
    fbase, _ = os.path.splitext(fn)
    if not fbase.endswith('_pynd'):
        fbase = fbase + '_pynd'

    z = zipfile.ZipFile(fp, 'w')

    manifest = []

    mselect = self.ui.mselect
    for doc in docs:
        modified = doc.isModified()
        cline, ccol = doc.getCursorPosition()
        code = doc.cleancode()
        doc.beginUndoAction()
        doc.selectAll()
        doc.removeSelectedText()
        doc.insert(code)
        doc.setCursorPosition(cline, ccol)
        doc.setModified(modified)
        doc.endUndoAction()

        logger.info('writing %s' % doc)
        if not backup and doc._filepath is not None:
            efp = doc._filepath
            manifest.append(efp)

            logger.info('external: %s' % efp)

            if efp.startswith('_@@'):
                dirname, _ = os.path.split(fp)
                if dirname:
                    efp = efp.replace('_@@', dirname)
                else:
                    efp = efp[4:]
            self._remwatcher(efp)
            f = open(efp, 'w')
            f.write(code)
            f.close()
            self._addwatcher(efp, doc)

            doc.setModified(False)
        
        else:
            arcname = '%05d.py' % n

            zipi = zipfile.ZipInfo()
            zipi.filename = os.path.join(fbase, arcname)
            manifest.append(zipi.filename)
            zipi.compress_type = zipfile.ZIP_DEFLATED
            zipi.date_time = time.localtime()
            zipi.external_attr = 0o644 << 16
            zipi.comment = VERSION
            z.writestr(zipi, code.encode('utf-8'))

    historyname = '@@history@@'
    history = '\n'.join(self.interpretereditor.history)

    zipi = zipfile.ZipInfo()
    zipi.filename = os.path.join(fbase, historyname)
    zipi.compress_type = zipfile.ZIP_DEFLATED
    zipi.date_time = time.localtime()
    zipi.external_attr = 0o644 << 16
    zipi.comment = VERSION
    z.writestr(zipi, history) #.encode('utf-8'))

    manifestname = '@@manifest@@'
    zipi = zipfile.ZipInfo()
    zipi.filename = os.path.join(fbase, manifestname)
    zipi.compress_type = zipfile.ZIP_DEFLATED
    zipi.date_time = time.localtime()
    zipi.external_attr = 0o644 << 16
    zipi.comment = VERSION
    manifeststr = '\n'.join(manifest)
    z.writestr(zipi, manifeststr.encode('utf-8'))

    z.close()
