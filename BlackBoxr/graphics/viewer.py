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
from PySide6.QtCore import Qt, QRectF, QRect, QPointF, QVariantAnimation, QEasingCurve, QLineF, QPoint, Signal
from PySide6 import QtGui
from PySide6.QtGui import QTransform, QPixmap, QAction, QPainter, QColor, QPen, QBrush, QCursor, QPainterPath, QFont, QFontMetrics, QUndoStack, QKeySequence, QWheelEvent

from BlackBoxr.misc import configuration, objects
from BlackBoxr.misc.Datatypes import MoveCommand, NameEdit
from BlackBoxr.utilities import closestPoint, printMatrix, transpose

from pathfinding.core.diagonal_movement import DiagonalMovement
from pathfinding.core.grid import Grid
from pathfinding.finder.a_star import AStarFinder

import igraph as ig
from igraph import Graph, EdgeSeq, plot

GRIDSIZE = (25, 25)
ENDOFFSET = -QPointF(25, 25)


class DiagramViewer(QGraphicsView):

    newVisibleArea = Signal(QRectF)

    def __init__(self, scene: QGraphicsScene):
        super(DiagramViewer, self).__init__(scene)
        self._scene = scene
        self.startPos = None
        self.setAcceptDrops(True)

        self.setDragMode(QGraphicsView.DragMode.RubberBandDrag)
        self.setViewportUpdateMode(QGraphicsView.FullViewportUpdate)

    ''' Item Focusing '''

    def moveTo(self, pos: QPointF):
        self.anim = QVariantAnimation()
        self.anim.setDuration(500)
        self.anim.setEasingCurve(QEasingCurve.InOutQuart)
        self.anim.setStartValue(self.mapToScene(self.rect().center()))
        self.anim.setEndValue(QPointF(pos.x(), pos.y()))
        self.anim.valueChanged.connect(self._moveTick)
        self.anim.finished.connect(self.repaintTraces)
        self.anim.start()

    def _moveTick(self, pos):
        self.centerOn(pos)

    def repaintTraces(self):
        self._scene.requestRepaintTraces()
        self._scene.update()
        self.update()

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

    def wheelEvent(self, event: QWheelEvent, norep=False):

        if Qt.KeyboardModifier.ControlModifier == event.modifiers():

            self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
            if event.angleDelta().y() > 0:
                self.scale(1.1, 1.1)
            else:
                self.scale(0.9, 0.9)
        else:
            super(DiagramViewer, self).wheelEvent(event)
        self.newVisibleArea.emit(self.mapToScene(
            self.viewport().geometry()).boundingRect())
        self._scene.update()

    def keyPressEvent(self, event: QtGui.QKeyEvent) -> None:
        if objects.qapp.keyboardModifiers() == (Qt.ControlModifier | Qt.AltModifier) and event.key() == Qt.Key_F:
            self._scene.formatRequirements()
        return super().keyPressEvent(event)


class DiagramScene(QGraphicsScene):

    def __init__(self):
        super().__init__()

        self._dragged = False
        # self.setBackgroundBrush(configuration.GridColor)

    def set_viewer(self, viewer):
        self.viewer = viewer

    def drawBackground(self, painter: QtGui.QPainter, rect: typing.Union[QtCore.QRectF, QtCore.QRect]) -> None:
        left = int(rect.left()) - (int(rect.left()) % GRIDSIZE[0])
        top = int(rect.top()) - (int(rect.top()) % GRIDSIZE[1])
        pen = painter.pen()
        pen.setColor(configuration.GridColor.color())
        painter.setPen(pen)

        lines = []
        for x in range(left, int(rect.right()), GRIDSIZE[0]):
            lines.append(QLineF(x, rect.top(), x, rect.bottom()))
        for y in range(top, int(rect.bottom()), GRIDSIZE[1]):
            lines.append(QLineF(rect.left(), y, rect.right(), y))

        painter.drawLines(lines)

        return super().drawBackground(painter, rect)

    def searchByUUID(self, uuid: str):
        db = self.items()
        hit = None
        for item in db:
            if item.__class__.__name__ == 'DesignNode' and str(item.ownedDL.uuid) == uuid:
                hit = item
                break
            elif item.__class__.__name__ == 'RequirementNode' and str(item.ownedRL.uuid) == uuid:
                hit = item
                break
        return hit

    def formatRequirements(self):
        g = Graph()
        testuuid = ""
        reqnodes = [itemiter for itemiter in self.items(
        ) if itemiter.__class__.__name__ == 'RequirementNode']
        root = g.add_vertex('root')
        for item in reqnodes:
            g.add_vertex(str(item.ownedRL.uuid))
            if len(item.ownedRL.upstream) == 0:
                g.add_edge('root', str(item.ownedRL.uuid))
        for item in reqnodes:
            for downstreamitem in item.getDownstreamItems():
                g.add_edge(str(item.ownedRL.uuid), str(
                    downstreamitem.ownedRL.uuid))

        
        #layout = g.layout_sugiyama()
        #g.layout("rt")
        offset = QPointF(0, 0)
        named_vertex_list = g.vs["name"]
        
        lookup = {}

        # Distances from the root, will be used for ordering:
        dist=g.shortest_paths(source='root')[0]

        def ordering(elems):
            return sorted(range(len(elems)), key=elems.__getitem__)

        # Compute orderings based on the distance from the root:
        perm = ordering(dist)
        invperm = ordering(perm)

        # Reorder, direct, restore order:
        dg = g.permute_vertices(invperm)
        dg.to_directed('acyclic')
        dg : Graph = dg.permute_vertices(perm)

        layout = dg.layout_reingold_tilford(root=root.index)

        '''for i, it in enumerate(named_vertex_list):
            it = self.searchByUUID(it)
            
            tarx = layout.coords[i][0] * (380 * math.log(len(layout.coords)))
            tary = layout.coords[i][1] * (480 * len(layout.coords[0]))
            #it.moveTo(QPointF(tarx, tary))
            it.setPos(QPointF(tarx, tary))'''

        # Capture original and ideal positions
        for i, vertex in enumerate(named_vertex_list):
            if vertex != 'root':
                item = self.searchByUUID(vertex)
                #g.vs['name'].index(vertex)
                #print(named_vertex_list.index(vertex))
                
                idealX = layout.coords[i][0] * (380 * math.log(len(layout.coords)))
                idealY = layout.coords[i][1] * (480 * len(layout.coords[0]))

                lookup[vertex] = {
                    'ideal':             {
                        'x': idealX,
                        'y': idealY
                    },
                    'original':             {
                        'x': item.x(),
                        'y': item.y()
                    },
                }
                item.setPos(idealX, idealY)


        # Calculate Midpoint
        itemsbbox = self.itemsBoundingRect()
        scenebbox = self.sceneRect()
        offset.setX((scenebbox.width()/2)-(itemsbbox.width()/2))
        offset.setY((scenebbox.height()/2)-(itemsbbox.height()/2))

        # Restore position
        for key, value in lookup.items():
            item = self.searchByUUID(key)
            item.setPos(value['original']['x'], value['original']['y'])

        self.views()[0].moveTo(
            QPointF((scenebbox.width()/2), (scenebbox.height()/2)))

        # Animate move to new point
        for key, value in lookup.items():
            item = self.searchByUUID(key)
            item.moveTo(QPointF(value['ideal']['x']+offset.x(), value['ideal']['y']+offset.y()))

        #plot(dg, layout=layout)

    def requestRepaintTraces(self):
        reqnodes = [itemiter for itemiter in self.items(
        ) if itemiter.__class__.__name__ == 'RequirementNode']
        for node in reqnodes:
            node.repaintTraces()
        self.update()
        self.views()[0].repaint()

    ''' Mouse Interactions '''

    def dragEnterEvent(self, QGraphicsSceneDragDropEvent):
        QGraphicsSceneDragDropEvent.accept()

    def dragMoveEvent(self, QGraphicsSceneDragDropEvent):
        QGraphicsSceneDragDropEvent.accept()
