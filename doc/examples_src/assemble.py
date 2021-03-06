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


import os
import zipfile
import time

def zip_pyn(ex, zfp, files, d):
    VERSION = b'pyn01'

    z = zipfile.ZipFile(zfp, 'w')
    for f in files:
        exp = os.path.join(ex, f)
        if '@@history@@' in f:
            data = open(exp).read()
            #history = data.decode('utf-8')

            zipi = zipfile.ZipInfo()
            zipi.filename = os.path.join(d, f)
            zipi.compress_type = zipfile.ZIP_DEFLATED
            zipi.date_time = time.localtime()
            zipi.external_attr = 0o644 << 16
            zipi.comment = VERSION
            z.writestr(zipi, data) #history.encode('utf-8'))

        elif f.endswith('.py'):
            data = open(exp).read()
            #code = data.decode('utf-8')

            zipi = zipfile.ZipInfo()
            zipi.filename = os.path.join(d, f)
            zipi.compress_type = zipfile.ZIP_DEFLATED
            zipi.date_time = time.localtime()
            zipi.external_attr = 0o644 << 16
            zipi.comment = VERSION
            z.writestr(zipi, data) #code.encode('utf-8'))

        else:
            print('ERROR. Unknown file: %s' % f)


def make_pyn(ex):
    manif = os.path.join(ex, '@@manifest@@')
    if os.path.exists(manif):
        os.remove(manif)

    histf = os.path.join(ex, '@@history@@')
    history = open(histf, 'w')
    history.close()

    if ex.endswith('_pynd'):
        exfile = '%s.pyn' % ex[:-5]
        d = ex
    elif ex.endswith('_pynd/'):
        exfile = '%s.pyn' % ex[:-6]
        d = ex
    else:
        exfile = '%s.pyn' % ex
        d = ex + '_pynd'

    fp = os.path.join('..', 'examples', exfile)
    files = os.listdir(ex)

    print(fp)
    print(files)
    zip_pyn(ex, fp, files, d)

def make_all():
    dirs = get_ex_dirs()
    for ex in dirs:
        make_pyn(ex)

def cleanup():
    dirs = get_ex_dirs()
    for ex in dirs:
        files = os.listdir(ex)
        for f in files:
            if f.startswith('##'):
                n = f[2:7]
                fpf = os.path.join(ex, f)
                fpt = os.path.join(ex, n + '.py')
                os.rename(fpf, fpt)

        if not ex.endswith('_pynd'):
            os.rename(ex, ex+'_pynd')

def get_ex_dirs():
    dirs = [d for d in os.listdir('.') if os.path.isdir(d)]
    return dirs

if __name__ == '__main__':
    import sys
    if len(sys.argv)==1:
        make_all()
    elif '-C' in sys.argv:
        cleanup()
    elif len(sys.argv)==2:
        make_pyn(sys.argv[1])
