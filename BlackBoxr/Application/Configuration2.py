import inspect
import json
import logging
import os
import qdarktheme
from BlackBoxr.Application.Canvas.GUITypes import ThemedColor
from BlackBoxr.Application import objects

from BlackBoxr.Application.Serializer import json_decode, json_encode
from PySide6.QtGui import QColor

class Settings:
    # Runtime Editable
    winx = 200
    winy = 150

    globalSettingsSizeX = 300
    globalSettingsSizeY = 200

    copypreference = 'None'

    # Theming
    themename = 'dark'

    # Config Colors
    SocketColor = ThemedColor(QColor(255, 87, 51, 255), QColor(255, 255, 255, 255))
    NodeBackground = ThemedColor(QColor(211, 211, 211, 255) , QColor(9, 12, 9, 255))
    OperationHeader = QColor(139, 140, 139, 255)
    FunctionHeader = QColor(55, 95, 119, 255)
    ExecColor = QColor(255, 255, 255, 255)
    HeaderTextColor = QColor(255, 255, 255, 255)

    CanvasColor = QColor(33, 33, 33, 255)
    GridColor = ThemedColor(QColor(211, 211, 211, 255) , QColor(47, 47, 47, 255))

    NodeZoomedColor = ThemedColor(QColor(47, 47, 47, 255), QColor(211, 211, 211, 255))

    SelectColor = QColor(255, 223, 100, 255)

    def serializeSettings():
        attributes = inspect.getmembers(Settings, lambda a:not(inspect.isroutine(a)))
        serializedDict = {a[0] : a[1] for a in attributes if not(a[0].startswith('__') and a[0].endswith('__'))}
        return json_encode(serializedDict)

    def loadSettings(indict : dict):
        for key, value in indict.items():
            try:
                setattr(Settings, key, json_decode(value))
            except:
                if isinstance(value, dict):
                    if value['type'] == ThemedColor.__class__.__name__:
                        value = ThemedColor.fromDict(value)
                    elif value['type'] == QColor.__class__.__name__:
                        value = QColor(value['color'][0], value['color'][1], value['color'][2])

                setattr(Settings, key, value)

    def saveToFile(path=objects.configfile):
        if not os.path.exists(objects.configdir):
            os.makedirs(objects.configdir)
        with open(path, 'w') as f:
            f.write(Settings.serializeSettings())

    def openFromFile(path=objects.configfile):
        Settings.loadSettings(dict(json.loads(open(path, 'r').read())))