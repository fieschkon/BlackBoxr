from abc import abstractmethod
from enum import Enum
import inspect
import math
import os
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
from PySide6.QtGui import QTransform, QClipboard, QPixmap, QAction, QPainter, QColor, QPen, QBrush, QCursor, QPainterPath, QFont, QFontMetrics, QUndoStack, QKeySequence, QWheelEvent
from BlackBoxr.Application import configuration
import BlackBoxr.Application.Canvas.Nodes

from BlackBoxr.Application import objects
from BlackBoxr.Application.Canvas.Widgets import SearchBox
from BlackBoxr.misc.Datatypes import MoveCommand, NameEdit, RequirementElement
from BlackBoxr.utilities import closestPoint, printMatrix, snapToGrid, transpose

import igraph as ig
from igraph import Graph, EdgeSeq, plot

GRIDSIZE = (25, 25)
ENDOFFSET = -QPointF(25, 25)


class DiagramViewer(QGraphicsView):

    newVisibleArea = Signal(QRectF)

    def __init__(self, scene: QGraphicsScene, insys = None):
        super(DiagramViewer, self).__init__(scene)
        self._scene = scene
        self.startPos = None
        self.zoomlevel = 0
        self.sys = insys
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
                self.zoomlevel += 1
            else:
                self.scale(0.9, 0.9)
                self.zoomlevel -= 1
        else:
            super(DiagramViewer, self).wheelEvent(event)
        self.newVisibleArea.emit(self.mapToScene(
            self.viewport().geometry()).boundingRect())
        self._scene.update()

    def keyPressEvent(self, event: QtGui.QKeyEvent) -> None:
        if objects.qapp.keyboardModifiers() == (Qt.ControlModifier | Qt.AltModifier) and event.key() == Qt.Key_F:
            self._scene.formatRequirements()
        elif objects.qapp.keyboardModifiers() == (Qt.ControlModifier) and event.key() == Qt.Key_C:
            bounds = self._scene.buildBoundingRectFromSelectedItems()
            self._scene.saveItemsForCopy()
            self._scene.saveImageToClipboard(bounds)
        elif objects.qapp.keyboardModifiers() == Qt.ControlModifier and event.key() == Qt.Key_S:
            self.sys.save()
        return super().keyPressEvent(event)

class DiagramScene(QGraphicsScene):

    formatFinished = Signal()

    def __init__(self, insys = None):
        super().__init__()
        self.sys = insys

        self._dragged = False
        self.moveditems = 0
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

    ''' Mouse Interactions '''

    def dragEnterEvent(self, QGraphicsSceneDragDropEvent):
        QGraphicsSceneDragDropEvent.accept()

    def dragMoveEvent(self, QGraphicsSceneDragDropEvent):
        QGraphicsSceneDragDropEvent.accept()

    def buildBoundingRectFromSelectedItems(self):
        sourcerect = QRect(0,0,0,0)
        for item in self.selectedItems():
            sourcerect = sourcerect.united(item.sceneBoundingRect().toRect())
        return sourcerect

    @abstractmethod
    def saveItemsForCopy(self):
        pass

    def saveImageToClipboard(self, bounds : QRectF):
        
        pxmap = QPixmap(self.views()[0].grab(self.views()[0].mapFromScene(bounds).boundingRect()))
        
        objects.qapp.clipboard().setPixmap(pxmap)
        '''fname = os.path.join(objects.tmpdir, 'boink.png')
        pxmap.save(fname)'''

class RequirementsScene(DiagramScene):

    def __init__(self, insys=None, viewpane=None):
        super().__init__(insys)
        self.viewpane = viewpane

    def contextMenuEvent(self, event: QtWidgets.QGraphicsSceneContextMenuEvent) -> None:
        return super().contextMenuEvent(event)

    def formatRequirements(self):
        g = Graph(directed=True)
        testuuid = ""
        reqnodes = [itemiter for itemiter in self.items(
        ) if itemiter.__class__.__name__ == 'RequirementNode']
        root = g.add_vertex('root')
        for item in reqnodes:
            g.add_vertex(str(item.ownedRL.uuid), label=str(item.ownedRL.uuid))
            if len(item.ownedRL.upstream) == 0:
                g.add_edge('root', str(item.ownedRL.uuid))
        for item in reqnodes:
            for downstreamitem in item.ownedRL.downstream:
                g.add_edge(str(item.ownedRL.uuid), downstreamitem)

        
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

        layout = g.layout_reingold_tilford(root=root.index)
        #g.layout_sugiyama()
        #dg.layout_reingold_tilford(root=root.index)

        # Capture original and ideal positions

        #print(named_vertex_list)

        for i, vertex in enumerate(named_vertex_list):
            if vertex != 'root':
                item = self.searchByUUID(vertex)
                #g.vs['name'].index(vertex)
                coordindex = named_vertex_list.index(vertex)
                
                idealX = layout.coords[coordindex][0] * (380 * math.log(len(layout.coords)))
                idealY = layout.coords[coordindex][1] * (480 * len(layout.coords[0]))

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
        itemsbbox = self.itemsBoundingRect()
        view = self.views()[0]
        offsetrect = view.mapToScene(view.viewport().geometry()).boundingRect()
        offset.setX(offsetrect.x()+offsetrect.width()/2)
        offset.setY(offsetrect.y()+offsetrect.height()/2-itemsbbox.height()/2)
        
        # Animate move to new point
        for key, value in lookup.items():
            item = self.searchByUUID(key)
            item.moveTo(QPointF(value['ideal']['x']+offset.x(), value['ideal']['y']+offset.y()))
            item.moveFinishedNotifier = self.moveIterator

    def saveItemsForCopy(self):
        objects.copiedItems.clear()
        for item in self.selectedItems():
            objects.copiedItems.append(item.ownedRL)

    def moveIterator(self):
        self.moveditems += 1
        requirementsItems = [itemiter for itemiter in self.items() if itemiter.__class__.__name__ == 'RequirementNode']
        numberofitems = len(requirementsItems)
        if self.moveditems == numberofitems:
            self.moveditems = 0
            self.formatFinished.emit()
            self.views()[0].repaint()
            self.update()
            for item in requirementsItems:
                item.itemChange(QGraphicsItem.GraphicsItemChange.ItemPositionChange, item.scenePos())
            
            

    def requestRepaintTraces(self):
        reqnodes = [itemiter for itemiter in self.items(
        ) if itemiter.__class__.__name__ == 'RequirementNode']
        for node in reqnodes:
            node.repaintTraces()
        self.update()
        self.views()[0].repaint()

    def createRequirement(self, at : QPointF):
        rl = BlackBoxr.Application.Canvas.Nodes.RequirementNode(RequirementElement(self.sys))
        self.addItem(rl)
        rl.setPos(at)

class RequirementsViewer(DiagramViewer):
    def __init__(self, scene: QGraphicsScene, insys=None, viewpane=None):
        super().__init__(scene, insys)
        self.reqscene = scene
        self.viewpane = viewpane

    def contextMenuEvent(self, event) -> None:
        menu = QMenu(self)
        wa = QWidgetAction(menu)
        wa.setDefaultWidget(SearchBox())
        menu.addAction(wa)
        '''reqcreate = menu.addAction("Create Requirement")
        reqcreate.triggered.connect(lambda : self.reqscene.createRequirement(self.mapToScene(event.pos())))'''
        
        menu.activateWindow()
        wa.defaultWidget().SearchBar.setFocus(Qt.FocusReason.PopupFocusReason)
        menu.exec(self.mapToGlobal(event.pos()))
        

        return super().contextMenuEvent(event)

    def wheelEvent(self, event: QWheelEvent, norep=False):
        super().wheelEvent(event, norep)
        if self.zoomlevel <= -6:
            for item in self.items():
                if item.__class__.__name__ == 'RequirementNode':
                    item.lbl.setHidden(True)
        else:
            for item in self.items():
                if item.__class__.__name__ == 'RequirementNode':
                    item.lbl.setHidden(False)
        
