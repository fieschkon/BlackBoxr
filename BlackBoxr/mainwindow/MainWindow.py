import os
import random
from typing import Optional
import typing
from PySide6 import QtCore, QtGui
import PySide6
from PySide6.QtWidgets import (
    QMainWindow, QFileDialog, QTreeView,
    QDockWidget, QFileDialog, QTreeWidget,
    QGraphicsScene, QGraphicsView, QHBoxLayout, QPushButton, QSizePolicy, QMenuBar, QStatusBar, QFrame,
    QTabWidget, QWidget, QVBoxLayout, QAbstractItemView, QGraphicsItem, QLabel, QSpacerItem, QTreeWidgetItem, QMenu
)
from PySide6.QtCore import QModelIndex, QRect, QSize, Qt
from PySide6.QtGui import QAction, QPen, QColor, QPainter, QKeySequence, QUndoStack, QFont
from pip import main
import BlackBoxr
from BlackBoxr.graphics.viewer import DiagramScene, DiagramViewer
from BlackBoxr.graphics.nodes import  DesignNode, NodeBase, RequirementNode, Socket
from BlackBoxr.mainwindow.dashboard.home import Dashboard, SystemRepresenter
from BlackBoxr.mainwindow.widgets import DesignView, DetachableTabWidget, GlobalSettingsDialog
from BlackBoxr.misc import configuration, objects, Datatypes

class MainWindow(QWidget):
    def __init__(self, parent: Optional[PySide6.QtWidgets.QWidget] = None, flags: PySide6.QtCore.Qt.WindowFlags = None) -> None:
        super().__init__()
        self.setupMenuBar()
        self.resize(int(configuration.winx), int(configuration.winy))
        self.setupUI()

    def setupUI(self):
        self.verticalLayout = QVBoxLayout()
        self.setLayout(self.verticalLayout)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.widget = QWidget(self)
        self.widget.setObjectName(u"widget")
        self.widget.setMaximumSize(QSize(16777215, 30))
        self.verticalLayout_2 = QVBoxLayout(self.widget)
        self.verticalLayout_2.setSpacing(0)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.verticalLayout_2.setContentsMargins(0, 0, 0, 0)
        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.label = QLabel(self.widget)
        self.label.setObjectName(u"label")
        sizePolicy = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.label.sizePolicy().hasHeightForWidth())
        self.label.setSizePolicy(sizePolicy)
        self.label.setMaximumSize(QSize(64, 64))

        self.horizontalLayout.addWidget(self.label)

        self.label_2 = QLabel(self.widget)
        self.label_2.setObjectName(u"label_2")
        font = QFont()
        font.setFamilies([u"Arial"])
        font.setPointSize(16)
        font.setBold(True)
        self.label_2.setFont(font)

        self.horizontalLayout.addWidget(self.label_2)

        self.horizontalSpacer_2 = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout.addItem(self.horizontalSpacer_2)

        self.pushButton = QPushButton(self.widget)
        self.pushButton.setObjectName(u"pushButton")

        self.horizontalLayout.addWidget(self.pushButton)


        self.verticalLayout_2.addLayout(self.horizontalLayout)


        self.verticalLayout.addWidget(self.widget)

        self.line = QFrame(self)
        self.line.setObjectName(u"line")
        self.line.setFrameShape(QFrame.HLine)
        self.line.setFrameShadow(QFrame.Sunken)

        self.verticalLayout.addWidget(self.line)

        self.ContentArea = QWidget(self)
        self.ContentArea.setObjectName(u"ContentArea")
        self.verticalLayout.addWidget(self.ContentArea)

        self.contentlayout = QVBoxLayout()
        self.ContentArea.setLayout(self.contentlayout)
        self.mainTabbedWidget = DetachableTabWidget(self.ContentArea)
        self.contentlayout.addWidget(self.mainTabbedWidget)

        objects.dashboard = Dashboard()
        self.mainTabbedWidget.addTab(objects.dashboard, "Dashboard")

        testsys = Datatypes.System()
        testDV = DesignView(None, self)
        self.mainTabbedWidget.addTab(testDV, "Test Canvas")

        testSys = Datatypes.System()
        rldata = Datatypes.RequirementElement(testSys)
        rldata.public = {
            'name' : 'Boingus',
            'requirement' : 'Skadoosh',
            'Rationale' : 'Skaboingus',
            'Metric' : 'Cum per second'
        }

        rl2data = Datatypes.RequirementElement(testSys)
        rl2data.public = {
            'name' : 'Boingus',
            'requirement' : 'Skadoosh',
            'Rationale' : 'Skaboingus',
            'Metric' : 'Cum per second'
        }

        rl3data = Datatypes.RequirementElement(testSys)
        rl3data.public = {
            'name' : 'Boingus',
            'requirement' : 'Skadoosh',
            'Rationale' : 'Skaboingus',
            'Metric' : 'Cum per second'
        }

        rl = RequirementNode(rldata)
        testDV.Scene.addItem(rl)
        testDV.Viewer.centerOn(rl)
        rl.setPos(300, 400)

        rl2 = RequirementNode(rl2data)
        testDV.Scene.addItem(rl2)
        rl2.setPos(700, 400)

        rl3 = RequirementNode(rl3data)
        testDV.Scene.addItem(rl3)
        rl3.setPos(1000, 400)

        self.setWindowTitle(objects.qapp.applicationName())
        self.label.setText(u"Ico")
        self.label_2.setText(objects.qapp.applicationName())
        self.pushButton.setText(u"Settings")

        self.pushButton.clicked.connect(lambda : GlobalSettingsDialog().exec_())

    def closeEvent(self, event: PySide6.QtGui.QCloseEvent) -> None:
        size = self.size().toTuple()
        configuration.winx = size[0]
        configuration.winy = size[1]
        return super().closeEvent(event)

    def setupMenuBar(self):

        def updateDashboard():
            self.mainTabbedWidget.removeTabByName("Dashboard")
            objects.dashboard = Dashboard()
            self.mainTabbedWidget.addTab(objects.dashboard, "Dashboard")

        self.menuBar = QMenuBar(None)
        fileMenu = self.menuBar.addMenu("View")
        dashboardView = fileMenu.addAction("View Dashboard")
        dashboardView.triggered.connect(lambda : updateDashboard())

        editMenu = self.menuBar.addMenu("Edit")
        undo = editMenu.addAction("Undo")
        undo.triggered.connect(lambda : objects.undoStack.undo())
        redo = editMenu.addAction("Redo")
        redo.triggered.connect(lambda : objects.undoStack.redo())

        undo.setShortcut(QKeySequence(Qt.CTRL | Qt.Key_Z))
        redo.setShortcut(QKeySequence(Qt.CTRL | Qt.Key_Y))

class SysDesign(QTabWidget):
    def __init__(self, parent: Optional[PySide6.QtWidgets.QWidget] = ...) -> None:
        super().__init__(parent)
        self.setLayoutDirection(QtCore.Qt.LeftToRight)
        self.setAutoFillBackground(False)
        self.setTabPosition(QTabWidget.North)
        self.setTabShape(QTabWidget.Rounded)
        self.setUsesScrollButtons(True)
        self.setDocumentMode(False)
        self.setTabsClosable(True)
        self.tabCloseRequested.connect(self.removeTab)


class testScene(QWidget):
    
    def __init__(self) -> None:
        super().__init__()
        self.verticalLayout_2 = QVBoxLayout(self)
        self.scene = DiagramScene()
        self.view = DiagramViewer(self.scene)
        self.scene.set_viewer(self.view)
        self.verticalLayout_2.addWidget(self.view)
        self.setLayout(self.verticalLayout_2)

        size = (120000, 120000)
        self.scene.setSceneRect(0,0,size[0],size[1])

        xoffset = size[0] / 2
        yoffset = size[1] / 2


        self.view.centerOn(xoffset,yoffset)
