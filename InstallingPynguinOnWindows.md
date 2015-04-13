You may want to get someone who has more computer experience help you get everything installed. It can be complicated and frustrating sometimes.

# The Portable Python Method #

This may be the easiest way to go. It does not require "installing" anything on your Windows computer.


## Get Portable Python ##

  * Go to http://www.portablepython.com/
  * Get the latest Portable Python that starts with 3
    * Portable Python includes everything you will need to run pynguin
    * Get the latest version of pynguin
  * Unpack Portable Python
  * Unpack pynguin
  * You will need to start pynguin from a command line
    * The command will look _something like_
      * `\path\to\portablepython\App\python.exe \path\to\pynguin_folder\pynguin`
    * Once you have the command working, put it in a .bat file so you can just click on it to run pynguin


# The Install Python and PyQt Method #

## Download ##

Get the latest version of Pynguin from [the download page](http://code.google.com/p/pynguin/downloads/list)

Get the one with the .zip file extension


## Extract ##

You cannot open a .zip file with Python. Python only opens .py files.

You need to extract the .zip file using a program that can extract .zip archives.

Assuming you are using Windows XP, Vista, or 7, you should be able to just double-click on the pynguin-0.14.zip file in windows explorer to extract the files from the archive.

That should leave you with a folder called pynguin-0.14


## Read the README ##

See the instructions in the [README](http://pynguin.googlecode.com/hg/README) file.



## Dependencies ##
### These are other installs you must do before Pynguin will work ###

Now, you need to have a 3-series Python installed. (That does not include Iron Python which is a completely different thing altogether.) I recommend Python-3.2.4 :

http://www.python.org/ftp/python/3.2.4/python-3.2.4.msi


You will also need a recent PyQt. Probably this one:

http://downloads.sourceforge.net/project/pyqt/PyQt4/PyQt-4.9.6/PyQt-Py3.2-x86-gpl-4.9.6-1.exe

Install Python first, then PyQt.


## Run ##

There is no way, currently, to run Pynguin by double-clicking an icon on windows. You will need to run it from the command line.

Open your command prompt and change directories to the pynguin folder.

Run pynguin with:

python pynguin

or you may need to do something like

c:\path\to\python pynguin

Once you get the necessary command worked out, you can put it in to a .bat file to make a clickable launcher.


## Help Out the Next Person ##

If you have any comments, clarifications, or questions, please post them below.

If you know how to set things up to be easier for users to run the program on windows, please contact me.