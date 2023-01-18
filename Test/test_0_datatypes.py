import copy
from datetime import datetime
import logging
import os
import random
import pytest
from time import sleep
from BlackBoxr import utilities
from BlackBoxr.misc import Datatypes
from BlackBoxr.misc.Datatypes import DesignElement, Element, RequirementElement, System, TestElement
from BlackBoxr.graphics.GUITypes import ThemedColor
from BlackBoxr.Application.objects import datadir, tmpdir
from BlackBoxr.Application import configuration
from dictdiffer import diff, patch, swap, revert
from PySide6.QtGui import QColor

testSys = System()

class TestElements:

    def test_AutoAdd(self):
        r = RequirementElement(testSys)
        d = DesignElement(testSys)
        t = Datatypes.TestElement(testSys)

        assert r in testSys.RL
        assert d in testSys.DL
        assert t in testSys.TE

    @pytest.mark.last
    def test_UpdateTime_NewData(self):
        '''
        Tests if the update time is updated when a field is modified with new data.
        '''
        e = Element(testSys)
        e.public = {"test": "testval"}
        u = datetime.strptime(e.updateDate, "%m/%d/%y %H:%M:%S")
        sleep(2)
        e.public = {"test": "testval2"}
        k = datetime.strptime(e.updateDate, "%m/%d/%y %H:%M:%S")
        duration = k - u
        assert duration.seconds == 2

    @pytest.mark.second_to_last
    def test_UpdateTime_StaleData(self):
        '''
        Tests if the update time is updated when a field is modified with stale data.
        '''
        e = Element(testSys)
        e.public = {"test": "testval"}
        u = datetime.strptime(e.updateDate, "%m/%d/%y %H:%M:%S")
        sleep(2)
        e.public = {"test": "testval"}
        k = datetime.strptime(e.updateDate, "%m/%d/%y %H:%M:%S")
        duration = k - u
        assert duration.seconds == 0

    def test_StrRep(self):
        '''
        Tests if the string representation matches the dict.
        '''
        e = Element(testSys)
        e.public = {"test": "testval"}

        d = {}
        d['uuid'] = str(e.uuid)
        d['public'] = e.public
        d['private'] = e.private
        d['createDate'] = e.createDate
        d['updateDate'] = e.updateDate

        compA = str(e).replace('"', "'")
        compB = str(d).replace('"', "'")
        assert compA == compB

    def test_Equality(self):
        a = Element(testSys)
        a.public = {"test": "testval"}
        b = copy.deepcopy(a)

        assert a == b
        assert a == str(b)
        assert a == b.toDict()

class TestDL:

    def test_Serialization(self):

        [RequirementElement(testSys) for x in range(10)]
        [DesignElement(testSys) for x in range(10)]

        dl = DesignElement(testSys)
        dl.requirements.append(str(random.choice(testSys.RL).uuid))
        dl.connectionsFrom.append(str(random.choice(testSys.DL).uuid))
        dl.connectionsTo.append(str(random.choice(testSys.DL).uuid))

        assert dl == DesignElement.fromDict(dl.toDict())

    def test_ConnectingTo(self):
        [DesignElement(testSys) for x in range(10)]
        dl = DesignElement(testSys)
        randdl = random.choice(testSys.DL)

        dl.addConnectionTo(randdl)
        assert str(dl.uuid) in randdl.connectionsFrom
        assert str(randdl.uuid) in dl.connectionsTo

class TestRL:

    def test_Serialization(self):

        [RequirementElement(testSys) for x in range(10)]
        [DesignElement(testSys) for x in range(10)]

        rl = RequirementElement(testSys)
        rl2 = RequirementElement(testSys)
        rl.addDownstream(rl2)

        assert rl == RequirementElement.fromDict(rl.toDict(), testSys)
        assert rl.isDownstream(rl2)

    def test_ConnectingTo(self):
        
        rl = RequirementElement(testSys)
        randrl = random.choice([RequirementElement(testSys) for x in range(10)])

        rl.addDownstream(randrl)

        assert str(rl.uuid) in randrl.upstream
        assert str(randrl.uuid) in rl.downstream

class TestSystem:
    def test_Search(self):
        e = random.choice([RequirementElement(testSys) for x in range(10)])
        assert e == testSys.searchByUUID(str(e.uuid))

    def test_Serialize(self):
        assert System.fromDict(testSys.toDict()) == testSys

class TestSerialization:
    def test_SaveLoad(self):

        [RequirementElement(testSys) for x in range(10)]
        [DesignElement(testSys) for x in range(10)]
        [TestElement(testSys) for x in range(10)]

        autosave = testSys.save()
        manualsave = testSys.save("{}/{}.json".format(tmpdir, str(testSys.uuid)))
        

        assert os.path.exists(autosave)
        assert os.path.exists(manualsave)

        assert System.loadFromFile(manualsave) == System.loadFromFile(autosave) == testSys

        os.remove(autosave)
        os.remove(manualsave)


class TestColors:
    def test_AutoDetect(self):
        color = ThemedColor(QColor(255, 0, 0, 255), QColor(0, 255, 0, 255))

        # Configuration uses dark
        configuration.themename = 'dark'
        assert color.color() == QColor(0, 255, 0 ,255)
        # Light
        configuration.themename = 'light'
        assert color.color() == QColor(255, 0, 0 ,255)
        # Auto
        configuration.themename = 'auto'
        testcolor = QColor(0, 255, 0 ,255) if utilities.getTheme() == 'dark' else QColor(255, 0, 0 ,255)
        assert color.color() == testcolor