from enum import Enum
import inspect
import math
import random
from types import NoneType
import typing
from PySide6.QtWidgets import (
    QGraphicsView, QMenu,
    QGraphicsItem, QGraphicsScene, QWidgetAction, QGraphicsRectItem, QGraphicsLineItem, QGraphicsPathItem, QGraphicsProxyWidget, QLabel, QApplication, QUndoView, QStatusBar
)
from PySide6 import QtCore, QtWidgets
from PySide6.QtCore import Qt, QRectF, QRect, QPointF, QVariantAnimation, QEasingCurve, QLineF, QPoint
from PySide6 import QtGui
from PySide6.QtGui import QTransform, QPixmap, QAction, QPainter, QColor, QPen, QBrush, QCursor, QPainterPath, QFont, QFontMetrics, QUndoStack, QKeySequence, QWheelEvent

from BlackBoxr.mainwindow.widgets import Label
from BlackBoxr.misc import configuration, objects
from BlackBoxr.misc.Datatypes import MoveCommand, NameEdit
from BlackBoxr.utilities import closestPoint

GRIDSIZE = (25, 25)
ENDOFFSET = -QPointF(25, 25)


class NodeBase( QGraphicsItem ):
    """
    A simple QGraphicsItem that can be dragged around the scene.
    Of course, this behavior is easier to achieve if you simply use the default 
    event handler implementations in place and call 
    QGraphicsItem.setFlags( QGraphicsItem.ItemIsMovable )
    
    ...but this example shows how to do it by hand, in case you want special behavior 
    (e.g. only allowing left-right movement instead of arbitrary movement). 
    """
    
    def __init__(self, *args, **kwargs):
        super( NodeBase, self ).__init__(*args, **kwargs )
        self.setAcceptHoverEvents(True)
        self.setFlags(self.flags() | QGraphicsItem.GraphicsItemFlag.ItemIsMovable | QGraphicsItem.GraphicsItemFlag.ItemIsSelectable | QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges)
        self.oldpos = self.scenePos().toPoint()
        self.previewSocket = None

        self.leftTerminals    : list[Socket] = []
        self.rightTerminals   : list[Socket] = []
        self.topTerminals     : list[Socket] = []
        self.bottomTerminals  : list[Socket] = []
    
    def boundingRect(self):
        return QRectF( 0, 0, 100, 100)
    
    # To be overwritten
    def paint(self, painter, option, widget):
        painter.setRenderHint(QPainter.Antialiasing)
        body = QPainterPath()
        pen = painter.pen()
        pen.setColor(Qt.black)
        pen.setCapStyle(Qt.RoundCap)
        painter.setPen(pen)
        body.addRoundedRect(self.boundingRect(), 10, 10)
        painter.fillPath(body, configuration.NodeBackground)
        painter.drawPath(body)

        '''if not isinstance(self.previewpos, NoneType):
            pen.setColor(QColor(255, 0, 0, 255))
            pen.setWidth(6)
            painter.setPen(pen)
            painter.drawEllipse(self.previewpos, 5, 5)'''

        if self.isSelected():
            selectionoutline = QPainterPath()
            selectionoutline.addRoundedRect(self.boundingRect(), 10, 10)
            pen.setColor(configuration.SelectColor)
            pen.setWidth(6)
            painter.setPen(pen)
            painter.drawPath(selectionoutline)

    def hoverEnterEvent(self, event):
        cursor = QCursor( Qt.OpenHandCursor )
        QApplication.instance().setOverrideCursor( cursor )
        

    def hoverMoveEvent(self, event: QtWidgets.QGraphicsSceneHoverEvent) -> None:

        bounds = self.boundingRect()
        hpadding = bounds.width() * 0.2
        vpadding = bounds.height() * 0.2

        leftregion = QRectF(bounds.x(), bounds.y(), hpadding, bounds.height())
        rightregion = QRectF(bounds.width() - hpadding, bounds.y(), hpadding, bounds.height())
        topregion = QRectF(bounds.x(), bounds.y(), bounds.width(), vpadding)
        botregion = QRectF(bounds.x(), bounds.height() - vpadding, bounds.width(), vpadding)

        centertop = QPointF(bounds.width()/2, bounds.y())
        centerleft = QPointF(bounds.x(), bounds.height()/2)
        centerbot = QPointF(bounds.width()/2, bounds.height())
        centerright = QPointF(bounds.width(), bounds.height()/2)

        if leftregion.contains(event.pos()) or rightregion.contains(event.pos()) or topregion.contains(event.pos()) or botregion.contains(event.pos()):

            closestpoint = closestPoint(event.pos(), [centerbot, centerleft, centerright, centertop])
            self.update()
            previewpos = closestpoint
            
            if leftregion.contains(previewpos):
                pass
            elif rightregion.contains(previewpos):
                pass
            elif topregion.contains(previewpos):
                pass
            elif botregion.contains(previewpos):
                pass
        #print(f'Top : {topregion.contains(event.pos())}\nBottom : {botregion.contains(event.pos())}\nLeft : {leftregion.contains(event.pos())}\nRight : {rightregion.contains(event.pos())}\nPreviewpos : {self.previewpos}')
    
    def hoverLeaveEvent(self, event):
        QApplication.instance().restoreOverrideCursor()
        self.previewSocket = None

    def itemChange(self, change: QtWidgets.QGraphicsItem.GraphicsItemChange, value: typing.Any) -> typing.Any:
        if change == QGraphicsItem.ItemPositionChange:
            newPos = value.toPoint()
            #print(f'{oldpos}, {newPos}')
            xV = round(newPos.x()/GRIDSIZE[0])*GRIDSIZE[0]
            yV = round(newPos.y()/GRIDSIZE[1])*GRIDSIZE[1]
            ret = QPointF(xV, yV)
            
        else:
            ret = super().itemChange(change, value)
        return ret

    def mousePressEvent(self, event: QtWidgets.QGraphicsSceneMouseEvent) -> None:
        self.oldpos = self.scenePos().toPoint()
        return super().mousePressEvent(event)

    def mouseReleaseEvent(self, event: QtWidgets.QGraphicsSceneMouseEvent) -> None:
        self.newpos = self.scenePos().toPoint()
        if self.newpos != self.oldpos:
            objects.undoStack.push(MoveCommand(self, self.oldpos, newpos=self.newpos))
        return super().mouseReleaseEvent(event)

    def renamed(self):
        objects.undoStack.push(NameEdit(self, self.lbl.namelabel.text()))
        self.blockname = self.lbl.namelabel.text()


class Socket(QGraphicsItem):

    PILLSIZE = QRectF( 0, 0, 20, 5)

    def __init__(self, parent, vertical = False) -> None:
        
        super( Socket, self ).__init__(parent=parent )
        self.parentNode = parent
        self.__trace = None
        self.setZValue(100)
        self.traces = []
        self.vertical = vertical
        self.setFlags(self.flags() | QGraphicsItem.GraphicsItemFlag.ItemIsSelectable | QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges)

    def paint(self, painter, option, widget):
        
        pos = Socket.PILLSIZE.getCoords()
        if self.vertical:
            pos = (pos[0], pos[1], pos[3], pos[2])
        pen = painter.pen()
        pen.setCapStyle(Qt.RoundCap)
        pen.setWidth(Socket.PILLSIZE.height())
        pen.setColor(QColor(255, 255, 255, 255))
        painter.setPen(pen)
        #painter.drawLine(pos[0], pos[3]/2, pos[2], pos[3]/2)
        painter.drawRect(self.boundingRect())

        if self.isSelected():
            selectionoutline = QPainterPath()
            selectionoutline.addRoundedRect(self.boundingRect(), 10, 10)
            pen.setColor(configuration.SelectColor)
            pen.setWidth(6)
            painter.setPen(pen)
            painter.drawPath(selectionoutline)

    def boundingRect(self):
        pos = Socket.PILLSIZE.getCoords()
        if self.vertical:
            return QRectF(pos[0], pos[1], pos[3], pos[2])
        else:
            return QRectF(pos[0], pos[1], pos[2], pos[3])

    def mousePressEvent(self, event):
        if objects.qapp.keyboardModifiers() == Qt.ControlModifier:
            self.__trace = OldArrowItem(endItem=self.scene().selectedItems()[0], startItem=self, parent=None)
            self.__trace.setZValue(0)
            self.__trace.setPos(self.scenePos())
            self.scene().addItem(self.__trace)
            self.setSelected(False)
        
        elif objects.qapp.keyboardModifiers() == Qt.AltModifier:
            self.scene().removeItem(self.__trace)
            self.__trace = None
        else:
            for item in self.scene().selectedItems():
                item.setSelected(False)
            self.setSelected(True)

    def mouseReleaseEvent(self, event):
        if not isinstance(self.__trace, NoneType):
            self.__trace.setZValue(0)

    def mouseMoveEvent(self, event: QtWidgets.QGraphicsSceneMouseEvent) -> None:
        if isinstance(self.__trace, NoneType):
            self.__trace = OldArrowItem(endItem=event.pos(), startItem=self, parent=None)
            self.__trace.setZValue(0)
            self.__trace.setPos(self.scenePos())
            self.scene().addItem(self.__trace)
            self.setSelected(False)
        self.__trace.prepareGeometryChange()
        self.__trace.myStartItem = event.pos()

class DiagramViewer(QGraphicsView):

    def __init__(self, scene : QGraphicsScene):
        super(DiagramViewer, self).__init__(scene)
        self._scene = scene
        self.startPos = None
        self.setAcceptDrops(True)
        
        self.setDragMode(QGraphicsView.DragMode.RubberBandDrag)
        self.setViewportUpdateMode(QGraphicsView.FullViewportUpdate)

    ''' Item Focusing '''
    def moveTo(self, pos : QPointF):
        self.anim = QVariantAnimation()
        self.anim.setDuration(500)
        self.anim.setEasingCurve(QEasingCurve.InOutQuart)
        self.anim.setStartValue(self.mapToScene(self.rect().center()))
        self.anim.setEndValue(QPointF(pos.x(), pos.y()))
        self.anim.valueChanged.connect(self._moveTick)
        self.anim.start()

    def _moveTick(self, pos):
        self.centerOn(pos)

    ''' Drag and Drop behavior '''
    def dropEvent(self, event: QtGui.QDropEvent) -> None:
        return super().dropEvent(event)

    def dragEnterEvent(self, event: QtGui.QDragEnterEvent) -> None:
        event.accept()
        event.acceptProposedAction()
        return super().dragEnterEvent(event)

    def dragMoveEvent(self, event: QtGui.QDragMoveEvent) -> None:
        event.accept()
        return super().dragMoveEvent(event)

    def contextMenuEvent(self, event) -> None:
        pass

    ''' Scroll behavior
    Responsible for scaling when scrolling
    '''
    def wheelEvent(self, event : QWheelEvent, norep = False):
        
        if Qt.KeyboardModifier.ControlModifier == event.modifiers():

            self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
            if event.angleDelta().y() > 0:
                self.scale(1.1, 1.1)
            else:
                self.scale(0.9, 0.9)
        else:
            super(DiagramViewer, self).wheelEvent(event)
        self._scene.update()

class DiagramScene(QGraphicsScene):

    def __init__(self):
        super().__init__()
        
        self._dragged= False
        #self.setBackgroundBrush(configuration.GridColor)

    def set_viewer(self, viewer):
        self.viewer = viewer

    def drawBackground(self, painter: QtGui.QPainter, rect: typing.Union[QtCore.QRectF, QtCore.QRect]) -> None:
        left = int(rect.left()) - (int(rect.left()) % GRIDSIZE[0])
        top = int(rect.top()) - (int(rect.top()) % GRIDSIZE[1])
        painter.fillRect(rect, configuration.CanvasColor)
        pen = painter.pen()
        pen.setColor(configuration.GridColor)
        painter.setPen(pen)

        lines = []
        for x in range(left, int(rect.right()), GRIDSIZE[0]):
            lines.append(QLineF(x, rect.top(), x, rect.bottom()))
        for y in range(top, int(rect.bottom()), GRIDSIZE[1]):
            lines.append(QLineF(rect.left(), y, rect.right(), y))

        painter.drawLines(lines)

        return super().drawBackground(painter, rect)

    ''' Mouse Interactions '''
    def dragEnterEvent(self, QGraphicsSceneDragDropEvent):
        QGraphicsSceneDragDropEvent.accept()

    def dragMoveEvent(self, QGraphicsSceneDragDropEvent):
        QGraphicsSceneDragDropEvent.accept()

class OldArrowItem(QGraphicsLineItem):
    ''' ArrowItem represents connections between items '''

    def __init__(self, startItem, endItem, parent = None):
        """
        ArrowItem represents a connection between two items
        @params:
            Set style to 2 for a dotted line
        """
        
        super(OldArrowItem, self).__init__() if isinstance(parent, NoneType) else super(OldArrowItem, self).__init__(parent)
        #self.setZValue(1)
        
        self.arrowHead = QtGui.QPolygonF()
        self.myStartItem = startItem
        self.myEndItem = endItem
        self.myColor = QColor(255, 0, 0, 255)
        pen = QPen()
        pen.setColor(self.myColor)
        pen.setWidth(5)
        pen.setCapStyle(QtCore.Qt.PenCapStyle.RoundCap)
        pen.setJoinStyle(QtCore.Qt.PenJoinStyle.RoundJoin)
        self.setPen(pen)

        self.setAcceptHoverEvents(True)

    def startItem(self):
        return self.myStartItem

    def endItem(self):
        return self.myEndItem

    def setColor(self, color : QColor):
        self.myColor = color

    def mouseDoubleClickEvent(self, event: 'QGraphicsSceneMouseEvent') -> None:
        pass
        '''print("{} : {}\n{} : {}".format(self.myStartItem, self.mapFromParent(self.myStartItem.pos()), self.myEndItem, self.mapFromParent(self.myEndItem.pos())))
        if isinstance(self.myStartItem, QGraphicsItem):
            
            p1 = self.mapFromParent(self.myStartItem.pos())
        else:
            p1 = self.myStartItem
        if isinstance(self.myEndItem, QGraphicsItem):
            p2 = self.mapFromParent(self.myEndItem.pos())
        else:
            p2 = self.myEndItem

        cursorpos : QPointF = self.scene().views()[0].mapToScene(self.scene().views()[0].mapFromGlobal(QtGui.QCursor.pos()))
        distToStart = math.sqrt((cursorpos.x() - self.myStartItem.x())**2 + (cursorpos.y() - self.myStartItem.y())**2)
        distToEnd = math.sqrt((cursorpos.x() - self.myEndItem.x())**2 + (cursorpos.y() - self.myEndItem.y())**2)
        if distToStart < distToEnd:
            #self.scene.views()[0].centerOn(self.myEndItem)
            self.scene().views()[0].moveTo(self.myEndItem)
        else:
            #self.scene.views()[0].centerOn(self.myStartItem)
            self.scene().views()[0].moveTo(p1)
        return super().mouseDoubleClickEvent(event)'''


    def boundingRect(self):
        extra = (self.pen().width() + 20) / 2.0
        p1 = self.line().p1()
        p2 = self.line().p2()
        return QtCore.QRectF(p1, QtCore.QSizeF(p2.x() - p1.x(), p2.y() - p1.y())).normalized().adjusted(-extra, -extra, extra, extra)

    def shape(self):
        path = super(OldArrowItem, self).shape()
        path.addPolygon(self.arrowHead)
        return path

    def updatePosition(self):
        line = QtCore.QLineF(self.mapFromItem(self.myStartItem, 0, self.myStartItem.rect.y()), self.mapFromItem(self.myEndItem, 0, 0))
        self.setLine(line)

    def hoverEnterEvent(self, event: 'QGraphicsSceneHoverEvent') -> None:
        self.myColor = QColor(0, 255, 0)
        return super().hoverEnterEvent(event)

    def hoverLeaveEvent(self, event: 'QGraphicsSceneHoverEvent') -> None:
        self.myColor = QColor(random.randint(0, 5), random.randint(0, 5), random.randint(0, 5))
        return super().hoverLeaveEvent(event)

    def paint(self, painter, option, widget=None):
        if isinstance(self.myStartItem, QGraphicsItem):
            myStartItem = self.mapFromParent(self.myStartItem.scenePos())
        else:
            myStartItem = self.myStartItem
        if isinstance(self.myEndItem, QGraphicsItem):
            myEndItem = self.mapFromParent(self.myEndItem.scenePos())
            
        else:
            myEndItem = self.myEndItem

        myPen = self.pen()
        myPen.setColor(self.myColor)
        arrowSize = 10.0
        painter.setPen(myPen)
        painter.setBrush(self.myColor)

        #startpos = QPointF(myStartItem.x() + (self.myStartItem.boundingRect().x() / 2), myStartItem.y() + self.myStartItem.boundingRect().y())

        p1 = myStartItem

        p2 = myEndItem

        

        self.setLine(QtCore.QLineF(p1, p2))
        line = self.line()
        try:
            angle = math.acos(line.dx() / line.length())
            if line.dy() >= 0:
                angle = (math.pi * 2.0) - angle

            arrowP1 = line.p1() + QtCore.QPointF(math.sin(angle + math.pi / 3.0) * arrowSize,
                                            math.cos(angle + math.pi / 3) * arrowSize)
            arrowP2 = line.p1() + QtCore.QPointF(math.sin(angle + math.pi - math.pi / 3.0) * arrowSize,
                                            math.cos(angle + math.pi - math.pi / 3.0) * arrowSize)

            self.arrowHead.clear()
            for point in [line.p1(), arrowP1, arrowP2]:
                self.arrowHead.append(point)

            painter.drawLine(line)
            painter.drawPolygon(self.arrowHead)
        except ZeroDivisionError:
            pass


