import datetime
import os
import sys
from PySide6.QtCore import *
from PySide6.QtWidgets import *
import pkg_resources
import qdarktheme
import configparser

import BlackBoxr
from BlackBoxr.Application import objects
from BlackBoxr.Application.Panels.Window import MainWindow
from BlackBoxr.Application import configuration



def run(args):
    """Initialize everything and run the application."""
    '''if args.temp_basedir:
        args.basedir = tempfile.mkdtemp(prefix='qutebrowser-basedir-')'''

    #log.init.debug("Main process PID: {}".format(os.getpid()))

    #log.init.debug("Initializing directories...")
    #standarddir.init(args)
    #resources.preload()

    #log.init.debug("Initializing config...")
    #configinit.early_init(args)

    #log.init.debug("Initializing application...")

    configuration.loadSettings()

    objects.qapp = Application(args)

    res = objects.qapp.primaryScreen().availableSize().toTuple()
    # protect against window starting off screen
    configuration.winx = min(configuration.winx, res[0])
    configuration.winy = min(configuration.winy, res[1])

    objects.qapp.setOrganizationName(objects.Org)
    objects.qapp.setApplicationName(objects.AppName)
    
    objects.qapp.setApplicationVersion(BlackBoxr.__version__)

    w = MainWindow()
    w.show()
    ret =  objects.qapp.exec()
    return ret

def shutdown(args):
    configuration.saveSettings()


class Application(QApplication):

    def __init__(self, args):
        self._last_focus_object = None

        super().__init__(args)

        #log.init.debug("Initializing application...")

        self.launch_time = datetime.datetime.now()
        self.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

        self.setStyleSheet(configuration.stylesheet)
        

    def event(self, e):
        """TODO: Handle macOS FileOpen events."""
        if e.type() != QEvent.FileOpen:
            return super().event(e)

        url = e.url()
        if url.isValid():
            pass
        else:
            pass

        return True
