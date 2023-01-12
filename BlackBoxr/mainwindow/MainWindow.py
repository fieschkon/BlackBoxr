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
from BlackBoxr.graphics.nodes import  DesignNode, NodeBase, RequirementNode, Socket
from BlackBoxr.mainwindow.dashboard.home import Dashboard, SystemRepresenter
from BlackBoxr.mainwindow.widgets import DesignView, DetachableTabWidget, GlobalSettingsDialog, RequirementsView
from BlackBoxr.misc import configuration, objects, Datatypes

class MainWindow(QWidget):
    def __init__(self, parent: Optional[PySide6.QtWidgets.QWidget] = None, flags: PySide6.QtCore.Qt.WindowFlags = None) -> None:
        super().__init__()
        self.resize(int(configuration.winx), int(configuration.winy))
        self.setupUI()
        self.setupMenuBar()

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
        objects.dashboard.requestSystemOpened.connect(self.openNewSysTab)

        testsys = Datatypes.System()
        testDV = RequirementsView(testsys, self)
        self.mainTabbedWidget.addTab(testDV, "Test Canvas")

        # Tree 1
        rl = RequirementNode(Datatypes.RequirementElement.random(testsys))
        testDV.Scene.addItem(rl)
        testDV.Viewer.centerOn(rl)
        rl.setPos(300, 400)

        rl2 = RequirementNode(Datatypes.RequirementElement.random(testsys))
        testDV.Scene.addItem(rl2)
        rl2.setPos(700, 400)

        rl3 = RequirementNode(Datatypes.RequirementElement.random(testsys))
        testDV.Scene.addItem(rl3)
        rl3.setPos(1000, 400)

        rl4 = RequirementNode(Datatypes.RequirementElement.random(testsys))
        testDV.Scene.addItem(rl4)
        rl4.setPos(1000, 400)

        rl.connectDownstream(rl2)
        rl2.connectDownstream(rl3)
        rl2.connectDownstream(rl4)

        # Tree 2

        tree2root = RequirementNode(Datatypes.RequirementElement.random(testsys))
        testDV.Scene.addItem(tree2root)
        testDV.Viewer.centerOn(tree2root)
        tree2root.setPos(300, 400)
        tree2root.connectDownstream(rl4)

        #testDV.repopulateTree()



        self.setWindowTitle(objects.qapp.applicationName())
        self.label.setText(u"Ico")
        self.label_2.setText(objects.qapp.applicationName())
        self.pushButton.setText(u"Settings")

        self.pushButton.clicked.connect(lambda : GlobalSettingsDialog().exec_())

    def openNewSysTab(self, sys):
        self.mainTabbedWidget.addTab(QWidget(), sys.name)

    def closeEvent(self, event: PySide6.QtGui.QCloseEvent) -> None:
        size = self.size().toTuple()
        configuration.winx = size[0]
        configuration.winy = size[1]
        return super().closeEvent(event)

    def setupMenuBar(self):
        
        def createImportExportActions():
            curwid = self.mainTabbedWidget.currentWidget()
            for exporter in objects.plugins['Exporter']:
                action : QAction = self.exporterMenu.addAction(exporter.info().get('name', 'Unnamed Exporter'))
                action.setData(exporter)
                action.triggered.connect(lambda : action.data().run())
            for importer in objects.plugins['Importer']:
                action : QAction = self.importMenu.addAction(importer.info().get('name', 'Unnamed Exporter'))
                action.setData(importer)
                action.triggered.connect(lambda : action.data().run())

        def export():
            curwid = self.mainTabbedWidget.currentWidget()
            if isinstance(curwid, RequirementsView):
                objects.plugins['Exporter'][0].run(insys = curwid.source)

        def updateDashboard():
            self.mainTabbedWidget.removeTabByName("Dashboard")
            objects.dashboard = Dashboard()
            self.mainTabbedWidget.addTab(objects.dashboard, "Dashboard")

        self.menuBar = QMenuBar(None)
        self.verticalLayout.setMenuBar(self.menuBar)
        viewMenu = self.menuBar.addMenu("View")
        dashboardView = viewMenu.addAction("View Dashboard")
        dashboardView.triggered.connect(lambda : updateDashboard())
        pluginManager = viewMenu.addAction("Plugin Manager")
        pluginManager.triggered.connect(lambda : updateDashboard())

        editMenu = self.menuBar.addMenu("Edit")
        undo = editMenu.addAction("Undo")
        undo.triggered.connect(lambda : objects.undoStack.undo())
        redo = editMenu.addAction("Redo")
        redo.triggered.connect(lambda : objects.undoStack.redo())

        self.importMenu = self.menuBar.addMenu("Import")

        self.exporterMenu = self.menuBar.addMenu("Export")
        createImportExportActions()

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

