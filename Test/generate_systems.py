
from BlackBoxr.Application.objects import *
from BlackBoxr.misc.Datatypes import DesignElement, RequirementElement, System, TestElement

testSys = System()

elements = [RequirementElement(testSys) for x in range(10)] + [DesignElement(testSys) for x in range(10)] + [TestElement(testSys) for x in range(10)]

print(testSys.save())