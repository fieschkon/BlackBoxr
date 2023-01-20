from datetime import datetime
import logging
from logging.handlers import RotatingFileHandler
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

def handle_exception(exc_type, exc_value, exc_traceback):
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return

    logging.getLogger().critical("Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback))

sys.excepthook = handle_exception

def run(args):
    """Initialize everything and run the application."""
    root = logging.getLogger()
    root.setLevel(logging.DEBUG)

    stformat = '%(asctime)s %(levelname)s %(module)s.%(funcName)s(%(lineno)d) %(message)s'
    logformat = logging.Formatter(stformat)
    
    FileLogHandler = RotatingFileHandler(os.path.join(objects.logdir, f'{datetime.now().strftime("%H-%M-%S")}.log'), mode='a', maxBytes=5*1024*1024, 
                                    backupCount=2, encoding=None, delay=0)

    FileLogHandler.setFormatter(logformat)
    FileLogHandler.setLevel(logging.INFO)
    root.addHandler(FileLogHandler)

    ConsoleHandler = logging.StreamHandler(sys.stdout)
    ConsoleHandler.setLevel(logging.DEBUG)
    ConsoleHandler.setFormatter(logformat)
    root.addHandler(ConsoleHandler)
    
    logging.debug("Main process PID: {}".format(os.getpid()))
    objects.qapp = Application(args)

    objects.qapp.setOrganizationName(objects.Org)
    objects.qapp.setApplicationName(objects.AppName)
    
    objects.qapp.setApplicationVersion(BlackBoxr.__version__)

    launcher = StartupLauncher()
    launcher.show()
    launcher.startupOperations()

    #res = objects.qapp.primaryScreen().availableSize().toTuple()
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
