#!/usr/bin/env python3
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
import os


def setup_devel():
    # Change current dir to where this file lives
    filepath = os.path.realpath(__file__)
    filedir, _ = os.path.split(filepath)
    os.chdir(filedir)

    # Use the pynguin lib here in the lib folder.
    # For development, or running from the source
    #   folder instead of a proper install.
    sys.path.insert(0, 'lib')

def make_deb():
    print('''
Not implemented for Python 3 deb build.

Read pynguin source for manual deb build instructions.
''')
    # New steps for python3 deb build:
    # from http://wiki.debian.org/Python/Packaging
    #
    # Create tarball. Name as pynguin-X.Y.tar.gz
    # Move it to a new workspace (new folder)
    # py2dsc -m "Lee Harr <missive@hotmail.com>" pynguin-X.Y.tar.gz
    # cd deb_dist/pynguin-X.Y
    # Modify debian/changelog
    #   # Change version "unstable" to "quantal"
    # Modify debian/control
    #   # Change package name to pynguin
    #   # Change all X-Python-Version lines to X-Python3-Version: >= 3.2
        # Add ", python3 (>= 3.2)" to Build-Depends
    # Modify debian/rules
    #   # Comment out export DH_OPTIONS line
    #   # Add lines:
    #       #override_dh_auto_install:
    #       #(tab) python3 setup.py install --root=debian/pynguin --install-layout=deb
    #       #override_dh_auto_build:
    #       #override_dh_compress:
    #       #(tab) dh_compress -X.pyn
    # For .deb:
    #   # debuild
    # For PPA:
    #   # debuild -S -sa
    #   # dput ppa:missive/ppa pynguin_X.Y-Z_source.changes

if '-d' in sys.argv:
    setup_devel()

    if 'MAKEDEB' in sys.argv:
        make_deb()
        sys.exit(0)


try:
    from pynguin import main
except ImportError:
    # No install found. Try to locate pynguin lib locally
    if '-d' not in sys.argv:
        sys.argv.append('-d')

    setup_devel()

    try:
        from pynguin import main
    except ImportError:
        print('Unable to locate the pynguin libraries.')
        print('Check your installation.')
        main = False


if main:
    if '-D' in sys.argv:
        main.setup_logging()

    from pynguin import util
    if not util.check_data_doc_dir():
        print('Unable to locate pynguin data.')
        print('Check your installation.')
        main = False

    if util.__file__.startswith('/usr/local') and sys.prefix == '/usr':
        print()
        print('If this is a Debian or Ubuntu system,')
        print('You may have forgotten to pass')
        print('--install-layout=deb')
        print('when installing.')


def help():
    from pynguin import conf
    print(conf.version)
    print()
    print('options:')
    print('  -h : this help text')
    print('  -d : development mode. Run from local directory')
    print('  -D : debug mode. Write debug info to log file')
    print(' DUMP <filename> :')
    print('       dump contents of pynguin file to standard output')
    print('  -d MAKEDEB : create debian package')

if '-h' in sys.argv:
    help()
elif main and 'DUMP' in sys.argv:
    main.dumpfile()
elif main:
    main.run()
else:
    input()
