version = 'pynguin-0.11'

bug_url = 'http://code.google.com/p/pynguin/issues/list'

LOG_FILENAME = 'logfile.log'

backupfolder = '' # blank means save in current directory
backupfile = 'backup~%s.pyn' # must have %s that will be replaced with number
backuprate = 3 # minutes between backups
keepbackups = 5 # set to 0 to disable automatic backups

KeyboardInterrupt_quiet = True

track_main_pynguin = False

# The default is to save the Pynguin file list as
#   a single file with all of the files zipped together.
# To override this behavior, and instead save the files
#   as a directory full of files, change use_pyn to False
use_pyn = True

# If you will be editing with an external editor, you
#   may want pynguin to automatically monitor and reload
#   those external files any time you make changes
# You may also want to automatically have the Test/Run
#   function run when an external file changes
auto_refresh_external = True
auto_test_external = True
