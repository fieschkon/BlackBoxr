import importlib.util
import inspect
import os
from os import path
import pkg_resources
import sys


__author__ = "Max Fieschko"
__copyright__ = "Copyright 2022 Bingus"
__license__ = "MIT"
__maintainer__ = __author__
__email__ = "mfieschko@gmail.com"
__version__ = "0.0.1"
__version_info__ = tuple(int(part) for part in __version__.split('.'))
__description__ = "A visual tool for designing systems."

basedir = os.path.dirname(os.path.realpath(__file__))
libdir =  os.path.normpath(basedir + os.sep + os.pardir) + "\\FunctionLibraries\\"



thidpartymodules = {}

# Load Function Libraries
from os.path import dirname, basename, isfile, join
