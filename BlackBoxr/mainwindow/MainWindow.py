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
from BlackBoxr.mainwindow.Graphics import DiagramScene, DiagramViewer, NodeBase, Socket
from BlackBoxr.mainwindow.dashboard.home import Dashboard, SystemRepresenter
from BlackBoxr.mainwindow.widgets import DetachableTabWidget, GlobalSettingsDialog
from BlackBoxr.misc import configuration, objects, Datatypes

class MainWindow_LEGACY(QMainWindow):
    '''Main window for the application'''
    def __init__(self, parent: Optional[PySide6.QtWidgets.QWidget] = None, flags: PySide6.QtCore.Qt.WindowFlags = None) -> None:
        super().__init__()
        self.setWindowTitle("BlackBoxr")
        self.centralwidget = QWidget(self)
        self.centralwidget.setObjectName(u"centralwidget")
        self.verticalLayout_2 = QVBoxLayout(self.centralwidget)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalLayout_3 = QHBoxLayout()
        self.horizontalLayout_3.setObjectName(u"horizontalLayout_3")
        self.LogoLBL = QLabel(self.centralwidget)
        self.LogoLBL.setObjectName(u"label")

        self.bozo = SystemRepresenter(self.centralwidget)
        self.horizontalLayout_3.addWidget(self.bozo)

        self.horizontalLayout_3.addWidget(self.LogoLBL)


        self.horizontalLayout.addLayout(self.horizontalLayout_3)

        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum)

        self.horizontalLayout.addItem(self.horizontalSpacer)

        self.horizontalLayout_4 = QHBoxLayout()
        self.horizontalLayout_4.setObjectName(u"horizontalLayout_4")
        self.AuthLBL = QLabel(self.centralwidget)
        self.AuthLBL.setObjectName(u"label_2")

        self.horizontalLayout_4.addWidget(self.AuthLBL)


        self.horizontalLayout.addLayout(self.horizontalLayout_4)


        self.verticalLayout_2.addLayout(self.horizontalLayout)

        self.tabWidget = QTabWidget(self.centralwidget)
        self.tabWidget.setObjectName(u"tabWidget")
        self.tabWidget.setLayoutDirection(QtCore.Qt.LeftToRight)
        self.tabWidget.setAutoFillBackground(False)
        self.tabWidget.setTabPosition(QTabWidget.North)
        self.tabWidget.setTabShape(QTabWidget.Rounded)
        self.tabWidget.setUsesScrollButtons(True)
        self.tabWidget.setDocumentMode(False)
        # Sys Designer
        self.sysdesigner = SysDesign(self.centralwidget)
        self.tabWidget.addTab(self.sysdesigner, "System Design")

        self.tab = testScene()
        self.sysdesigner.addTab(self.tab, "Demo Scene")
        self.tab_2 = QWidget()
        self.tabWidget.addTab(self.tab_2, "Requirements")

        self.verticalLayout_2.addWidget(self.tabWidget)

        self.setCentralWidget(self.centralwidget)
        self.statusbar = QStatusBar(self)
        self.statusbar.setObjectName(u"statusbar")
        self.setStatusBar(self.statusbar)
        self.dockWidget = QDockWidget(self)
        self.dockWidget.setObjectName(u"dockWidget")
        self.dockWidget.setFeatures(QDockWidget.DockWidgetFloatable|QDockWidget.DockWidgetMovable)
        self.dockWidgetContents = QWidget()
        self.dockWidgetContents.setObjectName(u"dockWidgetContents")
        self.verticalLayout = QVBoxLayout(self.dockWidgetContents)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.treeWidget = QTreeWidget(self.dockWidgetContents)
        __qtreewidgetitem = QTreeWidgetItem()
        __qtreewidgetitem.setText(0, u"Object Name")
        self.treeWidget.setHeaderItem(__qtreewidgetitem)
        self.treeWidget.setObjectName(u"treeWidget")

        self.verticalLayout.addWidget(self.treeWidget)

        self.dockWidget.setWidget(self.dockWidgetContents)
        self.addDockWidget(QtCore.Qt.LeftDockWidgetArea, self.dockWidget)

        self.setStatusBar(QStatusBar(self))
        
        menu = self.menuBar()

        canvasActionsMenu = menu.addMenu("&Canvas Actions")
        self.deleteAction = QAction(("Delete Item"), self)
        self.deleteAction.setShortcut(QKeySequence.Delete)
        self.deleteAction.triggered.connect(self.deleteItems)
        self.undoAction = objects.undoStack.createUndoAction(self, ("Undo"))
        self.undoAction.setShortcuts(QKeySequence.Undo)
        self.redoAction = objects.undoStack.createRedoAction(self, ("Redo"))
        self.redoAction.setShortcuts(QKeySequence.Redo)

        canvasActionsMenu.addAction(self.deleteAction)
        canvasActionsMenu.addAction(self.undoAction)
        canvasActionsMenu.addAction(self.redoAction)

    def deleteItems(self):
        if len(self.tab.scene.selectedItems()) == 0:
            return
        objects.undoStack.push(Datatypes.DeleteCommand(self.tab.scene))

class MainWindow(QWidget):
    def __init__(self, parent: Optional[PySide6.QtWidgets.QWidget] = None, flags: PySide6.QtCore.Qt.WindowFlags = None) -> None:
        super().__init__()
        self.setupMenuBar()
        self.resize(int(configuration.winx), int(configuration.winy))
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

        scene = DiagramScene()
        canvasview = DiagramViewer(scene)
        self.mainTabbedWidget.addTab(canvasview, "Test Canvas")
        scene.setSceneRect(0,0,5000,5000)
        self.db = NodeBase()
        scene.addItem(self.db)
        self.db.setPos(100, 100)

        socketA = Socket(self.db)
        socketB = Socket(self.db, vertical=True)
        scene.addItem(socketA)
        scene.addItem(socketB)
        socketA.setPos(200, 100)
        socketB.setPos(250, 100)

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
