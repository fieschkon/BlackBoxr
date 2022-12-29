import copy
from enum import Enum
import inspect
import math
import random
import sys
import threading
from types import NoneType
import typing
from PySide6.QtWidgets import (
    QGraphicsView, QMenu,
    QGraphicsItem, QGraphicsScene, QWidgetAction, QGraphicsRectItem, QGraphicsLineItem, QGraphicsPathItem, QGraphicsProxyWidget, QLabel, QApplication, QUndoView, QStatusBar
)
from PySide6 import QtCore, QtWidgets
from PySide6.QtCore import Qt, QRectF, QRect, QPointF, QVariantAnimation, QEasingCurve, QLineF, QPoint, QRunnable, Signal, QThreadPool, QObject, Slot, QThread
from PySide6 import QtGui
from PySide6.QtGui import QTransform, QPixmap, QAction, QPainter, QColor, QPen, QBrush, QCursor, QPainterPath, QFont, QFontMetrics, QUndoStack, QKeySequence, QWheelEvent

from BlackBoxr.mainwindow.widgets import DisplayItem, EditableLabel, ExpandableLineEdit, Label
from BlackBoxr.misc import configuration, objects
from BlackBoxr.misc.Datatypes import DesignElement, MoveCommand, NameEdit, RequirementElement
from BlackBoxr.utilities import closestPoint, printMatrix, snapToGrid
from pathfinding.core.diagonal_movement import DiagonalMovement
from pathfinding.core.grid import Grid
from pathfinding.finder.a_star import AStarFinder
from pathfinding.finder.dijkstra import DijkstraFinder
GRIDSIZE = (25, 25)
ENDOFFSET = -QPointF(25, 25)


class NodeBase(QGraphicsItem):

    def __init__(self, *args, **kwargs):
        super(NodeBase, self).__init__(*args, **kwargs)
        self.setAcceptHoverEvents(True)
        self.setFlags(self.flags() | QGraphicsItem.GraphicsItemFlag.ItemIsMovable |
                      QGraphicsItem.GraphicsItemFlag.ItemIsSelectable | QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges)
        self.oldpos = self.scenePos().toPoint()

    def boundingRect(self):
        return QRectF(0, 0, 100, 100)

    # To be overwritten
    def paint(self, painter, option, widget):
        painter.setRenderHint(QPainter.Antialiasing)
        body = QPainterPath()
        pen = painter.pen()
        pen.setColor(Qt.black)
        pen.setCapStyle(Qt.RoundCap)
        painter.setPen(pen)
        body.addRoundedRect(self.boundingRect(), 10, 10)
        painter.fillPath(body, configuration.NodeBackground.color())
        painter.drawPath(body)

        if self.isSelected():
            selectionoutline = QPainterPath()
            selectionoutline.addRoundedRect(self.boundingRect(), 10, 10)
            pen.setColor(configuration.SelectColor)
            pen.setWidth(6)
            painter.setPen(pen)
            painter.drawPath(selectionoutline)

    def hoverEnterEvent(self, event):
        cursor = QCursor(Qt.OpenHandCursor)
        QApplication.instance().setOverrideCursor(cursor)

    def hoverLeaveEvent(self, event):
        QApplication.instance().restoreOverrideCursor()

    def itemChange(self, change: QtWidgets.QGraphicsItem.GraphicsItemChange, value: typing.Any) -> typing.Any:
        if change == QGraphicsItem.ItemPositionChange:
            newPos = value.toPoint()
            # print(f'{oldpos}, {newPos}')
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
            objects.undoStack.push(MoveCommand(
                self, self.oldpos, newpos=self.newpos))
        return super().mouseReleaseEvent(event)

    def renamed(self):
        objects.undoStack.push(NameEdit(self, self.lbl.namelabel.text()))
        self.blockname = self.lbl.namelabel.text()


class DesignNode(NodeBase):

    MINIMUMSOCKETPADDING = 10

    def __init__(self, dl: DesignElement, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.previewSocket: Socket = Socket(None, None, False, 255/2)
        self.previewActive = False

        self.ownedDL = dl

        self.leftTerminals: list[Socket] = []
        self.rightTerminals: list[Socket] = []
        self.topTerminals: list[Socket] = []
        self.bottomTerminals: list[Socket] = []

        self.proxy = QGraphicsProxyWidget(self)
        self.lbl = EditableLabel()
        self.lbl.setText("DL")
        self.proxy.setWidget(self.lbl)

        # self.populate()

    def populate(self):
        # TODO
        sys = self.ownedDL.owningSystem
        self.lbl.setText(self.ownedDL.name)

        for i in self.ownedDL.leftSockets:
            pass
        sys.searchByUUID()

    def hookupConnections(self):
        # TODO
        self.scene().searchByUUID(str(self.ownedDL.uuid))  # For searching

    def boundingRect(self):

        horizontalUnitSize = Socket.PILLSIZE.height() + DesignNode.MINIMUMSOCKETPADDING*2
        verticalUnitSize = Socket.PILLSIZE.width() + DesignNode.MINIMUMSOCKETPADDING
        # Calculate horizontal Terminal offsets
        height = max(len(self.leftTerminals)+1, (len(self.rightTerminals)+1)
                     ) * verticalUnitSize + 4*Socket.PILLSIZE.height()
        # Calculate vertical terminal offsets
        width = max(len(self.bottomTerminals)+1, (len(self.topTerminals)+1)
                    ) * horizontalUnitSize + 4*Socket.PILLSIZE.width()

        basesize = super().boundingRect()

        return QRectF(0, 0, max(width, basesize.width()), max(height, basesize.height()))

    def hoverMoveEvent(self, event: QtWidgets.QGraphicsSceneHoverEvent) -> None:
        self.removePreviewSocket()
        zone = self.determineClosestTerminalZone(event.pos())
        if not isinstance(zone, NoneType):
            self.previewSocket.setParentItem(self)
            self.previewSocket.vertical = zone[1]
            zone[0].append(self.previewSocket)
            self.previewSocket.spriteOpacity = (255/2)
            self.previewActive = True
            self.update()

    def hoverLeaveEvent(self, event):
        super().hoverLeaveEvent(event)
        self.removePreviewSocket()

    def mousePressEvent(self, event: QtWidgets.QGraphicsSceneMouseEvent) -> None:
        super().mousePressEvent(event)

    def materializePreview(self, pos):
        socketzone = self.determineClosestTerminalZone(pos)
        if socketzone != None:
            dl = DesignElement(self.ownedDL.owningSystem)
            sock = Socket(self, dl, vertical=socketzone[1], preview=False)
            socketzone[0].append(sock)
            return sock
        else:
            return None

    def removePreviewSocket(self):
        # Remove preview socket from all terminal lists
        [terminalList.remove(self.previewSocket) if self.previewSocket in terminalList else None for terminalList in [
            self.leftTerminals, self.rightTerminals, self.topTerminals, self.bottomTerminals]]
        self.previewSocket.setParentItem(None)
        self.previewSocket.spriteOpacity = 0
        self.previewActive = False
        self.update()

    def determineClosestTerminalZone(self, inpos) -> typing.Union[tuple[list, bool], NoneType]:
        bounds = self.boundingRect()
        hpadding = bounds.width() * 0.2
        vpadding = bounds.height() * 0.2

        leftregion = QRectF(bounds.x(), bounds.y(), hpadding, bounds.height())
        rightregion = QRectF(bounds.width() - hpadding,
                             bounds.y(), hpadding, bounds.height())
        topregion = QRectF(hpadding, bounds.y(), bounds.width()*0.6, vpadding)
        botregion = QRectF(hpadding, bounds.height() -
                           vpadding, bounds.width()*0.6, vpadding)

        if leftregion.contains(inpos) or rightregion.contains(inpos) or topregion.contains(inpos) or botregion.contains(inpos):

            targetlist = None
            vertical = False

            if leftregion.contains(inpos):
                targetlist = self.leftTerminals
            elif rightregion.contains(inpos):
                targetlist = self.rightTerminals
            elif topregion.contains(inpos):
                targetlist = self.topTerminals
                vertical = True
            elif botregion.contains(inpos):
                targetlist = self.bottomTerminals
                vertical = True
            return (targetlist, vertical)
        else:
            return None

    def paint(self, painter: QPainter, option, widget):
        super().paint(painter, option, widget)
        # Calculate horizontal Terminal offsets
        horizontalUnitSize = Socket.PILLSIZE.height() + DesignNode.MINIMUMSOCKETPADDING*2
        # Calculate vertical terminal offsets
        verticalUnitSize = Socket.PILLSIZE.width() + DesignNode.MINIMUMSOCKETPADDING

        # Center Proxy
        midpoint = QPointF(self.boundingRect().width()/2,
                           self.boundingRect().height()/2)
        offset = QPointF(self.proxy.boundingRect().width()/2,
                         self.proxy.boundingRect().height()/2)
        self.proxy.setPos(midpoint-offset)

        # Arrange terminals
        centeringHPoint = self.boundingRect().height()/2
        centeringVPoint = self.boundingRect().width()/2

        leftOffset = centeringHPoint - \
            ((verticalUnitSize * len(self.leftTerminals))/2) + \
            Socket.PILLSIZE.height()*2
        rightOffset = centeringHPoint - \
            ((verticalUnitSize * len(self.rightTerminals))/2) + \
            Socket.PILLSIZE.height()*2
        topOffset = centeringVPoint - \
            ((horizontalUnitSize * len(self.topTerminals))/2) + \
            Socket.PILLSIZE.width()/2
        bottomOffset = centeringVPoint - \
            ((horizontalUnitSize * len(self.bottomTerminals))/2) + \
            Socket.PILLSIZE.width()/2

        for count, socket in enumerate(self.leftTerminals):
            socket.setPos(-Socket.PILLSIZE.width()/2,
                          leftOffset+count*verticalUnitSize)

        for count, socket in enumerate(self.rightTerminals):
            socket.setPos(self.boundingRect().width(
            )-Socket.PILLSIZE.width()/2, rightOffset+count*verticalUnitSize)

        for count, socket in enumerate(self.topTerminals):
            socket.setPos(topOffset+count*horizontalUnitSize, -
                          Socket.PILLSIZE.height()*1.8)

        for count, socket in enumerate(self.bottomTerminals):
            socket.setPos(bottomOffset+count*horizontalUnitSize, self.boundingRect(
            ).height()-Socket.PILLSIZE.height()*1.8)  # 1.8 fudge factor?


class RequirementNode(NodeBase):
    def __init__(self, RL: RequirementElement, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.ownedRL = RL
        self.proxy = QGraphicsProxyWidget(self)
        self.lbl = DisplayItem(self.ownedRL)
        self.proxy.setWidget(self.lbl)

        self.topSocket = Socket(self, None, vertical=True)
        self.bottomSocket = Socket(self, None, vertical=True)



    def boundingRect(self):
        proxysize = self.proxy.size()
        return QRectF(0, 0, proxysize.width(), proxysize.height())

    def paint(self, painter, option, widget):
        super().paint(painter, option, widget)
        bbox = self.boundingRect()
        # (self.boundingRect().width()/2)-(Socket.PILLSIZE.width()/2)
        self.bottomSocket.setPos(
            (bbox.width()/2)-(Socket.PILLSIZE.width()/2), bbox.height())
        self.topSocket.setPos(
            (bbox.width()/2)-(Socket.PILLSIZE.width()/2), -Socket.PILLSIZE.width())

    def itemChange(self, change: QtWidgets.QGraphicsItem.GraphicsItemChange, value: typing.Any) -> typing.Any:
        if change == QGraphicsItem.ItemPositionChange:
            if self.bottomSocket.trace != None:
                self.bottomSocket.trace.moved = True
                self.scene().views()[0].viewport().repaint()
                self.bottomSocket.trace.moved = False
            if self.topSocket.trace != None:
                self.topSocket.trace.moved = True
                self.scene().views()[0].viewport().repaint()
                self.topSocket.trace.moved = False

        return super().itemChange(change, value)


class ExternalConnections(DesignNode):
    def __init__(self, bbox, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.boundingbox = bbox

    def boundingRect(self):
        return QRectF(0, 0, self.boundingbox.width(), self.boundingbox.height())

    def updatePos(self):
        self.setPos(self.boundingbox.x(), self.boundingbox.y())


class Socket(QGraphicsItem):

    PILLSIZE = QRectF(0, 0, 25, 6)

    def __init__(self, parent, dl: DesignElement, vertical=False, preview=False) -> None:

        super(Socket, self).__init__(parent=parent)
        self.parentNode = parent
        self.ownedDL = dl
        self.trace = None
        self.setZValue(100)
        self.traces = []
        self.vertical = vertical
        self.setFlags(self.flags() | QGraphicsItem.GraphicsItemFlag.ItemIsSelectable |
                      QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges)
        self.preview = preview
        self.spriteOpacity = 255/2 if self.preview else 255


    def paint(self, painter, option, widget):

        pos = Socket.PILLSIZE.getCoords()
        if self.vertical:
            pos = (pos[0], pos[1], pos[3], pos[2])
        pen = painter.pen()
        pen.setCapStyle(Qt.RoundCap)
        pen.setWidth(Socket.PILLSIZE.height())

        socketcolor = configuration.SocketColor.color()
        socketcolor.setAlpha(self.spriteOpacity)
        pen.setColor(socketcolor)
        painter.setPen(pen)
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

        if self.preview:

            if isinstance(self.parentItem(), DesignNode):
                socket = self.parentItem().materializePreview(
                    self.mapToItem(self.parentItem(), event.pos()))
                for item in self.scene().selectedItems():
                    item.setSelected(False)
                socket.setSelected(True)

        else:
            try:
                if objects.qapp.keyboardModifiers() == Qt.ControlModifier:
                    self.trace = ArrowItem(source=self.scene().selectedItems()[
                                             0], destination=self, parent=None)
                    self.trace.setZValue(0)
                    self.trace.setPos(self.scenePos())
                    self.scene().addItem(self.trace)
                    self.setSelected(False)

                elif objects.qapp.keyboardModifiers() == Qt.AltModifier:
                    self.scene().removeItem(self.trace)
                    self.trace = None
                else:
                    for item in self.scene().selectedItems():
                        item.setSelected(False)
                    self.setSelected(True)
            except IndexError:
                pass

    def mouseReleaseEvent(self, event):
        # Todo: cleanup

        # Branch 1. Does trace exist and self is not preview
        # Step 1. Move trace to back

        # Branch 2. Determine if there is a socket at location that is not self and is not preview
        # Step 1. Connect to socket
        # Step 2. Bring trace to front
        # Elif there is a DL at location
        # Step 1. Determine which side was dropped
        # Step 2. Materialize preview
        # Step 3. Connect to socket
        # Step 4. Bring trace to front
        # Else:
        # Step 1. Invalid drop placement, destroy trace
        # Else:
        # Pass

        if self.trace != None and not self.preview:
            self.trace.setZValue(-10)
            item = self.scene().itemAt(event.scenePos(), QTransform())

            if isinstance(item, Socket) and item != self and not item.preview:
                self.trace._destinationPoint = item
                item.trace = self.trace
                self.trace.setZValue(10)
                self.trace.moved = False

            elif isinstance(item, DesignNode):
                socket = item.materializePreview(
                    self.mapToItem(item, event.pos()))
                self.trace._destinationPoint = socket
                socket.trace = self.trace
                self.trace.setZValue(10)
                self.trace.moved = False
            else:
                self.scene().removeItem(self.trace)
                self.trace = None

    def mouseMoveEvent(self, event: QtWidgets.QGraphicsSceneMouseEvent) -> None:
        if isinstance(self.trace, NoneType):
            self.trace = ArrowItem(
                source=self, destination=event.pos(), parent=None)
            self.trace.setZValue(0)
            self.trace.setPos(self.scenePos())
            self.scene().addItem(self.trace)
            self.setSelected(False)
        self.trace.prepareGeometryChange()
        self.trace._destinationPoint = event.pos()

    def anchorPoint(self) -> QPointF:
        boundingrect = self.boundingRect()
        return QPointF((boundingrect.width() / 2), (boundingrect.height() / 2))


class OldArrowItem(QGraphicsLineItem):
    ''' ArrowItem represents connections between items '''

    def __init__(self, startItem, endItem, parent=None):
        """
        ArrowItem represents a connection between two items
        @params:
            Set style to 2 for a dotted line
        """

        super(OldArrowItem, self).__init__() if isinstance(
            parent, NoneType) else super(OldArrowItem, self).__init__(parent)
        # self.setZValue(1)

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

    def setColor(self, color: QColor):
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
        line = QtCore.QLineF(self.mapFromItem(
            self.myStartItem, 0, self.myStartItem.rect.y()), self.mapFromItem(self.myEndItem, 0, 0))
        self.setLine(line)

    def hoverEnterEvent(self, event: 'QGraphicsSceneHoverEvent') -> None:
        self.myColor = QColor(0, 255, 0)
        return super().hoverEnterEvent(event)

    def hoverLeaveEvent(self, event: 'QGraphicsSceneHoverEvent') -> None:
        self.myColor = QColor(random.randint(
            0, 5), random.randint(0, 5), random.randint(0, 5))
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

        # startpos = QPointF(myStartItem.x() + (self.myStartItem.boundingRect().x() / 2), myStartItem.y() + self.myStartItem.boundingRect().y())

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


class ArrowItem(QtWidgets.QGraphicsPathItem):
    def __init__(self, source=None, destination=None, *args, **kwargs):
        super(ArrowItem, self).__init__(*args, **kwargs)

        self._sourcePoint = source
        self._destinationPoint = destination

        self._arrow_height = 5
        self._arrow_width = 4
        self.moved = True
        self.nodePath = []
        self.worker : PathingRunnable = None
        self.threadpool = QThreadPool()

    def setSource(self, point: QtCore.QPointF):
        self._sourcePoint = point

    def setDestination(self, point: QtCore.QPointF):
        self._destinationPoint = point

    def itemChange(self, change: QtWidgets.QGraphicsItem.GraphicsItemChange, value: typing.Any) -> typing.Any:
        if change == QGraphicsItem.ItemPositionChange:
            self.moved = True

        return super().itemChange(change, value)

    def directPath(self):
        ignoreditems = []
        if isinstance(self._sourcePoint, QGraphicsItem):
            s = self.mapFromParent(self._sourcePoint.scenePos())
            ignoreditems.append(self._sourcePoint)
        else:
            s = self._sourcePoint
        if isinstance(self._destinationPoint, QGraphicsItem):
            d = self.mapFromParent(self._destinationPoint.scenePos())
            ignoreditems.append(self._destinationPoint)

        else:
            d = self._destinationPoint

        s.setY(s.y()+Socket.PILLSIZE.width())

        mid_x = s.x() + ((d.x() - s.x()) * 0.2)

        if self.moved:
            searchbounds : QRectF = buildSearchBounds(self.mapToScene(s), self.mapToScene(d), self.scene())
            #self.nodePath = pathfind( self.mapToScene(s), self.mapToScene(d), searchbounds, generateMatrixFromScene(searchbounds, self.scene()))
            if self.worker != None:
                self.worker.terminate()
            self.worker = PathingThread(self.updatePath, self.mapToScene(s), self.mapToScene(d), searchbounds, generateMatrixFromScene(searchbounds, self.scene())) # Any other args, kwargs are passed to the run function
            
            

        path = QtGui.QPainterPath(s)

        for coord in self.nodePath:
            p = self.mapFromScene(QPointF(coord[0], coord[1]))
            path.lineTo(p)
        path.lineTo(d)

        '''path = QtGui.QPainterPath(QtCore.QPointF(s.x(), s.y()))
        path.lineTo(mid_x, s.y())
        path.lineTo(mid_x, d.y())
        path.lineTo(d.x(), d.y())'''

        return path
    
    def updatePath(self, nodes):
        self.nodePath = nodes

    # calculates the point where the arrow should be drawn
    def arrowCalc(self, arrow_pos, start_point=None, end_point=None):
        if isinstance(self._sourcePoint, QGraphicsItem):
            start_point = self.mapFromParent(
                self._sourcePoint.scenePos()) - self._sourcePoint.anchorPoint()
        else:
            start_point = self._sourcePoint
        if isinstance(self._destinationPoint, QGraphicsItem):
            end_point = self.mapFromParent(
                self._destinationPoint.scenePos()) + self._sourcePoint.anchorPoint()

        else:
            end_point = self._destinationPoint
        try:
            startPoint, endPoint = start_point, end_point

            if start_point is None:
                startPoint = self._sourcePoint

            if endPoint is None:
                endPoint = self._destinationPoint

            dx, dy = arrow_pos.x() - endPoint.x(), arrow_pos.y() - endPoint.y()

            leng = math.sqrt(dx ** 2 + dy ** 2)
            normX, normY = dx / leng, dy / leng  # normalize

            # perpendicular vector
            perpX = -normY
            perpY = normX

            leftX = endPoint.x() + self._arrow_height * normX + self._arrow_width * perpX
            leftY = endPoint.y() + self._arrow_height * normY + self._arrow_width * perpY

            rightX = endPoint.x() + self._arrow_height * normX - self._arrow_width * perpX
            rightY = endPoint.y() + self._arrow_height * normY - self._arrow_width * perpY

            point2 = QtCore.QPointF(leftX, leftY)
            point3 = QtCore.QPointF(rightX, rightY)

            return QtGui.QPolygonF([point2, endPoint, point3])

        except (ZeroDivisionError, Exception):
            return None

    def paint(self, painter: QtGui.QPainter, option, widget=None) -> None:

        painter.setRenderHint(QPainter.Antialiasing)

        pen = painter.pen()
        pen.setWidth(6)
        painter.setPen(pen)
        painter.setBrush(QtCore.Qt.NoBrush)

        path = self.directPath()
        painter.drawPath(path)
        self.setPath(path)

        # change path.PointAtPercent() value to move arrow on the line
        triangle_source = self.arrowCalc(path.pointAtPercent(0.5))

        if triangle_source is not None:
            painter.drawPolyline(triangle_source)

class PathingRunnable(QRunnable):
    def __init__(self, fn, a: QPointF, b: QPointF, searchbounds, mat):
        super().__init__()
        self.a = a
        self.b = b
        self.searchbounds = searchbounds
        self.mat = mat
        self.fn = fn

    @Slot()
    def run(self):
        self.fn(pathfind(self.a, self.b, self.searchbounds, self.mat))

class PathingThread(QThread):
    def __init__(self, fn, a: QPointF, b: QPointF, searchbounds, mat):
        super().__init__()
        self.a = a
        self.b = b
        self.searchbounds = searchbounds
        self.mat = mat
        self.fn = fn
        self.setTerminationEnabled(False)
        self.run()
    @Slot()
    def run(self):
        self.fn(pathfind(self.a, self.b, self.searchbounds, self.mat))


def buildSearchBounds(a: QPointF, b: QPointF, scene: QGraphicsScene):
    topleft = a if a.x() <= b.x() and a.y() <= b.y() else b
    bottomright = b if a.x() <= b.x() and a.y() <= b.y() else a
    
    #print(f'Original: {view.mapToScene(view.viewport().geometry()).boundingRect()}, New: {QRectF(topleft, bottomright)}')

    if a.x() < b.x() and a.y() < b.y():
        #print("Bottom Right")
        topleft = a
        bottomright = b
    elif a.x() < b.x() and a.y() > b.y():
        #print("Top Right")
        topleft = QPointF(a.x(), b.y())
        bottomright = QPointF(b.x(), a.y())
    elif a.x() > b.x() and a.y() < b.y():
        #print("Bottom Left")
        topleft = QPointF(b.x(), a.y())
        bottomright = QPointF(a.x(), b.y())
    elif a.x() > b.x() and a.y() > b.y():
        #print("Top Left")
        topleft = b
        bottomright = a

    searchbounds = QRectF(topleft, bottomright)
    for item in scene.items(searchbounds):
        if not isinstance(item, ArrowItem):
            rect = item.sceneBoundingRect()
            rect.adjust(-GRIDSIZE[0], -GRIDSIZE[1], GRIDSIZE[0], GRIDSIZE[1])
            searchbounds |= rect
    return searchbounds

def generateMatrixFromScene(searchbounds, scene):
    mat = [[1 for _ in range(math.ceil(searchbounds.width() / GRIDSIZE[0]))]
           for _ in range(math.ceil(searchbounds.height() / GRIDSIZE[1]))]
    for c2 in range(len(mat)):
        for c1 in range(len(mat[0])):
            x = searchbounds.x() + (GRIDSIZE[0] * c1)
            y = searchbounds.y() + (GRIDSIZE[0] * c2)
            t = scene.itemAt(QPointF(float(x), float(y)), QTransform())
            items = scene.items(QPointF(float(x), float(y)))
            types = [type(item) for item in items]
            if QGraphicsProxyWidget in types:
                mat[c2][c1] = -1
            else:
                mat[c2][c1] = 1
    return mat

def pathfind(a: QPointF, b: QPointF, searchbounds, mat):
    if searchbounds.width() == 0:
        searchbounds.setWidth(10) 
        searchbounds.setX(searchbounds.x()-5)
    if searchbounds.height() == 0:
        searchbounds.setHeight(10) 
        searchbounds.setY(searchbounds.y()-5)
    grid = Grid(matrix=mat)

    gridOffset = (-(GRIDSIZE[0]/2), -(GRIDSIZE[1]/4))

    xoffset = snapToGrid(searchbounds.width(), GRIDSIZE[0])
    yoffset = snapToGrid(searchbounds.height(), GRIDSIZE[1])

    pointACoords = (math.floor((a.x()-searchbounds.x()) /
                    GRIDSIZE[0]), math.floor((a.y()-searchbounds.y())/GRIDSIZE[1]))
    pointBCoords = (math.floor((b.x()-searchbounds.x()) /
                    GRIDSIZE[0]), math.floor((b.y()-searchbounds.y())/GRIDSIZE[1]))

    if a.x() < b.x() and a.y() < b.y():
        start = grid.node(0, 0)
        end = grid.node(len(mat[0])-1, len(mat)-1)

    elif a.x() < b.x() and a.y() > b.y():
        start = grid.node(0, len(mat)-1)
        end = grid.node(len(mat[0])-1, 0)

    elif a.x() > b.x() and a.y() < b.y():
        start = grid.node(len(mat[0])-1, 0)
        end = grid.node(0, len(mat)-1)

    elif a.x() > b.x() and a.y() > b.y():
        start = grid.node(len(mat[0])-1, len(mat)-1)
        end = grid.node(0, 0)
        
    try:
        start = grid.node(pointACoords[0], pointACoords[1])
    except IndexError:
        pointACoords = (math.floor((a.x()-searchbounds.x()) /
                        GRIDSIZE[0])-1, math.floor((a.y()-searchbounds.y())/GRIDSIZE[1]))
        start = grid.node(pointACoords[0], pointACoords[1])
    try:
        end = grid.node(pointBCoords[0], pointBCoords[1])
    except IndexError:
        pointBCoords = (math.floor((b.x()-searchbounds.x()) /
                    GRIDSIZE[0])-1, math.floor((b.y()-searchbounds.y())/GRIDSIZE[1])-1)
        end = grid.node(pointBCoords[0], pointBCoords[1])

    finder = DijkstraFinder(
        diagonal_movement=DiagonalMovement.only_when_no_obstacle)
    path, runs = finder.find_path(start, end, grid)
    translatedpath = []
    for coordinate in path:
        mat[coordinate[1]][coordinate[0]] = 'x'
        p = (coordinate[0]*GRIDSIZE[0]+gridOffset[0]+searchbounds.x()+Socket.PILLSIZE.width(),
             coordinate[1]*GRIDSIZE[1]+gridOffset[1]+searchbounds.y()+Socket.PILLSIZE.height())
        translatedpath.append(p)
    return translatedpath

