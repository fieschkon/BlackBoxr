from datetime import datetime
import logging
import os
import random
import pytest
from time import sleep
from BlackBoxr.misc import Datatypes
from BlackBoxr.misc.Datatypes import DesignElement, Element, RequirementElement, System, TestElement
from BlackBoxr.misc.objects import datadir, tmpdir
from BlackBoxr.misc import configuration
from dictdiffer import diff, patch, swap, revert

testSys = System()

class TestSaving:

    def test_NamingConvention(self):
        [RequirementElement(testSys) for x in range(10)] + [DesignElement(testSys) for x in range(10)] + [TestElement(testSys) for x in range(10)]

        configuration.namingstyle = 'By UUID'

        uuidsaved = testSys.save()

        configuration.namingstyle = 'By Name'

        namedsave = testSys.save()
        
        assert os.path.exists("{}/{}.json".format(datadir, str(testSys.uuid)))
        assert os.path.exists("{}/{}.json".format(datadir, str(testSys.name)))

        os.remove(uuidsaved)
        os.remove(namedsave)