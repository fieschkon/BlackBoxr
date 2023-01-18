from typing import Optional
from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QBrush, QColor, QConicalGradient, QCursor,
    QFont, QFontDatabase, QGradient, QIcon,
    QImage, QKeySequence, QLinearGradient, QPainter,
    QPalette, QPixmap, QRadialGradient, QTransform)
from PySide6.QtWidgets import (QApplication, QHBoxLayout, QLabel, QMainWindow,
    QProgressBar, QSizePolicy, QVBoxLayout, QWidget)
from BlackBoxr.Application.Panels.Window import MainWindow

from BlackBoxr.modules.ExtensionLoader import ExtensionLoader
from BBData.Delegate import Delegate

class StartupLauncher(QMainWindow):

    

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setAttribute( Qt.WA_DeleteOnClose, True )
        self.operationsFinished = Delegate()
        self.currentstep = 0
        self.setupUi()
        
    def finished(self):
        self.operationsFinished.emit()
        self.close()

    def setupUi(self):
        self.resize(578, 206)
        self.centralwidget = QWidget(self)
        self.centralwidget.setObjectName(u"centralwidget")
        self.verticalLayout = QVBoxLayout(self.centralwidget)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.TitleLabel = QLabel(self.centralwidget)
        self.TitleLabel.setObjectName(u"TitleLabel")
        font = QFont()
        font.setFamilies([u"Arial"])
        font.setPointSize(48)
        font.setBold(True)
        self.TitleLabel.setFont(font)

        self.horizontalLayout.addWidget(self.TitleLabel)

        self.ImageBox = QLabel(self.centralwidget)
        self.ImageBox.setObjectName(u"ImageBox")
        self.ImageBox.setMaximumSize(QSize(150, 150))

        self.horizontalLayout.addWidget(self.ImageBox)


        self.verticalLayout.addLayout(self.horizontalLayout)

        self.ProgressBar = QProgressBar(self.centralwidget)
        self.ProgressBar.setObjectName(u"ProgressBar")
        self.ProgressBar.setMaximumSize(QSize(16777215, 10))
        self.ProgressBar.setValue(24)
        self.ProgressBar.setTextVisible(False)
        self.ProgressBar.setOrientation(Qt.Horizontal)
        self.ProgressBar.setInvertedAppearance(False)

        self.verticalLayout.addWidget(self.ProgressBar)

        self.setCentralWidget(self.centralwidget)
        self.TitleLabel.setText("BlackBoxr")
        self.ImageBox.setText("")
        self.setWindowFlags(Qt.FramelessWindowHint)
        #self.setAttribute(Qt.WA_TranslucentBackground)
        #self.setStyleSheet("background:transparent;")

    def startupOperations(self):
        # Collect Maximum Steps
        steps = len(ExtensionLoader.DiscoverExtensions())

        self.ProgressBar.setMaximum(steps)

        self.InitExtensionLoader()

        # Done
        self.ProgressBar.setValue(self.ProgressBar.maximum())
        self.finished()

        

    def InitExtensionLoader(self):
        def extensionLoaderProgress(args):
            self.currentstep += 1
            self.ProgressBar.setValue(self.currentstep)
        ExtensionLoader.onBuildProgress.connect(extensionLoaderProgress)
        ExtensionLoader.buildPlugins()

    def loadSettings(self):
        pass