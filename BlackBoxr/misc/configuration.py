import configparser
import os
import typing
from typing import NewType
from PySide6.QtGui import QColor
import qdarktheme
from BlackBoxr import utilities
from BlackBoxr.misc import objects
from BlackBoxr.graphics.GUITypes import ThemedColor

config = configparser.ConfigParser()

def write_file():
    if not os.path.exists(objects.configdir):
        os.makedirs(objects.configdir)
    config.write(open(objects.configfile, 'w+'))

rt = NewType('RichText', str)
sys = NewType('System', str)
exc = NewType('Exec', bool)

# Stylesheet
themename = 'dark'
stylesheet = qdarktheme.load_stylesheet(themename)
palette = qdarktheme.load_palette()

# Naming Style
namingstyle = u"By UUID"

# Config Colors
SocketColor = ThemedColor(QColor(255, 87, 51, 255), QColor(255, 255, 255, 255))
NodeBackground = ThemedColor(QColor(211, 211, 211, 255) , QColor(9, 12, 9, 255))
OperationHeader = QColor(139, 140, 139, 255)
FunctionHeader = QColor(55, 95, 119, 255)
ExecColor = QColor(255, 255, 255, 255)
HeaderTextColor = QColor(255, 255, 255, 255)

CanvasColor = QColor(33, 33, 33, 255)
GridColor = ThemedColor(QColor(211, 211, 211, 255) , QColor(47, 47, 47, 255))

SelectColor = QColor(255, 223, 100, 255)

varcolors = {
    typing.Any : QColor(226, 105, 4, 255),
    exc : QColor(255, 255, 255, 255),
    bool : QColor(142, 0, 0, 255),
    bytes : QColor(1, 99, 90, 255),
    int : QColor(28, 195, 151, 255),
    float : QColor(151, 242, 65, 255),
    str : QColor(215, 3, 179, 255),
    rt : QColor(217, 116, 159, 255),
    sys : QColor(22, 99, 132, 255)
}


# Runtime Editable
winx = 200
winy = 150

globalSettingsSizeX = 300
globalSettingsSizeY = 200

copypreference = 'None'

def loadSettings():
    global winx, winy, themename, namingstyle, stylesheet, globalSettingsSizeX, globalSettingsSizeY, copypreference

    utilities.log('configuration.loadSettings', "Loading Settings...")

    if not os.path.exists(objects.configfile):
        utilities.log('configuration.loadSettings', "No settings file found, writing...")
        config['DEFAULT'] = getDefaults()
        write_file()
    config.read(objects.configfile)

    winx = int(config['DEFAULT']['winx'])
    winy = int(config['DEFAULT']['winy'])
    globalSettingsSizeX = int(config['DEFAULT']['globalSettingsSizeX'])
    globalSettingsSizeY = int(config['DEFAULT']['globalSettingsSizeY'])
    themename = config['DEFAULT']['themename']
    stylesheet = qdarktheme.load_stylesheet(themename)
    namingstyle = config['DEFAULT']['namingstyle']
    copypreference = config['DEFAULT']['copypreference']


def saveSettings():
    if not os.path.exists(objects.configfile):
        config['DEFAULT'] = getDefaults()
    else:
        config['DEFAULT'] = {'winx': winx, 'winy': winy, 'themename' : themename, 'namingstyle' : namingstyle, 'globalSettingsSizeX' : globalSettingsSizeX, 'globalSettingsSizeY' : globalSettingsSizeY, 'copypreference' : copypreference}
    write_file()

def getDefaults() -> dict:
    return {'winx': '200', 'winy': '150', 'themename' : 'dark', 'namingstyle' : 'By UUID', 'globalSettingsSizeX' : '300', 'globalSettingsSizeY' : '200', 'copypreference' : 'None'}