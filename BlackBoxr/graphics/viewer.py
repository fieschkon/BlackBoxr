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
from BlackBoxr.utilities import closestPoint, printMatrix

from pathfinding.core.diagonal_movement import DiagonalMovement
from pathfinding.core.grid import Grid
from pathfinding.finder.a_star import AStarFinder

GRIDSIZE = (25, 25)
ENDOFFSET = -QPointF(25, 25)

class DiagramViewer(QGraphicsView):

    newVisibleArea = Signal(QRectF)

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
        self.newVisibleArea.emit(self.mapToScene(self.viewport().geometry()).boundingRect())
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

    def searchByUUID(self, uuid : str):
        db = self.items()
        hit = None
        for item in db:
            if item.__class__ == 'Socket' and str(item.ownedDL.uuid) == uuid:
                hit = item
                break
            elif item.__class__ == 'DesignNode' and str(item.ownedDL.uuid) == uuid:
                hit = item
                break
        return hit

    ''' Mouse Interactions '''
    def dragEnterEvent(self, QGraphicsSceneDragDropEvent):
        QGraphicsSceneDragDropEvent.accept()

    def dragMoveEvent(self, QGraphicsSceneDragDropEvent):
        QGraphicsSceneDragDropEvent.accept()



def pathfind(a : QPointF, b : QPointF, scene : QGraphicsScene, ignoreditems : list[QGraphicsItem]):

    topleft = QPointF(min(a.x(), b.x()), min(a.y(), b.y()))
    bottomright = QPointF(max(a.x(), b.x()), max(a.y(), b.y()))
    searchbounds = QRectF(topleft, bottomright)
    
    mat = [[1 for _ in range(math.ceil(searchbounds.width() / GRIDSIZE[0]))] for _ in range(math.ceil(searchbounds.height() / GRIDSIZE[1]))]
    for c2 in range(len(mat)):
        for c1 in range(len(mat[0])):
            x = searchbounds.x() + (GRIDSIZE[0] * c1)
            y = searchbounds.y() + (GRIDSIZE[0] * c2)
            
            t = scene.itemAt(QPointF(float(x), float(y)), QTransform())
            mat[c2][c1] = -1 if isinstance(t, NodeBase) and t not in ignoreditems else 1
    
    grid = Grid(matrix=mat)

    if a.x() < b.x() and a.y() < b.y():

        start = grid.node(0, 0)
        end = grid.node(len(mat[0])-1, len(mat)-1)
        anchor = a

    elif a.x() < b.x() and a.y() > b.y():

        start = grid.node(0, len(mat)-1)
        end = grid.node(len(mat[0])-1, 0)
        anchor = a - QPointF(len(mat[0])-1, 0)

    elif a.x() > b.x() and a.y() < b.y():

        start = grid.node(len(mat[0])-1, 0)
        end = grid.node(0, len(mat)-1)
        anchor = a - QPointF((len(mat[0])-1) * GRIDSIZE[0], 0)

    elif a.x() > b.x() and a.y() > b.y():

        start = grid.node(len(mat[0])-1, len(mat)-1)
        end = grid.node(0, 0)
        anchor = a - QPointF(0, 0)

    finder = AStarFinder(diagonal_movement=DiagonalMovement.always)
    path, runs = finder.find_path(start, end, grid)
    translatedpath = []
    printMatrix(mat)

    return translatedpath, anchor

