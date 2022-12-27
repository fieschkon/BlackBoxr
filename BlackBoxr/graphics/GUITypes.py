from BlackBoxr import utilities
import BlackBoxr.misc.configuration as configuration
from PySide6.QtGui import QColor

class ThemedColor():

    DEFAULTCOLOR = QColor(255, 0, 0, 255)

    def __init__(self, lightColor : QColor = None, darkColor: QColor = None) -> None:
        self.lightColor = lightColor
        self.darkColor = darkColor

    def color(self, themename = None):
        if themename == None:
            themename = configuration.themename
        match themename:
            case 'dark':
                return self.darkColor
            case 'light':
                return self.lightColor
            case 'auto':
                return self.color(utilities.getTheme())
            
