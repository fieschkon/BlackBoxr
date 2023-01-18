from BlackBoxr import utilities
import configuration as configuration
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
            
    def toDict(self):
        return {
            'type' : self.__class__.__name__,
            'light' : (self.lightColor.red(), self.lightColor.green(), self.lightColor.blue()),
            'dark' : (self.darkColor.red(), self.darkColor.green(), self.darkColor.blue())
        }
    
    def fromDict(indict):
        return ThemedColor(QColor(indict['light'][0], indict['light'][1], indict['light'][2]), QColor(indict['dark'][0], indict['dark'][1], indict['dark'][2]))