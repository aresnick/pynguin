from distutils.core import setup
from glob import glob
from os import listdir
from os.path import isdir, isfile
import os
import sys

NAME = 'pynguin'
VERSION = '0.10'

DESC = 'Python-based turtle graphics application'

LONG_DESC = '''\
Pynguin is a python-based turtle graphics application.
It combines an editor, interactive interpreter, and
graphics display area.

http://pynguin.googlecode.com/
'''

CLASSIFIERS = [
    'Development Status :: 3 - Alpha',
    'Environment :: X11 Applications :: Qt',
    'Intended Audience :: End Users/Desktop',
    'Intended Audience :: Education',
    'License :: OSI Approved :: GNU General Public License (GPL)',
    'Operating System :: OS Independent',
    'Programming Language :: Python :: 2',
    'Topic :: Education',
    'Natural Language :: English',
]

os.chdir(os.path.abspath(os.path.dirname(__file__)))

DATA_FILES = [('share/doc/pynguin', ['README', 'COPYING', ])]

# ui
DATA_FILES += [('share/pynguin/ui', glob('data/ui/*.ui'))]
DATA_FILES += [('share/pynguin/images', glob('data/images/*'))]

# examples
DATA_FILES += [('share/doc/pynguin/examples', glob('doc/examples/*.pyn'))]

# worksheets
DATA_FILES += [('share/doc/pynguin', glob('doc/worksheets/*.pdf'))]



# Data
#DATA_FILES += [('share/applications', ['pynguin.desktop'])]
#DATA_FILES += [('share/icons/hicolor/scalable/apps', ['pynguin.svg'])]
#DATA_FILES += [('share/pixmaps', ['pynguin.svg'])]
#DATA_FILES += [('share/icons/hicolor/24x24/apps', ['pynguin.png'])]

# Manpages
#DATA_FILES += [('share/man/man1', ['manpages/pynguin.1.gz'])]


# Packages
PACKAGES = ['pynguin']

# Setup
setup (
    name             = NAME,
    version          = VERSION,
    author           = 'Lee Harr',
    author_email     = 'missive@hotmail.com',
    maintainer       = 'Lee Harr',
    classifiers      = CLASSIFIERS,
    keywords         = 'python pyqt turtle',
    description      = DESC,
    long_description = LONG_DESC,
    license          = 'GPL3',
    url              = 'http://pynguin.googlecode.com',
    download_url     = 'http://code.google.com/p/pynguin/downloads/list',
    package_dir      = {'': 'lib'},
    packages         = PACKAGES,
    data_files       = DATA_FILES,
    scripts          = ['pynguin']
)
