
from datetime import datetime
import json
import logging
import math
import os
from types import NoneType
from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect, QFileSystemWatcher,
    QSize, QTime, QUrl, Qt, Signal)
from PySide6.QtGui import (QBrush, QColor, QConicalGradient, QCursor,
    QFont, QFontDatabase, QGradient, QIcon, QResizeEvent,
    QImage, QKeySequence, QLinearGradient, QPainter, QPaintEvent,
    QPalette, QPixmap, QRadialGradient, QTransform)
from PySide6.QtWidgets import (QApplication, QHBoxLayout, QLabel, QLayout, QGridLayout, QListWidget, QListWidgetItem, QListView,
    QPushButton, QSizePolicy, QSpacerItem, QVBoxLayout, QLineEdit,
    QWidget, QTextEdit)
from BlackBoxr import utilities
from BlackBoxr.Application import configuration, objects
from BlackBoxr.Application.Panels.Widgets import EditableLabel
from BlackBoxr.misc import Datatypes
from BlackBoxr.misc.Datatypes import System
from BlackBoxr.utilities import getDuration, searchFilesForUUID

class SystemRepresenter(QWidget):
    def __init__(self, insys : System = None):
        super().__init__()
        self.initUI()

        if isinstance(insys, NoneType):
            insys = System()

        self.represented = insys

        timesince = getDuration(datetime.strptime(insys.updateDate, "%m/%d/%y %H:%M:%S"))

        updatedlabeltext = ""

        updatedlabeltext = "{} seconds ago".format(timesince['seconds']) if timesince['seconds'] > 0 else updatedlabeltext
        updatedlabeltext = "{} minutes ago".format(timesince['minutes']) if timesince['minutes'] > 1 else updatedlabeltext
        updatedlabeltext = "{} hours ago".format(timesince['hours']) if timesince['hours'] > 1 else updatedlabeltext
        updatedlabeltext = "{} days ago".format(timesince['days']) if timesince['days'] > 0 else updatedlabeltext


        self.TypeLabel.setText(u"System")
        self.OptionsButton.setText(u"\u00b7\u00b7\u00b7")
        self.SystemNameLabel.setText(insys.name)
        self.LastEditedIcon.setText(u"ico")
        self.LastEditedLabel.setText(updatedlabeltext)


    def initUI(self):
        self.verticalLayout = QVBoxLayout(self)
        self.widget_3 = QWidget(self)
        self.verticalLayout_2 = QVBoxLayout(self.widget_3)
        self.verticalLayout_2.setContentsMargins(5, 5, 5, 5)
        self.widget = QWidget(self.widget_3)
        sizePolicy = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Fixed)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.widget.sizePolicy().hasHeightForWidth())
        self.widget.setSizePolicy(sizePolicy)
        self.horizontalLayout = QHBoxLayout(self.widget)
        self.horizontalLayout.setSpacing(10)
        self.horizontalLayout.setContentsMargins(0, 0, 0, 0)
        self.TypeWidget = QWidget(self.widget)
        self.TypeWidget.setMaximumSize(QSize(200, 16777215))
        self.verticalLayout_3 = QVBoxLayout(self.TypeWidget)
        self.verticalLayout_3.setSpacing(0)
        self.verticalLayout_3.setContentsMargins(0, 0, 0, 0)
        self.TypeLabel = QLabel(self.TypeWidget)
        sizePolicy1 = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        sizePolicy1.setHorizontalStretch(0)
        sizePolicy1.setVerticalStretch(0)
        sizePolicy1.setHeightForWidth(self.TypeLabel.sizePolicy().hasHeightForWidth())
        self.TypeLabel.setSizePolicy(sizePolicy1)
        self.TypeLabel.setMinimumSize(QSize(150, 0))
        self.TypeLabel.setMaximumSize(QSize(400, 16777215))
        font = QFont()
        font.setFamilies([u"Arial"])
        self.TypeLabel.setFont(font)

        self.verticalLayout_3.addWidget(self.TypeLabel)


        self.horizontalLayout.addWidget(self.TypeWidget)

        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout.addItem(self.horizontalSpacer)

        self.OptionsButton = QPushButton(self.widget)
        sizePolicy2 = QSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        sizePolicy2.setHorizontalStretch(0)
        sizePolicy2.setVerticalStretch(0)
        sizePolicy2.setHeightForWidth(self.OptionsButton.sizePolicy().hasHeightForWidth())
        self.OptionsButton.setSizePolicy(sizePolicy2)
        self.OptionsButton.setMinimumSize(QSize(32, 32))
        self.OptionsButton.setMaximumSize(QSize(32, 32))

        self.horizontalLayout.addWidget(self.OptionsButton)


        self.verticalLayout_2.addWidget(self.widget)

        self.SystemNameLabel = EditableLabel(self.widget_3)
        self.SystemNameLabel.textChanged.connect(self.renameEvent)
        font1 = QFont()
        font1.setFamilies([u"Arial"])
        font1.setPointSize(14)
        self.SystemNameLabel.setFont(font1)
        #self.SystemNameLabel.setAlignment(Qt.AlignCenter)

        self.verticalLayout_2.addWidget(self.SystemNameLabel)

        self.widget_2 = QWidget(self.widget_3)
        sizePolicy.setHeightForWidth(self.widget_2.sizePolicy().hasHeightForWidth())
        self.widget_2.setSizePolicy(sizePolicy)
        self.horizontalLayout_2 = QHBoxLayout(self.widget_2)
        self.horizontalLayout_2.setContentsMargins(5, 5, 5, 5)
        self.LastEditedIcon = QLabel(self.widget_2)
        sizePolicy2.setHeightForWidth(self.LastEditedIcon.sizePolicy().hasHeightForWidth())
        self.LastEditedIcon.setSizePolicy(sizePolicy2)
        self.LastEditedIcon.setMinimumSize(QSize(32, 32))
        self.LastEditedIcon.setMaximumSize(QSize(32, 32))

        self.horizontalLayout_2.addWidget(self.LastEditedIcon)

        self.LastEditedLabel = QLabel(self.widget_2)
        self.LastEditedLabel.setFont(font)

        self.horizontalLayout_2.addWidget(self.LastEditedLabel)


        self.verticalLayout_2.addWidget(self.widget_2)


        self.verticalLayout.addWidget(self.widget_3)


        self.TypeLabel.setText(u"TextLabel")
        self.OptionsButton.setText(u"\u00b7\u00b7\u00b7")
        self.SystemNameLabel.setText(u"TextLabel")
        self.LastEditedIcon.setText(u"TextLabel")
        self.LastEditedLabel.setText(u"x days ago")

    def renameEvent(self, text):
        self.represented.setName(text)
        file = searchFilesForUUID(objects.getFilesInDataPaths(), str(self.represented.uuid))
        if file != False:
            sys = System.loadFromFile(file)
            sys.setName(text)
            logging.info(f'Saved system to {sys.save(file)}')
            del sys
        else:
            self.represented.save()

    def paintEvent(self, event: QPaintEvent) -> None:
        pass
        '''if not self.paintingActive():
            painter = QPainter(self)
            painter.setBrush(configuration.palette.color(configuration.palette.AlternateBase))
            painter.drawRoundedRect(self.rect().adjusted(0,0,-1,-1), 15, 15)'''


class Dashboard(QWidget):

    requestSystemOpened = Signal(System)

    def __init__(self, parent = None) -> None:
        super().__init__(parent)
        self.setupUI(parent)
        self.systemReppers = []
        self.discoverSystems()

        self.observer = QFileSystemWatcher(self)
        for path in objects.searchdirs:
            self.observer.addPath(path)
        self.observer.fileChanged.connect(lambda : self.repopulateSystems())
        self.observer.directoryChanged.connect(lambda : self.repopulateSystems())

    def repopulateSystems(self):
        self.systemReppers.clear()
        self.gridlist.clear()

        self.discoverSystems()

    def discoverSystems(self):
        
        files =[]
        systems = []
        for dir in objects.searchdirs:
            dir = os.path.normpath(dir)
            files += [os.path.join(dir, pos_json) for pos_json in os.listdir(dir) if pos_json.endswith('.json')]
        for file in files:
            try:
                systems.append(System.getDummySystemFromFile(file))
                systems.sort(key=lambda x: x.deltaSinceUpdate(), reverse=False)
            except:
                pass
        for system in systems:
            self.addWidget(SystemRepresenter(system))
        

    def setupUI(self, parent):
        self.setSizePolicy(QSizePolicy(QSizePolicy.Preferred, QSizePolicy.MinimumExpanding))
        self.verticalLayout = QVBoxLayout(self)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.widget = QWidget(self)
        self.widget.setObjectName(u"widget")
        self.widget.setMaximumSize(QSize(16777215, 60))
        self.horizontalLayout = QHBoxLayout(self.widget)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.label = QLabel(self.widget)
        self.label.setObjectName(u"label")
        font = QFont()
        font.setFamilies([u"Arial"])
        font.setPointSize(14)
        font.setBold(True)
        self.label.setFont(font)

        self.horizontalLayout.addWidget(self.label)

        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout.addItem(self.horizontalSpacer)

        self.lineEdit = QLineEdit(self.widget)
        self.lineEdit.setObjectName(u"lineEdit")
        self.lineEdit.setMinimumSize(QSize(200, 0))
        self.lineEdit.setMaximumSize(QSize(600, 16777215))
        self.lineEdit.setFrame(True)
        self.lineEdit.setClearButtonEnabled(False)

        self.horizontalLayout.addWidget(self.lineEdit)

        self.pushButton = QPushButton(self.widget)
        self.pushButton.setObjectName(u"pushButton")

        self.horizontalLayout.addWidget(self.pushButton)

        self.verticalLayout.addWidget(self.widget)

        self.gridlist = QListWidget(self)
        self.verticalLayout.addWidget(self.gridlist)
        self.gridlist.setFlow(QListView.LeftToRight)
        self.gridlist.setProperty("isWrapping", True)
        self.gridlist.setResizeMode(QListView.Adjust)
        self.gridlist.setUniformItemSizes(True)
        self.gridlist.setSpacing(5)

        self.verticalLayout.setAlignment(Qt.AlignTop)

        self.label.setText(u"Dashboard")
        self.lineEdit.setInputMask("")
        self.lineEdit.setPlaceholderText(u"Filter")
        self.pushButton.setText(u"Create")

        self.pushButton.clicked.connect(lambda: self.addWidget(SystemRepresenter()))
        self.gridlist.itemDoubleClicked.connect(self.systemOpened)

    def systemOpened(self, sysrepper : QListWidgetItem):
        sysrepper = self.gridlist.itemWidget(sysrepper)
        
        file = utilities.searchFilesForUUID(utilities.getFilesWithExtension(objects.searchdirs), str(sysrepper.represented.uuid))
        if file != False:
            sys = System.loadFromFile(file)
            if sys in objects.systems:
                objects.systems.remove(sys)
            logging.info(f"Opened {sys.uuid}")
            objects.systems.append(sys)
            self.requestSystemOpened.emit(sys)
            
        else:
            logging.error(f"ERROR: Could not open system with uuid {str(sysrepper.represented.uuid)}")
        


    def addWidget(self, widget : QWidget):
        self.systemReppers.append(widget)
        itemProxy = QListWidgetItem()
        itemProxy.setSizeHint(QSize(200, 200))
        self.gridlist.addItem(itemProxy)
        self.gridlist.setItemWidget(itemProxy, widget)

    def resizeEvent(self, event: QResizeEvent) -> None:
        self.gridlist.resizeEvent(event)
        return super().resizeEvent(event)
            