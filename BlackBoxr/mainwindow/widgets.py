import copy
from typing import Optional
from PySide6.QtWidgets import (
    QLabel, QWidget,QTextEdit, QLineEdit, QDialog, QVBoxLayout, QScrollArea, QGridLayout, QComboBox, QDialogButtonBox, QSpacerItem, QSizePolicy, QHBoxLayout, QTreeWidget, QTreeWidgetItem, QAbstractItemView
)
from PySide6.QtGui import QFont, QFontMetrics, QTextCursor, QPainter, QPen, QPainterPath, QRegion
from PySide6.QtCore import Signal, Slot, QRect, QSize, Qt
from PySide6 import QtCore, QtGui, QtWidgets
from BlackBoxr import utilities
from BlackBoxr.graphics.viewer import DiagramScene, DiagramViewer

from BlackBoxr.misc import configuration, objects
from PySide6.QtCharts import QChart, QChartView, QPieSeries
import qdarktheme

from BlackBoxr.misc.Datatypes import DesignElement, Element, System

bold = QFont("Verdana", 16)
bold.setBold(True)
boldMetrics = QFontMetrics(bold)

class DetachableTabWidget(QtWidgets.QTabWidget):
    def __init__(self, parent=None):

        super().__init__()

        self.tabBar = self.TabBar(self)
        self.tabBar.onDetachTabSignal.connect(self.detachTab)
        self.tabBar.onMoveTabSignal.connect(self.moveTab)
        self.tabBar.detachedTabDropSignal.connect(self.detachedTabDrop)

        self.setTabBar(self.tabBar)

        # Used to keep a reference to detached tabs since their QMainWindow
        # does not have a parent
        self.detachedTabs = {}

        # Close all detached tabs if the application is closed explicitly
        QtCore.QCoreApplication.instance().aboutToQuit.connect(self.closeDetachedTabs)

        self.setTabsClosable(True)
        self.tabCloseRequested.connect(lambda index: self.removeTab(index))

    ##
    #  The default movable functionality of QTabWidget must remain disabled
    #  so as not to conflict with the added features
    def setMovable(self, movable):
        pass

    ##
    #  Move a tab from one position (index) to another
    #
    #  @param    fromIndex    the original index location of the tab
    #  @param    toIndex      the new index location of the tab
    @Slot(int, int)
    def moveTab(self, fromIndex, toIndex):
        widget = self.widget(fromIndex)
        icon = self.tabIcon(fromIndex)
        text = self.tabText(fromIndex)

        self.removeTab(fromIndex)
        self.insertTab(toIndex, widget, icon, text)
        self.setCurrentIndex(toIndex)

    ##
    #  Detach the tab by removing it's contents and placing them in
    #  a DetachedTab window
    #
    #  @param    index    the index location of the tab to be detached
    #  @param    point    the screen position for creating the new DetachedTab window
    @Slot(int, QtCore.QPoint)
    def detachTab(self, index, point):

        # Get the tab content
        name = self.tabText(index)
        icon = self.tabIcon(index)
        if icon.isNull():
            icon = self.window().windowIcon()
        contentWidget = self.widget(index)

        try:
            contentWidgetRect = contentWidget.frameGeometry()
        except AttributeError:
            return

        # Create a new detached tab window
        detachedTab = self.DetachedTab(name, contentWidget, index)
        detachedTab.setWindowModality(QtCore.Qt.NonModal)
        detachedTab.setWindowIcon(icon)
        detachedTab.setGeometry(contentWidgetRect)
        detachedTab.onCloseSignal.connect(self.attachTab)
        detachedTab.onDropSignal.connect(self.tabBar.detachedTabDrop)
        detachedTab.move(point)
        detachedTab.show()

        # Create a reference to maintain access to the detached tab
        self.detachedTabs[name] = detachedTab

    ##
    #  Re-attach the tab by removing the content from the DetachedTab window,
    #  closing it, and placing the content back into the DetachableTabWidget
    #
    #  @param    contentWidget    the content widget from the DetachedTab window
    #  @param    name             the name of the detached tab
    #  @param    icon             the window icon for the detached tab
    #  @param    insertAt         insert the re-attached tab at the given index
    def attachTab(self, contentWidget, name, icon, insertAt=None):

        # Make the content widget a child of this widget
        contentWidget.setParent(self)

        # Remove the reference
        del self.detachedTabs[name]

        # Create an image from the given icon (for comparison)
        if not icon.isNull():
            try:
                tabIconPixmap = icon.pixmap(icon.availableSizes()[0])
                tabIconImage = tabIconPixmap.toImage()
            except IndexError:
                tabIconImage = None
        else:
            tabIconImage = None

        # Create an image of the main window icon (for comparison)
        if not icon.isNull():
            try:
                windowIconPixmap = self.window().windowIcon().pixmap(icon.availableSizes()[0])
                windowIconImage = windowIconPixmap.toImage()
            except IndexError:
                windowIconImage = None
        else:
            windowIconImage = None

        # Determine if the given image and the main window icon are the same.
        # If they are, then do not add the icon to the tab
        if tabIconImage == windowIconImage:
            if insertAt == None:
                index = self.addTab(contentWidget, name)
            else:
                index = self.insertTab(insertAt, contentWidget, name)
        else:
            if insertAt == None:
                index = self.addTab(contentWidget, icon, name)
            else:
                index = self.insertTab(insertAt, contentWidget, icon, name)

        # Make this tab the current tab
        if index > -1:
            self.setCurrentIndex(index)

    ##
    #  Remove the tab with the given name, even if it is detached
    #
    #  @param    name    the name of the tab to be removed
    def removeTabByName(self, name):

        # Remove the tab if it is attached
        attached = False
        for index in range(self.count()):
            if str(name) == str(self.tabText(index)):
                self.removeTab(index)
                attached = True
                break

        # If the tab is not attached, close it's window and
        # remove the reference to it
        if not attached:
            for key in self.detachedTabs:
                if str(name) == str(key):
                    self.detachedTabs[key].onCloseSignal.disconnect()
                    self.detachedTabs[key].close()
                    del self.detachedTabs[key]
                    break

    ##
    #  Handle dropping of a detached tab inside the DetachableTabWidget
    #
    #  @param    name     the name of the detached tab
    #  @param    index    the index of an existing tab (if the tab bar
    #                     determined that the drop occurred on an
    #                     existing tab)
    #  @param    dropPos  the mouse cursor position when the drop occurred
    @Slot(str, int, QtCore.QPoint)
    def detachedTabDrop(self, name, index, dropPos):
        # If the drop occurred on an existing tab, insert the detached
        # tab at the existing tab's location
        if index > -1:

            # Create references to the detached tab's content and icon
            contentWidget = self.detachedTabs[name].contentWidget
            icon = self.detachedTabs[name].windowIcon()

            # Disconnect the detached tab's onCloseSignal so that it
            # does not try to re-attach automatically
            self.detachedTabs[name].onCloseSignal.disconnect()

            # Close the detached
            self.detachedTabs[name].close()

            # Re-attach the tab at the given index
            self.attachTab(contentWidget, name, icon, index)

        # If the drop did not occur on an existing tab, determine if the drop
        # occurred in the tab bar area (the area to the side of the QTabBar)
        else:

            # Find the drop position relative to the DetachableTabWidget
            tabDropPos = self.mapFromGlobal(dropPos)

            # If the drop position is inside the DetachableTabWidget...
            if self.rect().contains(tabDropPos):

                # If the drop position is inside the tab bar area (the
                # area to the side of the QTabBar) or there are not tabs
                # currently attached...
                if tabDropPos.y() < self.tabBar.height() or self.count() == 0:

                    # Close the detached tab and allow it to re-attach
                    # automatically
                    self.detachedTabs[name].close()

    ##
    #  Close all tabs that are currently detached.
    def closeDetachedTabs(self):
        listOfDetachedTabs = []
        for key in self.detachedTabs:
            listOfDetachedTabs.append(self.detachedTabs[key])

        for detachedTab in listOfDetachedTabs:
            detachedTab.close()

    ##
    #  When a tab is detached, the contents are placed into this QMainWindow.  The tab
    #  can be re-attached by closing the dialog or by dragging the window into the tab bar
    class DetachedTab(QtWidgets.QMainWindow):
        onCloseSignal = Signal(QtWidgets.QWidget, str, QtGui.QIcon, int)
        onDropSignal = Signal(str, QtCore.QPoint)

        def __init__(self, name, contentWidget, index):
            QtWidgets.QMainWindow.__init__(self, None)
            self.index = index
            self.setObjectName(name)
            self.setWindowTitle(name)

            self.contentWidget = contentWidget
            self.setCentralWidget(self.contentWidget)
            self.contentWidget.show()

            self.windowDropFilter = self.WindowDropFilter()
            self.installEventFilter(self.windowDropFilter)
            self.windowDropFilter.onDropSignal.connect(self.windowDropSlot)

        ##
        #  Handle a window drop event
        #
        #  @param    dropPos    the mouse cursor position of the drop
        @Slot(QtCore.QPoint)
        def windowDropSlot(self, dropPos):
            self.onDropSignal.emit(self.objectName(), dropPos)

        ##
        #  If the window is closed, emit the onCloseSignal and give the
        #  content widget back to the DetachableTabWidget
        #
        #  @param    event    a close event
        def closeEvent(self, event):
            self.onCloseSignal.emit(
                self.contentWidget, self.objectName(), self.windowIcon(), self.index
            )

        ##
        #  An event filter class to detect a QMainWindow drop event
        class WindowDropFilter(QtCore.QObject):
            onDropSignal = Signal(QtCore.QPoint)

            def __init__(self):
                QtCore.QObject.__init__(self)
                self.lastEvent = None

            ##
            #  Detect a QMainWindow drop event by looking for a NonClientAreaMouseMove (173)
            #  event that immediately follows a Move event
            #
            #  @param    obj    the object that generated the event
            #  @param    event  the current event
            def eventFilter(self, obj, event):
                # If a NonClientAreaMouseMove (173) event immediately follows a Move event...
                if self.lastEvent == QtCore.QEvent.Move and event.type() == 175:
                    # Determine the position of the mouse cursor and emit it with the
                    # onDropSignal
                    mouseCursor = QtGui.QCursor()
                    dropPos = mouseCursor.pos()
                    self.onDropSignal.emit(dropPos)
                    self.lastEvent = event.type()
                    return True

                else:
                    self.lastEvent = event.type()
                    return False

    #  The TabBar class re-implements some of the functionality of the QTabBar widget
    class TabBar(QtWidgets.QTabBar):
        onDetachTabSignal = Signal(int, QtCore.QPoint)
        onMoveTabSignal = Signal(int, int)
        detachedTabDropSignal = Signal(str, int, QtCore.QPoint)

        def __init__(self, parent=None):
            QtWidgets.QTabBar.__init__(self, parent)

            self.setAcceptDrops(True)
            self.setElideMode(QtCore.Qt.ElideRight)
            self.setSelectionBehaviorOnRemove(QtWidgets.QTabBar.SelectLeftTab)

            self.dragStartPos = QtCore.QPoint()
            self.dragDropedPos = QtCore.QPoint()
            self.mouseCursor = QtGui.QCursor()
            self.dragInitiated = False

        ##
        #  Send the onDetachTabSignal when a tab is double clicked
        #
        #  @param    event    a mouse double click event
        # def mouseDoubleClickEvent(self, event):
        #     event.accept()
        #     self.onDetachTabSignal.emit(self.tabAt(event.pos()), self.mouseCursor.pos())

        ##
        #  Set the starting position for a drag event when the mouse button is pressed
        #
        #  @param    event    a mouse press event
        def mousePressEvent(self, event):
            if event.button() == QtCore.Qt.LeftButton:
                self.dragStartPos = event.pos()

            self.dragDropedPos.setX(0)
            self.dragDropedPos.setY(0)

            self.dragInitiated = False

            QtWidgets.QTabBar.mousePressEvent(self, event)

        ##
        #  Determine if the current movement is a drag.  If it is, convert it into a QDrag.  If the
        #  drag ends inside the tab bar, emit an onMoveTabSignal.  If the drag ends outside the tab
        #  bar, emit an onDetachTabSignal.
        #
        #  @param    event    a mouse move event
        def mouseMoveEvent(self, event):
            # Determine if the current movement is detected as a drag (when outside the tab and above the drag distance)
            if not self.dragStartPos.isNull() and (
                (event.pos() - self.dragStartPos).manhattanLength()
                > QtWidgets.QApplication.startDragDistance() + 10
            ):
                self.dragInitiated = True

            # If the current movement is a drag initiated by the left button
            if ((event.buttons() & QtCore.Qt.LeftButton)) and self.dragInitiated:

                # Stop the move event
                finishMoveEvent = QtGui.QMouseEvent(
                    QtCore.QEvent.MouseMove,
                    event.pos(),
                    QtCore.Qt.NoButton,
                    QtCore.Qt.NoButton,
                    QtCore.Qt.NoModifier,
                )
                QtWidgets.QTabBar.mouseMoveEvent(self, finishMoveEvent)

                # Convert the move event into a drag
                drag = QtGui.QDrag(self)
                mimeData = QtCore.QMimeData()
                mimeData.setData("action", QtCore.QByteArray(b"application/tab-detach"))
                drag.setMimeData(mimeData)
                # Create the appearance of dragging the tab content
                pixmap = self.parent().widget(self.tabAt(self.dragStartPos)).grab()
                targetPixmap = QtGui.QPixmap(pixmap.size())
                targetPixmap.fill(QtCore.Qt.transparent)
                painter = QtGui.QPainter(targetPixmap)
                painter.setOpacity(0.85)
                painter.drawPixmap(0, 0, pixmap)
                painter.end()
                drag.setPixmap(targetPixmap)

                # Initiate the drag
                dropAction = drag.exec_(
                    QtCore.Qt.CopyAction | QtCore.Qt.MoveAction, QtCore.Qt.CopyAction
                )

                # For Linux:  Here, drag.exec_() will not return MoveAction on Linux.  So it
                #             must be set manually
                if self.dragDropedPos.x() != 0 and self.dragDropedPos.y() != 0:
                    dropAction = QtCore.Qt.MoveAction

                # If the drag completed outside of the tab bar, detach the tab and move
                # the content to the current cursor position
                if dropAction == QtCore.Qt.IgnoreAction:
                    event.accept()
                    self.onDetachTabSignal.emit(
                        self.tabAt(self.dragStartPos), self.mouseCursor.pos()
                    )

                # Else if the drag completed inside the tab bar, move the selected tab to the new position
                elif dropAction == QtCore.Qt.MoveAction:
                    if not self.dragDropedPos.isNull():
                        event.accept()
                        self.onMoveTabSignal.emit(
                            self.tabAt(self.dragStartPos), self.tabAt(self.dragDropedPos)
                        )
            else:
                QtWidgets.QTabBar.mouseMoveEvent(self, event)

        ##
        #  Determine if the drag has entered a tab position from another tab position
        #
        #  @param    event    a drag enter event
        def dragEnterEvent(self, event):
            mimeData = event.mimeData()
            formats = mimeData.formats()
            # check if drag mime data contains the action that detached it, to accept the drop
            if "action" in formats and mimeData.data("action") == QtCore.QByteArray(
                b"application/tab-detach"
            ):
                event.acceptProposedAction()

            QtWidgets.QTabBar.dragMoveEvent(self, event)

        ##
        #  Get the position of the end of the drag
        #
        #  @param    event    a drop event
        def dropEvent(self, event):
            self.dragDropedPos = event.pos()
            QtWidgets.QTabBar.dropEvent(self, event)

        ##
        #  Determine if the detached tab drop event occurred on an existing tab,
        #  then send the event to the DetachableTabWidget
        def detachedTabDrop(self, name, dropPos):

            tabDropPos = self.mapFromGlobal(dropPos)

            index = self.tabAt(tabDropPos)

            self.detachedTabDropSignal.emit(name, index, dropPos)

class Label(QLabel):
    def __init__(self, text):
        super(Label, self).__init__(text)
        self.setFont(bold)
        self.setWordWrap(True)
        self.setAutoFillBackground(False)
        self.setStyleSheet("background-color:transparent")

    def resizeEvent(self, event):
        width = self.width()
        height = self.height()

class LineEdit(QLineEdit):
    def __init__(self, parent=None, **kwargs):
        QLineEdit.__init__(self, parent=parent)

    def focusOutEvent(self, arg__1: QtGui.QFocusEvent) -> None:
        self.emit
        self.editingFinished.emit()
        return super().focusOutEvent(arg__1)

class TextEdit(QTextEdit):
    """
    A TextEdit editor that sends editingFinished events 
    when the text was changed and focus is lost.
    """

    editingFinished = QtCore.Signal()
    receivedFocus = QtCore.Signal()
    
    def __init__(self, parent):
        super(TextEdit, self).__init__(parent)
        self._changed = False
        self.setTabChangesFocus( True )
        self.textChanged.connect( self._handle_text_changed )

    def focusInEvent(self, event):
        super(TextEdit, self).focusInEvent( event )
        self.receivedFocus.emit()

    def focusOutEvent(self, event):
        if self._changed:
            self.editingFinished.emit()
        super(TextEdit, self).focusOutEvent( event )

    @QtCore.Slot()
    def _handle_text_changed(self):
        self._changed = True

    def setTextChanged(self, state=True):
        self._changed = state

    def setHtml(self, html):
        QtGui.QTextEdit.setHtml(self, html)
        self._changed = False

class KeyPressHandler(QtCore.QObject):
    """Custom key press handler"""
    escapePressed = QtCore.Signal(bool)
    returnPressed = QtCore.Signal(bool)
    shiftReturnPressed = QtCore.Signal(bool)

    def eventFilter(self, obj, event):
        if event.type() == QtCore.QEvent.KeyPress:
            event_key = event.key()
            if event_key == QtCore.Qt.Key.Key_Escape:
                self.escapePressed.emit(True)
                return True
            if event_key == QtCore.Qt.Key.Key_Return or event_key == QtCore.Qt.Key.Key_Enter and event_key == QtCore.Qt.Key.Key_Control:
                self.shiftReturnPressed.emit(True)
                return True
            if event_key == QtCore.Qt.Key.Key_Return or event_key == QtCore.Qt.Key.Key_Enter:
                self.returnPressed.emit(True)
                return True

        return QtCore.QObject.eventFilter(self, obj, event)

class EditableLabel(QWidget):
    """Editable label"""
    textChanged = QtCore.Signal(str)
    def __init__(self, parent=None, **kwargs):
        QWidget.__init__(self, parent=parent)
        
        self.is_editable = kwargs.get("editable", True)
        self.keyPressHandler = KeyPressHandler(self)

        self.mainLayout = QtWidgets.QHBoxLayout(self)
        self.mainLayout.setContentsMargins(0, 0, 0, 0)
        self.mainLayout.setObjectName("mainLayout")
        
        self.label = QtWidgets.QLabel(self)
        self.label.setObjectName("label")
        self.label.setAutoFillBackground(False)
        self.label.setStyleSheet("background-color: rgba(255, 255, 255, 0);")
        self.mainLayout.addWidget(self.label)
        self.lineEdit = LineEdit(self)
        self.lineEdit.setObjectName("lineEdit")
        self.mainLayout.addWidget(self.lineEdit)
        # hide the line edit initially
        self.lineEdit.setHidden(True)

        # setup signals
        self.create_signals()

    def create_signals(self):
        self.lineEdit.installEventFilter(self.keyPressHandler)
        self.label.mousePressEvent = self.labelPressedEvent

        # give the lineEdit both a `returnPressed` and `escapedPressed` action
        self.keyPressHandler.escapePressed.connect(self.escapePressedAction)
        self.keyPressHandler.returnPressed.connect(self.returnPressedAction)
        self.lineEdit.editingFinished.connect(self.returnPressedAction)

    def text(self):
        """Standard QLabel text getter"""
        return self.label.text()

    def setText(self, text):
        """Standard QLabel text setter"""
        self.label.blockSignals(True)
        self.label.setText(text)
        self.label.blockSignals(False)

    def labelPressedEvent(self, event):
        """Set editable if the left mouse button is clicked"""
        if event.button() == QtCore.Qt.MouseButton.LeftButton:
            self.setLabelEditableAction()

    def setLabelEditableAction(self):
        """Action to make the widget editable"""
        if not self.is_editable:
            return

        self.label.setHidden(True)
        self.label.blockSignals(True)
        self.lineEdit.setHidden(False)
        self.lineEdit.setText(self.label.text())
        self.lineEdit.blockSignals(False)
        self.lineEdit.setFocus(QtCore.Qt.MouseFocusReason)
        self.lineEdit.selectAll()

    def labelUpdatedAction(self):
        """Indicates the widget text has been updated"""
        text_to_update = self.lineEdit.text()

        if text_to_update != self.label.text():
            self.label.setText(text_to_update)
            self.textChanged.emit(text_to_update)

        self.label.setHidden(False)
        self.lineEdit.setHidden(True)
        self.lineEdit.blockSignals(True)
        self.label.blockSignals(False)

    def returnPressedAction(self):
        """Return/enter event handler"""
        self.labelUpdatedAction()

    def escapePressedAction(self):
        """Escape event handler"""
        self.label.setHidden(False)
        self.lineEdit.setHidden(True)
        self.lineEdit.blockSignals(True)
        self.label.blockSignals(False)

class GlobalSettingsDialog(QDialog):

    DARKTHEME = 0
    LIGHTTHEME = 1
    SYNCTHEME = 2

    def __init__(self) -> None:
        super().__init__()
        self.setupUI()
        self.resize(configuration.globalSettingsSizeX, configuration.globalSettingsSizeY)

    def setupUI(self):
        
        self.verticalLayout = QVBoxLayout(self)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.scrollArea = QScrollArea(self)
        self.scrollArea.setObjectName(u"scrollArea")
        self.scrollArea.setWidgetResizable(True)
        self.scrollArea.resize(self.scrollArea.minimumSizeHint())
        self.scrollAreaWidgetContents = QWidget()
        self.scrollAreaWidgetContents.setObjectName(u"scrollAreaWidgetContents")
        self.scrollAreaWidgetContents.setGeometry(QRect(0, 0, 418, 215))
        self.verticalLayout_2 = QVBoxLayout(self.scrollAreaWidgetContents)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.gridLayout = QGridLayout()
        self.gridLayout.setObjectName(u"gridLayout")
        self.gridLayout.setContentsMargins(-1, 10, -1, -1)
        self.label_2 = QLabel(self.scrollAreaWidgetContents)
        self.label_2.setObjectName(u"label_2")

        self.gridLayout.addWidget(self.label_2, 1, 0, 1, 1)

        self.appThemeSelectBox = QComboBox(self.scrollAreaWidgetContents)
        self.appThemeSelectBox.addItems(qdarktheme.get_themes())
        self.appThemeSelectBox.currentTextChanged.connect(self.onThemeChange)
        self.appThemeSelectBox.setObjectName(u"appThemeSelectBox")

        self.gridLayout.addWidget(self.appThemeSelectBox, 1, 1, 1, 1)

        self.label = QLabel(self.scrollAreaWidgetContents)
        self.label.setObjectName(u"label")

        self.gridLayout.addWidget(self.label, 0, 0, 1, 1)

        self.namingStyleSelectBox = QComboBox(self.scrollAreaWidgetContents)
        self.namingStyleSelectBox.addItem("")
        self.namingStyleSelectBox.addItem("")
        self.namingStyleSelectBox.setObjectName(u"namingStyleSelectBox")

        self.gridLayout.addWidget(self.namingStyleSelectBox, 0, 1, 1, 1)


        self.verticalLayout_2.addLayout(self.gridLayout)

        self.label_3 = QLabel(self.scrollAreaWidgetContents)
        self.label_3.setObjectName(u"label_3")

        self.verticalLayout_2.addWidget(self.label_3)

        self.gridLayout_2 = QGridLayout()
        self.gridLayout_2.setObjectName(u"gridLayout_2")
        self.gridLayout_2.setContentsMargins(-1, 10, -1, -1)
        self.label_4 = QLabel(self.scrollAreaWidgetContents)
        self.label_4.setObjectName(u"label_4")

        self.gridLayout_2.addWidget(self.label_4, 0, 0, 1, 1)

        self.lineEdit = QLineEdit(self.scrollAreaWidgetContents)
        self.lineEdit.setObjectName(u"lineEdit")
        self.lineEdit.setMaximumSize(QSize(50, 16777215))

        self.gridLayout_2.addWidget(self.lineEdit, 0, 1, 1, 1)

        self.label_5 = QLabel(self.scrollAreaWidgetContents)
        self.label_5.setObjectName(u"label_5")
        self.label_5.setMaximumSize(QSize(20, 16777215))

        self.gridLayout_2.addWidget(self.label_5, 0, 2, 1, 1)


        self.verticalLayout_2.addLayout(self.gridLayout_2)

        self.verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)

        self.verticalLayout_2.addItem(self.verticalSpacer)

        self.scrollArea.setWidget(self.scrollAreaWidgetContents)

        self.verticalLayout.addWidget(self.scrollArea)

        self.buttonBox = QDialogButtonBox(self)
        self.buttonBox.setObjectName(u"buttonBox")
        self.buttonBox.setOrientation(Qt.Horizontal)
        self.buttonBox.setStandardButtons(QDialogButtonBox.Cancel|QDialogButtonBox.Save)

        self.verticalLayout.addWidget(self.buttonBox)


        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)

        self.setWindowTitle("Global Settings")
        self.label_2.setText("Theme")

        self.label.setText("Default Naming Style:")
        self.namingStyleSelectBox.setItemText(0, u"By UUID")
        self.namingStyleSelectBox.setItemText(1, u"By Name")

        self.label_3.setText(u"Font Settings")
        self.label_4.setText(u"Title Size")
        self.lineEdit.setText(u"16")
        self.label_5.setText(u"pt")

        self.scrollAreaWidgetContents.resize(self.scrollArea.minimumSizeHint())
        self.scrollArea.resize(self.scrollArea.minimumSizeHint())
        self.loadSettings()

    def loadSettings(self):
        self.appThemeSelectBox.setCurrentIndex(self.appThemeSelectBox.findText(configuration.themename))
        self.namingStyleSelectBox.setCurrentIndex(self.namingStyleSelectBox.findText(configuration.namingstyle))
    
    def saveSettings(self):
        configuration.globalSettingsSizeX = self.size().width()
        configuration.globalSettingsSizeY = self.size().height()
        configuration.saveSettings()

    def accept(self) -> None:
        super().accept()
        configuration.themename = self.appThemeSelectBox.currentText()
        configuration.namingstyle = self.namingStyleSelectBox.currentText()
        self.saveSettings()

    def reject(self) -> None:
        super().reject()
        try:
            configuration.themename = self.oldtheme
            qdarktheme.setup_theme(self.oldtheme)
        except AttributeError:
            pass
        self.saveSettings()

    def onThemeChange(self, theme):
        self.oldtheme = configuration.themename
        qdarktheme.setup_theme(theme)

    def closeEvent(self, arg__1) -> None:
        self.saveSettings()
        return super().closeEvent(arg__1)

class PieChart(QWidget):

    def __init__(self):
        super().__init__()

        self.series = QPieSeries()

        self.series.append('Jane', 1)
        self.series.append('Joe', 2)
        self.series.append('Andy', 3)
        self.series.append('Barbara', 4)
        self.series.append('Axel', 5)

        self.slice = self.series.slices()[1]
        self.slice.setExploded()
        self.slice.setLabelVisible()
        self.slice.setPen(QPen(Qt.darkGreen, 2))
        self.slice.setBrush(Qt.green)

        self.chart = QChart()
        self.chart.addSeries(self.series)
        self.chart.setTitle('Simple piechart example')
        self.chart.legend().hide()

        self._chart_view = QChartView(self.chart)
        self._chart_view.setRenderHint(QPainter.Antialiasing)


class ExpandableLineEdit(QWidget):
    textChanged = QtCore.Signal(str)
    textCommitted = QtCore.Signal(str)

    def __init__(self, parent: Optional[QtWidgets.QWidget]) -> None:
        super().__init__(parent)
        self.mainLayout = QtWidgets.QHBoxLayout(self)
        self.mainLayout.setContentsMargins(0, 0, 0, 0)
        self.mainLayout.setObjectName("mainLayout")

        self.lineEdit = LineEdit(self)
        self.lineEdit.setObjectName("lineEdit")
        self.mainLayout.addWidget(self.lineEdit)

        self.textEdit = TextEdit(self)
        self.textEdit.setObjectName("textEdit")
        self.mainLayout.addWidget(self.textEdit)
        self.textEdit.setHidden(True)

        self.setupSignals()

    def text(self) -> str:
        self.unifyText()
        return self.lineEdit.text()

    def setText(self, text):
        self.lineEdit.setText(text)
        self.textEdit.setText(text)

    def setupSignals(self):
        self.lineEdit.editingFinished.connect(self.returnPressed)
        self.textEdit.editingFinished.connect(self.returnPressed)
        self.lineEdit.textChanged.connect(self.edited)
        self.textEdit.textChanged.connect(self.edited)

    def returnPressed(self):
        self.unifyText()
        self.textCommitted.emit(self.lineEdit.text())

    def edited(self):
        try:
            self.evaluate()
            self.textChanged.emit(self.lineEdit.text())
        except RecursionError: pass

    def unifyText(self):
        if self.lineEdit.isHidden():
            self.lineEdit.setText(self.textEdit.toPlainText())
        else:
            self.textEdit.setText(self.lineEdit.text())
        
    def evaluate(self):
        shouldHide = self.getTextWidth() >= self.lineEdit.width()
        self.unifyText()
        self.lineEdit.setHidden(shouldHide)
        self.textEdit.setHidden(not shouldHide)
        self.lineEdit.blockSignals(shouldHide)
        self.textEdit.blockSignals(not shouldHide)
        if shouldHide:
            if self.lineEdit.hasFocus():
                self.textEdit.setFocus(Qt.FocusReason.OtherFocusReason)
                cursor = QTextCursor(self.textEdit.document())
                cursor.movePosition(QTextCursor.MoveOperation.End)
                self.textEdit.setTextCursor(cursor)
        else:
            if self.textEdit.hasFocus():
                self.lineEdit.setFocus(Qt.FocusReason.OtherFocusReason)

        

    def getTextWidth(self) -> int:
        return QFontMetrics(self.font()).horizontalAdvance(self.lineEdit.text())

class GenericCanvasView(QWidget):

    def __init__(self, source : System, parent: Optional[QtWidgets.QWidget]) -> None:
        super().__init__(parent)
        self.setupUI()
        self.source = source

    def setupUI(self):
        self.horizontalLayout = QHBoxLayout(self)
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.horizontalLayout.setContentsMargins(0, 0, 0, 0)
        self.ElementTree = QTreeWidget(self)
        __qtreewidgetitem = QTreeWidgetItem()
        __qtreewidgetitem.setText(0, u"Available Elements")
        self.ElementTree.setHeaderItem(__qtreewidgetitem)
        self.ElementTree.setObjectName(u"ElementTree")
        sizePolicy = QSizePolicy(QSizePolicy.Preferred, QSizePolicy.Expanding)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(self.ElementTree.sizePolicy().hasHeightForWidth())
        self.ElementTree.setSizePolicy(sizePolicy)
        self.ElementTree.setDragDropMode(QAbstractItemView.InternalMove)
        self.ElementTree.setSelectionMode(QTreeWidget.SelectionMode.ContiguousSelection)
        self.ElementTree.setSortingEnabled(True)
        self.ElementTree.setHeaderHidden(False)
        self.ElementTree.header().setProperty("showSortIndicator", True)

        self.horizontalLayout.addWidget(self.ElementTree)

        self.Scene = DiagramScene()
        self.Viewer = DiagramViewer(self.Scene)
        self.Viewer.setObjectName(u"Viewer")

        self.horizontalLayout.addWidget(self.Viewer)

class DesignView(GenericCanvasView):

    def __init__(self, source, parent: Optional[QtWidgets.QWidget]) -> None:
        super().__init__(source, parent)
        self.Scene.setSceneRect(0,0,50000,50000)
        self.Viewer.centerOn(25000, 25000)
        self.populateTree()

        self.Viewer.newVisibleArea.connect(self.onViewportResize)


    def onViewportResize(self, rect):
        pass
        '''self.externalConnectors.boundingbox = rect
        self.externalConnectors.updatePos()'''

    def populateTree(self):
        self.ElementTree.clear()
        self.toplevelDLs = QTreeWidgetItem(self.ElementTree)
        self.toplevelDLs.setText(0, "Design Elements")
        self.toplevelSystems = QTreeWidgetItem(self.ElementTree)
        self.toplevelSystems.setText(0, "Available Systems")
        self.ElementTree.addTopLevelItem(self.toplevelDLs)
        self.ElementTree.addTopLevelItem(self.toplevelSystems)

        # Populate Systems
        for system in objects.systems:
            system : System
            self.toplevelDLs = QTreeWidgetItem(self.toplevelSystems)
            self.toplevelDLs.setText(0, system.name)
                
class DisplayItem(QWidget):
    def __init__(self, item : Element, parent: Optional[QtWidgets.QWidget] = None) -> None:
        super().__init__(parent)
        self.resize(380, 480)
        self.ownedItem = item
        self.fieldAreas : list[ExpandableLineEdit] = []
        self.setupUI()
        self.createFields()

        # Rounded corners
        path = QPainterPath()
        path.addRoundedRect(0, 0, self.size().width(), self.size().height(), 10, 10)
        mask = QRegion(path.toFillPolygon().toPolygon())
        self.setMask(mask)

    def setupUI(self):

        self.verticallayout = QVBoxLayout(self)

        self.idLabel = QLabel(str(self.ownedItem.uuid), self)

        self.verticallayout.addWidget(self.idLabel)

        self.scrollArea = QScrollArea(self)
        self.scrollArea.setFrameShape(QtWidgets.QFrame.Shape.NoFrame)
        self.scrollArea.setWidgetResizable(True)
        self.scrollAreaContents = QtWidgets.QWidget()
        self.scrollAreaContents.setGeometry(QtCore.QRect(0, 0, 380, 480))
        self.scrollArea.setWidget(self.scrollAreaContents)
        self.verticallayout.addWidget(self.scrollArea)
        
        self.mainLayout = QVBoxLayout(self.scrollAreaContents)
        self.scrollAreaContents.setLayout(self.mainLayout)
        

    def createFields(self):
        for i, (key, value) in enumerate(self.ownedItem.public.items()):
            self.fieldAreas.append(FieldWidget(key, self.scrollAreaContents))
            self.fieldAreas[-1].setText(value)
            self.fieldAreas[-1].edited.connect(lambda title, content : self.itemChanged(title, content))
            self.mainLayout.addWidget(self.fieldAreas[-1])


    def itemChanged(self, key, value):
        prevpublic = copy.deepcopy(self.ownedItem.public)
        self.ownedItem.public[key] = value
        print(utilities.diffdict(prevpublic, self.ownedItem.public))

class FieldWidget(QWidget):

    edited = Signal(str, str)

    def __init__(self, title, parent: Optional[QtWidgets.QWidget]) -> None:
        super().__init__(parent)
        self.title = title
        self.mainLayout = QVBoxLayout(self)
        self.setLayout(self.mainLayout)

        self.mainLayout.addWidget(QLabel(title, self))
        self.textfield = ExpandableLineEdit(self)
        self.mainLayout.addWidget(self.textfield)

        self.textfield.textCommitted.connect(lambda x: self.edited.emit(title, x))
        

    def setText(self, text : str):
        self.textfield.setText(text)

    def text(self):
        return self.textfield.text()