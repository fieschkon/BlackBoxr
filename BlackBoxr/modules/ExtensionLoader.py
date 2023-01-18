from importlib import import_module
import os
import sys

from inspect import isclass
from pkgutil import iter_modules
from pathlib import Path
from importlib import import_module

from BBData import Plugins


plugins = {}

class ExtensionLoader():

    def DiscoverExtensions():
        discoveredExtensionPaths : list[str] = []
        for root, dirs, files in os.walk(os.path.join(os.getcwd(), 'Plugins')):
            for file in files:
                if file.endswith(".py"):
                    discoveredExtensionPaths.append(os.path.relpath(os.path.join(root, file)))
        return discoveredExtensionPaths

    def ExtractPackages():
        modules = []
        files = ExtensionLoader.DiscoverExtensions()
        print(f'{len(files)} files found, {files}')
        #files = [path.replace(os.sep, '.') for path in files]
        for (_, module_name, _) in iter_modules([os.path.join(os.getcwd(), 'Plugins')]):
            print(f'Found {module_name}, checking for plugin data...')
            # import the module and iterate through its attributes
            module = import_module(f"Plugins.{module_name}")
            for attribute_name in dir(module):
                attribute = getattr(module, attribute_name)

                if isclass(attribute) and issubclass(attribute, Plugins.PluginBase):
                    #globals()[attribute_name] = attribute
                    print(f'Plugin found in {attribute_name}')
                    modules.append(Plugin(attribute))
            '''path = os.path.splitext(path)[0]
            path = path.replace(os.sep, '.')
            try:
                p = Plugin(path)
                modules.append(p)
                print(f'Found extension {path}')
            except AttributeError:
                # Not a plugin
                pass
            except Exception as e:
                print(f'Error loading extension {path}: {e}, skipping...')'''

        return modules

class Plugin():
    def __init__(self, pluginbase) -> None:
        self.plugin : Plugins.PluginBase = pluginbase
    
    def run(self, *args, **kwargs):
        return self.plugin.run(*args, **kwargs)
