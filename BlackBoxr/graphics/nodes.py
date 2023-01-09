import copy
from enum import Enum
import inspect
import math
import random
import sys
import threading
import time
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
from BlackBoxr import utilities

from BlackBoxr.mainwindow.widgets import DisplayItem, EditableLabel, ExpandableLineEdit, Label
from BlackBoxr.misc import configuration, objects
from BlackBoxr.misc.Datatypes import DesignElement, MoveCommand, NameEdit, RequirementElement
from BlackBoxr.utilities import closestPoint, printMatrix, snapToGrid
from pathfinding.core.diagonal_movement import DiagonalMovement
from pathfinding.core.grid import Grid
from pathfinding.finder.a_star import AStarFinder
from pathfinding.finder.dijkstra import DijkstraFinder

import qdarktheme

import asyncio

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

        self.ownedRL.subscribe(self.onRLUpdate)

        self.proxy = QGraphicsProxyWidget(self)
        self.lbl = DisplayItem(self.ownedRL)
        self.proxy.setWidget(self.lbl)
        
        
        self.topSocket = Socket(self, None, vertical=True, type=Socket.IOTYPE.IN)
        self.bottomSocket = Socket(self, None, vertical=True, type=Socket.IOTYPE.OUT)

        self.moveFinishedNotifier = None

    def onRLUpdate(self):
        self.lbl

    def boundingRect(self):
        proxysize = self.proxy.size()
        return QRectF(0, 0, proxysize.width(), proxysize.height())

    def paint(self, painter : QPainter, option, widget):
        super().paint(painter, option, widget)
        bbox = self.boundingRect()
        # (self.boundingRect().width()/2)-(Socket.PILLSIZE.width()/2)

        painter.setBrush(configuration.NodeZoomedColor.color())
        pen = painter.pen()
        pen.setColor(configuration.NodeZoomedColor.color())
        pen.setCapStyle(Qt.RoundCap)
        painter.setPen(pen)
        font = QFont('arial', 24)
        font.setHintingPreference(QFont.PreferNoHinting)
        painter.setFont(font)
        painter.drawText(self.boundingRect(), Qt.AlignCenter ,self.ownedRL.public['Requirement'])

        self.bottomSocket.setPos(
            (bbox.width()/2)-(Socket.PILLSIZE.width()/2), bbox.height())
        self.topSocket.setPos(
            (bbox.width()/2)-(Socket.PILLSIZE.width()/2), -Socket.PILLSIZE.width())
        

    def itemChange(self, change: QtWidgets.QGraphicsItem.GraphicsItemChange, value: typing.Any) -> typing.Any:
        if change == QGraphicsItem.ItemPositionChange:
            self.bottomSocket.flagForRepaint(True)
            self.topSocket.flagForRepaint(True)
            self.scene().views()[0].viewport().repaint()
            self.bottomSocket.flagForRepaint(False)
            self.topSocket.flagForRepaint(False)

        return super().itemChange(change, value)

    def mouseDoubleClickEvent(self, event: QtWidgets.QGraphicsSceneMouseEvent) -> None:
        print(self.ownedRL.toDict())
        return super().mouseDoubleClickEvent(event)

    def getDownstreamItems(self):
        return [trace._destinationPoint.parentNode for trace in self.bottomSocket.traces]

    def repaintTraces(self):
        self.topSocket.flagForRepaint()
        self.bottomSocket.flagForRepaint()
        for trace in self.bottomSocket.traces + self.topSocket.traces:
            trace.directPath()
            trace.update()
            trace.show()
        if self.moveFinishedNotifier != None:
            self.moveFinishedNotifier()
        self.scene().update()

    def moveTo(self, pos : QPointF):
        self.anim = QVariantAnimation()
        self.anim.setDuration(500)
        self.anim.setEasingCurve(QEasingCurve.OutQuad)
        self.anim.setStartValue(self.pos())
        self.anim.setEndValue(pos)
        self.anim.valueChanged.connect(self._moveTick)
        self.anim.finished.connect(self.repaintTraces)
        self.anim.start()
        

        

    def _moveTick(self, pos):
        self.prepareGeometryChange()
        for trace in self.bottomSocket.traces + self.topSocket.traces:
            trace.hide()
        self.setPos(pos)
        self.update()

        self.hoverEnterEvent(None)
        self.hoverLeaveEvent(None)

    def connectDownstream(self, item):
        if isinstance(item, RequirementNode):
            self.bottomSocket.connectTo(item.topSocket)

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

    class IOTYPE(Enum):
        IN = 0
        OUT = 1
        INOUT = 2

    def __init__(self, parent, dl: DesignElement, vertical=False, preview=False, type=IOTYPE.INOUT) -> None:

        super(Socket, self).__init__(parent=parent)
        self.parentNode = parent
        self.ownedDL = dl
        self.trace = None
        self.setZValue(100)
        self.traces : list[ArrowItem] = []
        self.vertical = vertical
        self.setFlags(self.flags() | QGraphicsItem.GraphicsItemFlag.ItemIsSelectable |
                      QGraphicsItem.GraphicsItemFlag.ItemSendsGeometryChanges)
        self.preview = preview
        self.spriteOpacity = 255/2 if self.preview else 255
        self.socketType = type


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

        for trace in self.traces:
            trace.setPos(self.scenePos())

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
                selectedItem = self.scene().selectedItems()[0]
                if objects.qapp.keyboardModifiers() == Qt.ControlModifier and isinstance(selectedItem, Socket):
                    self.trace = ArrowItem(source=selectedItem, destination=self, parent=None)
                    self.connectTrace(self.trace)
                    self.trace.setZValue(0)
                    self.trace.setPos(self.scenePos())
                    self.scene().addItem(self.trace)
                    self.setSelected(False)
                    if isinstance(self.parentNode, RequirementNode) and isinstance(selectedItem.parentNode, RequirementNode):
                        selectedItem.parentNode.ownedRL.addDownstream(self.parentNode.ownedRL)
                    self.trace = None
                elif objects.qapp.keyboardModifiers() == Qt.AltModifier:
                    self.scene().removeItem(self.trace)
                    self.disconnectAll()
                    self.trace = None
                else:
                    for item in self.scene().selectedItems():
                        item.setSelected(False)
                    self.setSelected(True)
            except IndexError:
                self.setSelected(True)

    def connectTo(self, targetSocket):
        if isinstance(targetSocket, Socket) and isinstance(self.parentNode, RequirementNode):
            t = ArrowItem(source=self, destination=targetSocket, parent=None)
            self.scene().addItem(t)
            self.connectTrace(t)
            self.parentNode.ownedRL.addDownstream(targetSocket.parentNode.ownedRL)

    def connectTrace(self, trace):
            self.traces.append(trace)

    def disconnectTrace(self, trace):
        self.scene().removeItem(trace)
        if trace in self.traces:
            trace : ArrowItem = trace
            if isinstance(trace._sourcePoint.parentNode, RequirementNode):
                trace._sourcePoint.parentNode.ownedRL.removeFromStreams(trace._destinationPoint.parentNode.ownedRL)
            self.traces.remove(trace)
    
    def disconnectAll(self):
        for trace in self.traces:
            self.disconnectTrace(trace)

    def flagForRepaint(self, shouldrepaint = True):
        for trace in self.traces:
            trace.moved = shouldrepaint
    
    def mouseReleaseEvent(self, event):
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

            if isinstance(item, Socket) and item != self and not item.preview and self.compatibleSockets(self, item):
                self.trace._destinationPoint = item
                item.connectTrace(self.trace)
                self.connectTrace(self.trace)
                self.trace.setZValue(10)
                self.trace.moved = False

                if isinstance(self.parentNode, RequirementNode):
                    self.parentNode.ownedRL.addDownstream(item.parentNode.ownedRL)

            elif isinstance(item, DesignNode):
                socket = item.materializePreview(
                    self.mapToItem(item, event.pos()))
                self.trace._destinationPoint = socket
                socket.connectTrace(self.trace)
                self.connectTrace(self.trace)
                self.trace.setZValue(10)
                self.trace.moved = False
                '''elif isinstance(item, RequirementNode) or isinstance(item, QGraphicsProxyWidget):
                if self.trace._sourcePoint.socketType == Socket.IOTYPE.OUT:
                    if isinstance(item, QGraphicsProxyWidget):
                        socket = item.parent().topSocket
                    else:
                        socket = item.topSocket
                    self.trace._destinationPoint = socket
                    socket.connectTrace(self.trace)
                    self.connectTrace(self.trace)
                    self.trace.setZValue(10)
                    self.trace.moved = False
                elif self.trace._sourcePoint.socketType == Socket.IOTYPE.IN:
                    if isinstance(item, QGraphicsProxyWidget):
                        socket = item.parent().bottomSocket
                    else:
                        socket = item.bottomSocket
                    self.trace._sourcePoint = socket
                    self.trace._destinationPoint = self
                    socket.connectTrace(self.trace)
                    self.connectTrace(self.trace)
                    self.trace.setZValue(10)
                    self.trace.moved = False'''
            else:
                self.scene().removeItem(self.trace)
            self.trace = None

    def compatibleSockets(self, sourceSocket, destinationSocket):
        sourceSocket : Socket
        destinationSocket : Socket

        RuleA = (sourceSocket.socketType == Socket.IOTYPE.OUT and destinationSocket.socketType == Socket.IOTYPE.IN)
        RuleB = (sourceSocket.socketType == Socket.IOTYPE.INOUT and destinationSocket.socketType == Socket.IOTYPE.INOUT)
        RuleC = (sourceSocket.socketType == Socket.IOTYPE.OUT and destinationSocket.socketType == Socket.IOTYPE.INOUT)
        RuleD = (sourceSocket.socketType == Socket.IOTYPE.INOUT and destinationSocket.socketType == Socket.IOTYPE.IN)

        return RuleA or RuleB or RuleC or RuleD

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


    def mouseDoubleClickEvent(self, event: QtWidgets.QGraphicsSceneMouseEvent) -> None:
        print()
        if isinstance(self._sourcePoint, QGraphicsItem):
            s = self.mapFromParent(self._sourcePoint.scenePos())
        else:
            s = self._sourcePoint
        if isinstance(self._destinationPoint, QGraphicsItem):
            d = self.mapFromParent(self._destinationPoint.scenePos())
        else:
            d = self._destinationPoint
        print(self.nodePath)
        self.launchpather()
        self.scene().views()[0].viewport().repaint()
        print(self.scenePos())
        print(s, d)
        print(self.nodePath)
        return super().mouseDoubleClickEvent(event)

    def setSource(self, point: QtCore.QPointF):
        self._sourcePoint = point

    def setDestination(self, point: QtCore.QPointF):
        self._destinationPoint = point

    def itemChange(self, change: QtWidgets.QGraphicsItem.GraphicsItemChange, value: typing.Any) -> typing.Any:
        if change == QGraphicsItem.ItemPositionChange:
            self.moved = True

        return super().itemChange(change, value)

    def directPath(self):
        if isinstance(self._sourcePoint, QGraphicsItem):
            s = self.mapFromParent(self._sourcePoint.scenePos())
        else:
            s = self._sourcePoint
        if isinstance(self._destinationPoint, QGraphicsItem):
            d = self.mapFromParent(self._destinationPoint.scenePos())
        else:
            d = self._destinationPoint

        path = QtGui.QPainterPath(s)
        for percentage in (x * 0.1 for x in range(0, 10)):
            p = utilities.snapToGrid(utilities.lerp(s, d, percentage), GRIDSIZE[0]*2)
            path.lineTo(p)
        path.lineTo(d)
        return path  

    def smartPath(self):
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

        '''if self.moved:
            print(f'{self} refreshing path')
            searchbounds : QRectF = buildSearchBounds(self.mapToScene(s), self.mapToScene(d), self.scene())
            if self.worker != None:
                self.worker.terminate()

            mat = generateMatrixFromScene(searchbounds, self.scene(), [self])
            #self.nodePath = pathfind(self.mapToScene(s), self.mapToScene(d), searchbounds, mat)
            self.worker = PathingThread(self.updatePath, self.mapToScene(s), self.mapToScene(d), searchbounds, mat) # Any other args, kwargs are passed to the run function
            self.worker.start()'''
            
        #self.launchpather()
        asyncio.run(self.pathAllocator())


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
    
    async def pathAllocator(self):
        if self.worker != None:
            self.worker.cancel()
        self.worker = asyncio.create_task(self.launchpather())

    async def launchpather(self):
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

        searchbounds : QRectF = buildSearchBounds(self.mapToScene(s), self.mapToScene(d), self.scene())
        '''if self.worker != None:
            self.worker.terminate()'''
        mat = generateMatrixFromScene(searchbounds, self.scene(), [self])
        self.nodePath = pathfind(self.mapToScene(s), self.mapToScene(d), searchbounds, mat)
        '''self.worker = PathingThread(self.updatePath, self.mapToScene(s), self.mapToScene(d), searchbounds, mat) # Any other args, kwargs are passed to the run function
        self.worker.start()'''
    
    def updatePath(self, nodes):
        if nodes != None:
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
        #self.smartPath()
        painter.drawPath(path)
        self.setPath(path)

        # change path.PointAtPercent() value to move arrow on the line
        triangle_source = self.arrowCalc(path.pointAtPercent(0.5))

        if triangle_source is not None:
            painter.drawPolyline(triangle_source)

    def refresh(self):
        self.directPath()
        #self.smartPath()
        self.update()

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
        self.setTerminationEnabled(True)
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

def gridPointsFromPath(path : QGraphicsPathItem):
    qpath = path.path()
    coords = []
    for index in range(qpath.elementCount()):
        point = QPointF(qpath.elementAt(index))
        coords.append((max(0, math.floor(point.x()/GRIDSIZE[0])-1), max(0, math.floor(point.y()/GRIDSIZE[1])-1)))
    return coords

def generateMatrixFromScene(searchbounds : QRectF, scene: QGraphicsScene, ignoreditems = []):
    mat = [[1 for _ in range(math.ceil(searchbounds.width() / GRIDSIZE[0])+1)]
           for _ in range(math.ceil(searchbounds.height() / GRIDSIZE[1])+1)]

    detected = scene.items(searchbounds)
    for item in detected:
        if item not in ignoreditems:
            # Rectangular Items
            if type(item) not in [QGraphicsProxyWidget, Socket, ArrowItem]:
                itemrect = item.sceneBoundingRect()

                # Cutoff off screen
                itemrect.translate(-searchbounds.x(), -searchbounds.y())
                itemrect.setWidth(itemrect.width()+min(0, itemrect.x()))
                itemrect.setX(max(itemrect.x(), 0))
                itemrect.setHeight(itemrect.height()+min(0, itemrect.y()))
                itemrect.setY(max(itemrect.y(), 0))
                
                # Width of item in cells
                itemw = math.ceil(itemrect.width()/GRIDSIZE[0])-1
                # Height 
                itemh = math.ceil(itemrect.height()/GRIDSIZE[1])-1
                # Column (x) base
                col = math.ceil((itemrect.x())/GRIDSIZE[0])
                # Row (y) base
                row = math.ceil((itemrect.y())/GRIDSIZE[1])
                
                colbase = max(col, 0)
                rowbase = max(row, 0)

                for colit in range(colbase, colbase+itemw):
                    for rowit in range(rowbase, rowbase+itemh):
                        try:
                            mat[rowit][colit] = 3
                        except IndexError as e:
                            pass
            elif isinstance(item, QGraphicsPathItem):
                coords = gridPointsFromPath(item)
                for coord in coords:
                    try:
                        mat[coord[1]][coord[0]] = 2
                    except IndexError: pass
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


    pointACoords = (math.floor((a.x()-searchbounds.x()) /
                    GRIDSIZE[0]), math.floor((a.y()-searchbounds.y())/GRIDSIZE[1]))
    pointBCoords = (math.floor((b.x()-searchbounds.x()) /
                    GRIDSIZE[0]), math.floor((b.y()-searchbounds.y())/GRIDSIZE[1]))
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

    #print(grid.grid_str(path=path, start=start, end=end))

    for coordinate in path:
        p = (coordinate[0]*GRIDSIZE[0]+gridOffset[0]+searchbounds.x()+Socket.PILLSIZE.width(),
            coordinate[1]*GRIDSIZE[1]+gridOffset[1]+searchbounds.y()+Socket.PILLSIZE.height())
        translatedpath.append(p)
    return translatedpath