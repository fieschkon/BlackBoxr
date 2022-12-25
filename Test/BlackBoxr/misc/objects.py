import os
import platform
from typing import cast
#from BlackBoxr import app
from PySide6.QtGui import QUndoStack
from appdirs import *

from BlackBoxr.utilities import makeDir

AppName = "BlackBoxr"
Org = "Bingus"

qapp = cast('app.Application', None)
undoStack = QUndoStack()
configdir = user_config_dir(AppName, Org)
makeDir(configdir)
configfile = "{}/config.ini".format(configdir)

### Runtime Data ###

systems = []

### Directory Data ###

datadir = user_data_dir(AppName, Org)

tmpdir = user_cache_dir(AppName, Org)

makeDir(datadir)
makeDir(tmpdir)

searchdirs = [datadir]

def getFilesInDataPaths():
    files = []
    for dir in searchdirs:
        for file in os.listdir(dir):

            files.append(os.path.join(dir, file))
    return files

# Runtime Objects
dashboard = None