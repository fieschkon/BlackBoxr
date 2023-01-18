import os
import platform
from typing import cast
#from BlackBoxr import app
from PySide6.QtGui import QUndoStack
from appdirs import *
from BlackBoxr.modules.ExtensionLoader import ExtensionLoader, Plugin

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

copiedItems = []

### Directory Data ###

datadir = user_data_dir(AppName, Org)

tmpdir = user_cache_dir(AppName, Org)

makeDir(datadir)
makeDir(tmpdir)

searchdirs = [datadir]

def buildPlugins():
    print(f'Building Plugins...')
    rawplugins : list[Plugin] = ExtensionLoader.ExtractPackages()
    processedplugins = {}
    for plugin in rawplugins:
        category = plugin.plugin.role
        print(f'Found {plugin.plugin.name}, adding to {plugin.plugin.role.name}')
        if category not in list(processedplugins.keys()):
            processedplugins[category] = [plugin]
        else:
            processedplugins[category].append(plugin)
    return processedplugins

plugins = buildPlugins()  

def getFilesInDataPaths():
    files = []
    for dir in searchdirs:
        for file in os.listdir(dir):

            files.append(os.path.join(dir, file))
    return files

# Runtime Objects
dashboard = None