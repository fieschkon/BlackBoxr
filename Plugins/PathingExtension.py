import math
from PySide6.QtWidgets import (
    QGraphicsScene, QGraphicsPathItem, QGraphicsItem
)

from PySide6.QtCore import QRectF, QPointF
from pathfinding.core.diagonal_movement import DiagonalMovement
from pathfinding.core.grid import Grid
from pathfinding.finder.dijkstra import DijkstraFinder
GRIDSIZE = (25, 25)

from BBData import Plugins

class PathingPlugin(Plugins.PluginBase):

    role = Plugins.PluginRole.PATHING

    def run(*args, **kwargs):
        ignoreditems = []

        ref = kwargs.get('ref')

        if isinstance(ref._sourcePoint, QGraphicsItem):
            s = ref.mapFromParent(ref._sourcePoint.scenePos())
            ignoreditems.append(ref._sourcePoint)
        else:
            s = ref._sourcePoint
        if isinstance(ref._destinationPoint, QGraphicsItem):
            d = ref.mapFromParent(ref._destinationPoint.scenePos())
            ignoreditems.append(ref._destinationPoint)

        else:
            d = ref._destinationPoint

        searchbounds : QRectF = PathingPlugin.buildSearchBounds(ref.mapToScene(s), ref.mapToScene(d), ref.scene())
        '''if ref.worker != None:
            ref.worker.terminate()'''
        mat = PathingPlugin.generateMatrixFromScene(searchbounds, ref.scene(), [ref])
        return PathingPlugin.pathfind(ref.mapToScene(s), ref.mapToScene(d), searchbounds, mat)


    ## Unique Plugin Contents ##
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
            if item.__class__.__name__ != 'ArrowItem':
                #isinstance(item, ArrowItem):
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
                if item.__class__.__name__ not in ['QGraphicsProxyWidget', 'Socket', 'ArrowItem']:
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
                elif item.__class__.__name__ in ['QGraphicsPathItem', 'ArrowItem']:
                    #isinstance(item, QGraphicsPathItem):
                    coords = PathingPlugin.gridPointsFromPath(item)
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
            p = (coordinate[0]*GRIDSIZE[0]+gridOffset[0]+searchbounds.x()+25,
                coordinate[1]*GRIDSIZE[1]+gridOffset[1]+searchbounds.y()+6)
            translatedpath.append(p)
        return translatedpath