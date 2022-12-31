from abc import abstractmethod
import copy
from enum import Enum
import os
import time
from types import NoneType
from typing import Type
from uuid import UUID, uuid4
import uuid
import warnings
import qdarktheme
from dictdiffer import diff, patch, swap, revert
from PySide6.QtWidgets import (
    
    QGraphicsItem, QGraphicsScene
)
from PySide6.QtGui import QUndoCommand
from PySide6.QtCore import QPointF
from datetime import datetime
import json

from BlackBoxr.utilities import first, getDuration
from BlackBoxr.misc.objects import datadir, tmpdir, systems
import BlackBoxr.misc.configuration as configuration

class System():
    
    @staticmethod
    def getDummySystemFromFile(path):
        d = json.load(open(path))
        e = System()
        e.uuid                = uuid.UUID(d['uuid'])
        e.name                = d['name']
        e.createDate          = d['createDate']
        e.updateDate          = d['updateDate']


        return e

    @staticmethod
    def loadFromFile(path):
        return System.fromDict(json.load(open(path)))

    @staticmethod
    def fromDict(inDict : dict):
        e = System()

        ''' Identifiers '''
        e.uuid = uuid.UUID(inDict['uuid'])
        
        e.name                = inDict['name']
        e.createDate          = inDict['createDate']
        e.DL                  = [DesignElement.fromDict(dl) for dl in inDict['DesignElements']]
        e.RL                  = [RequirementElement.fromDict(rl) for rl in inDict['RequirementElements']]
        e.TE                  = [TestElement.fromDict(te) for te in inDict['TestElements']]
        e.updateDate          = inDict['updateDate']
        return copy.deepcopy(e)

    def __init__(self) -> None:
        self.DL = []
        self.RL = []
        self.TE = []

        self.name = "Default System Name"
        self.uuid = uuid.uuid4()

        self.createDate = self.generateCreateTime()
        self.updateDate = self.createDate

        if self not in systems:
            systems.append(self)

    def setName(self, name):
        self.name = copy.deepcopy(name)

    def unloadData(self):
        pass

    def searchByUUID(self, uuid):
        a = copy.deepcopy(uuid)
        s = self.DL + self.RL + self.TE
        if isinstance(uuid, UUID):
            a = str(a)
        return first(x for x in s if str(x.uuid) == a)
        
    def getAllElements(self):
        return self.DL + self.RL + self.TE

    def generateCreateTime(self):
        self.createDate = datetime.now().strftime("%m/%d/%y %H:%M:%S")
        return self.createDate

    def toDict(self):
        d = {}
        d['name'               ] = self.name
        d['createDate'         ] = self.createDate
        d['updateDate'         ] = self.updateDate
        d['uuid'               ] = str(self.uuid)
        d['DesignElements'     ] = [dl.toDict() for dl in self.DL]
        d['RequirementElements'] = [rl.toDict() for rl in self.RL]
        d['TestElements'       ] = [te.toDict() for te in self.TE]
        return copy.deepcopy(d)

    def save(self, filename = None):
        if isinstance(filename, NoneType):
            name = str(self.uuid) if configuration.namingstyle == 'By UUID' else self.name
            filename = "{}/{}.json".format(datadir, name)
        with open(filename, "w+") as outfile:
            outfile.write(json.dumps(self.toDict()))
        return filename

    def deltaSinceUpdate(self):
        return getDuration(datetime.strptime(self.updateDate, "%m/%d/%y %H:%M:%S"))['seconds']

    def __setattr__(self, key, value):
        if hasattr(self, key):
            if key not in ['updateDate'] and value != self.__getattribute__(key):
                self.updateDate = datetime.now().strftime("%m/%d/%y %H:%M:%S")
        super().__setattr__(key, value)

    def __eq__(self, __o: object) -> bool:
        if isinstance(__o, System):
            return self.toDict() == __o.toDict()
        return False

# Stuff that goes into a system

class Element():

    @staticmethod
    def diff(elementA, elementB):
        return list(diff(elementA.toDict(), elementB.toDict()))

    @staticmethod
    def fromDict(inDict : dict, owningSystem : System = None):
        e = Element(owningSystem)

        ''' Identifiers '''
        e.uuid = uuid.UUID(inDict['uuid'])
        
        ''' Fields are used to denote public and private fields '''
        e.public = inDict['public']
        e.private = inDict['private']

        ''' Time tracking '''
        e.createDate = inDict['createDate']
        e.updateDate = inDict['updateDate']

        return copy.deepcopy(e)

    @staticmethod
    def fromStr(inStr : str, owningSystem : System = None):
        return Element.fromDict(json.loads(str), owningSystem)

    @abstractmethod
    def addToSystem(self):
        pass

    def __init__(self, owningSystem : System = None) -> None:
        self.owningSystem = owningSystem

        ''' Identifiers '''
        self.uuid = uuid.uuid4()
        
        ''' Fields are used to denote public and private fields '''
        self.public = {}
        self.private = {'tags' : []}

        ''' Time tracking '''
        self.createDate = self.generateCreateTime()
        self.updateDate = self.createDate

        self.addToSystem()

    def generateCreateTime(self):
        self.createDate = datetime.now().strftime("%m/%d/%y %H:%M:%S")
        return self.createDate

    def toDict(self) -> dict:
        d = {}
        d['uuid'] = str(self.uuid)
        d['public'] = self.public
        d['private'] = self.private
        d['createDate'] = self.createDate
        d['updateDate'] = self.updateDate
        return copy.deepcopy(d)

    def __setattr__(self, key, value):
        if hasattr(self, key):
            if key not in ['updateDate', 'initflag'] and value != self.__getattribute__(key):
                self.updateDate = datetime.now().strftime("%m/%d/%y %H:%M:%S")
        super().__setattr__(key, value)

    def __repr__(self) -> str:
        return str(self.uuid)

    def __str__(self) -> str:
        return json.dumps(self.toDict())

    def __eq__(self, __o: object) -> bool:
        if isinstance(__o, Element):
            return self.toDict() == __o.toDict()
        elif isinstance(__o, dict):
            warnings.warn("Warning: instance {} is dict, not Element.".format(__o))
            return self.toDict() == __o
        elif isinstance(__o, str):
            warnings.warn("Warning: instance {} is str, not Element.".format(__o))
            return str(self) == __o

    def __hash__(self) -> int:
        return hash(tuple(sorted(self.toDict())))

class DesignElement(Element):
    
    @staticmethod
    def fromDict(inDict: dict, owningSystem: System = None):
        e = Element.fromDict(inDict, owningSystem)
        e.__class__ = DesignElement
        e.name = inDict["name"]  
        e.topSockets     = inDict["topSockets"]  
        e.bottomSockets   = inDict["bottomSockets"]
        e.leftSockets     = inDict["leftSockets"]  
        e.rightSockets   = inDict["rightSockets"]
        e.requirements  = inDict["requirements"]

        e.connectionTo = inDict["connectionTo"]
        e.connectionFrom = inDict["connectionFrom"]

        return copy.deepcopy(e)

    def __init__(self, owningSystem : System = None) -> None:
        super().__init__(owningSystem)
        self.name : str = ""

        self.topSockets    : list[str] = []
        self.bottomSockets  : list[str] = []
        self.leftSockets    : list[str] = []
        self.rightSockets  : list[str] = []

        self.requirements : list[str] = []
        self.connectionTo : list[str] = []
        self.connectionFrom : list[str] = []

    def hasSockets(self)->bool:
        return len(self.topSockets) == 0 and len(self.bottomSockets) == 0 and len(self.leftSockets) == 0 and len(self.rightSockets) == 0

    def addToSystem(self):
        self.owningSystem.DL.append(self)

    def toDict(self) -> dict:
        d = super().toDict()
        d["name"] = self.name
        d["topSockets"]   = self.topSockets
        d["bottomSockets"] = self.bottomSockets
        d["leftSockets"]   = self.leftSockets
        d["rightSockets"] = self.rightSockets
        d["requirements"] = self.requirements

        d["connectionTo"] = self.connectionTo
        d["connectionFrom"] = self.connectionFrom

        return copy.deepcopy(d)

    def addConnectionTo(self, targetDL):
        if str(targetDL.uuid) not in self.connectionTo:
            self.connectionTo.append(str(targetDL.uuid))
        if str(self.uuid) not in targetDL.connectionFrom:
            targetDL.connectionFrom.append(str(self.uuid))

    def addConnectionFrom(self, sourceDL):
        if str(sourceDL.uuid) not in self.connectionFrom:
            self.connectionFrom.append(str(sourceDL.uuid))
        if str(self.uuid) not in sourceDL.connectionTo:
            sourceDL.connectionTo.append(str(self.uuid))


class RequirementElement(Element):

    @staticmethod
    def fromDict(inDict: dict, owningSystem: System = None):
        e = Element.fromDict(inDict, owningSystem)
        e.__class__ = RequirementElement
        e.owningDL          = inDict["owningDL"]  
        e.upstream          = inDict["upstream"]  
        e.downstream        = inDict["downstream"]
        return copy.deepcopy(e)

    def __init__(self, owningSystem : System = None) -> None:
        super().__init__(owningSystem)
        self.owningDL   = ""
        self.downstream = []
        self.upstream   = []

    def addToSystem(self):
        self.owningSystem.RL.append(self)

    def toDict(self) -> dict:
        d = super().toDict()
        d["owningDL"]   = self.owningDL
        d["upstream"]   = self.upstream
        d["downstream"] = self.downstream

        return copy.deepcopy(d)

    def addDownstream(self, RL):
        if str(RL.uuid) not in self.downstream:
            self.downstream.append(str(RL.uuid))
        if str(self.uuid) not in RL.upstream:
            RL.upstream.append(str(self.uuid))

    def addUpstream(self, RL):
        if str(RL.uuid) not in self.upstream:
            self.upstream.append(str(RL.uuid))
        if str(self.uuid) not in RL.downstream:
            RL.downstream.append(str(self.uuid))

    def removeDownstream(self, RL):
        if str(RL.uuid) in self.downstream:
            self.downstream.remove(str(RL.uuid))
        if str(self.uuid) in RL.upstream:
            RL.upstream.remove(str(self.uuid))

    def removeUpstream(self, RL):
        if str(RL.uuid) in self.upstream:
            self.upstream.remove(str(RL.uuid))
        if str(self.uuid) in RL.downstream:
            RL.downstream.remove(str(self.uuid))

    def removeFromStreams(self, RL):
        self.removeDownstream(RL)
        self.removeUpstream(RL)

    def isDownstream(self, dsitem) -> bool:
        return str(dsitem.uuid) in self.downstream

    def isUpstream(self, usitem) -> bool:
        return str(self.uuid) in usitem.downstream

class TestElement(Element):

    def __init__(self, owningSystem : System = None) -> None:
        super().__init__(owningSystem)

    def addToSystem(self):
        self.owningSystem.TE.append(self)
####################################

class MoveCommand(QUndoCommand):

    def __init__( self, diagramItem : QGraphicsItem, oldPos : QPointF, newpos = None, parent = None):
        super().__init__(parent)
        self.myDiagramItem = diagramItem
        self.myOldPos = oldPos
        if isinstance(newpos, NoneType):
            self.newPos = self.myDiagramItem.pos()
        else: self.newPos = newpos
        self.parent = parent

    def undo(self):
        self.myDiagramItem.setPos(self.myOldPos)
        self.myDiagramItem.scene().update()

    def redo(self):
        self.myDiagramItem.setPos(self.newPos)
        self.myDiagramItem.scene().update()

class AddCommand(QUndoCommand):

    def __init__( self, item, scene, initialpos, parent = None):
        super().__init__(parent)
        self.myGraphicsScene = scene
        self.myDiagramItem = item
        self.initialposition = initialpos

    def undo(self):
        self.myGraphicsScene.removeItem(self.myDiagramItem)
        self.myGraphicsScene.update()

    def redo(self):
        self.myGraphicsScene.addItem(self.myDiagramItem)
        self.myDiagramItem.setPos(self.initialposition)
        self.myGraphicsScene.clearSelection()
        self.myGraphicsScene.update()

class DeleteCommand(QUndoCommand):
    def __init__(self, scene, parent = None):
        super().__init__(parent)
        self.myGraphicsScene = scene
        self.list = self.myGraphicsScene.selectedItems()
        
    def undo(self):
        [self.myGraphicsScene.addItem(n) for n in self.list]
        self.myGraphicsScene.update()

    def redo(self):
        [self.myGraphicsScene.removeItem(n) for n in self.list]

class NameEdit(QUndoCommand):
    def __init__(self, node, newtext, parent=None):
        super().__init__(parent)
        self.node = node
        self.oldtext = self.node.blockname
        self.newtext = newtext
        
    def undo(self):
        self.node.blockname = self.oldtext
        self.node.lbl.namelabel.setText(self.oldtext)

    def redo(self):
        self.node.blockname = self.newtext
        self.node.lbl.namelabel.setText(self.newtext)



'''class ConnectionCommand(QUndoCommand):
    def __init__(self, scene, socketA, socketB):
        super().__init__()
        self.scene : QGraphicsScene = scene
        self.a = socketA
        self.b = socketB
        
        self.list = self.myGraphicsScene.selectedItems()
        
    def undo(self):
        self.scene.removeItem(self.a.__trace)
        self.a.__trace = None
        self.b.__trace = None
        
        self.scene.update()

    def redo(self):
        source = self.a if self.a.iotype == IOType.OUTPUT else self.b
        dest = self.a if source is self.b else self.b
        source.__trace = OldArrowItem(endItem=dest, startItem=source)
        self.scene.addItem(source.__trace)
        source.__trace.setZValue(0)
        source.__trace.setPos(source.scenePos())
        dest.__trace = source.__trace'''