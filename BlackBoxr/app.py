from datetime import datetime
import logging
import os
import sys
from PySide6.QtCore import *
from PySide6.QtWidgets import *
import pkg_resources
import qdarktheme
import configparser

import BlackBoxr
from BlackBoxr.Application import objects
from BlackBoxr.Application.Launcher import StartupLauncher
from BlackBoxr.Application.Panels.Window import MainWindow
from BlackBoxr.Application import configuration
from BlackBoxr.Application.Configuration2 import Settings



def run(args):
    """Initialize everything and run the application."""
    '''if args.temp_basedir:
        args.basedir = tempfile.mkdtemp(prefix='qutebrowser-basedir-')'''
    logformat = '%(asctime)s :: %(levelname)s :: %(module)s.%(funcName)s :: %(message)s'
    logging.basicConfig(level=logging.DEBUG, format=logformat, filename=os.path.join(objects.logdir, f'{datetime.now().strftime("%H-%M-%S")}.log'))
    root = logging.getLogger()
    root.setLevel(logging.DEBUG)

    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter(logformat)
    handler.setFormatter(formatter)
    root.addHandler(handler)
    

    #log.init.debug("Main process PID: {}".format(os.getpid()))

    #log.init.debug("Initializing directories...")
    #standarddir.init(args)
    #resources.preload()

    #log.init.debug("Initializing config...")
    #configinit.early_init(args)

    #log.init.debug("Initializing application...")

    #configuration.loadSettings()

    objects.qapp = Application(args)

    objects.qapp.setOrganizationName(objects.Org)
    objects.qapp.setApplicationName(objects.AppName)
    
    objects.qapp.setApplicationVersion(BlackBoxr.__version__)

    launcher = StartupLauncher()
    launcher.show()
    launcher.startupOperations()


    res = objects.qapp.primaryScreen().availableSize().toTuple()
    #Settings.winx = min(configuration.winx, res[0])
    #Settings.winy = min(configuration.winy, res[1])


    w = MainWindow()
    w.show()

    ret =  objects.qapp.exec()
    return ret

def shutdown(args):
    Settings.saveToFile()
    #configuration.saveSettings()


class Application(QApplication):

    def __init__(self, args):
        self._last_focus_object = None

        super().__init__(args)

        #log.init.debug("Initializing application...")

        self.launch_time = datetime.now()
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
