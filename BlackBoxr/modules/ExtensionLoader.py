from importlib import import_module
import os
import sys

from inspect import isclass
from pkgutil import iter_modules
from pathlib import Path
from importlib import import_module, reload
from time import sleep
from types import ModuleType

from BBData import Plugins, Delegate


plugins = {}

class ExtensionLoader():

    plugins = {}
    onPackagesExtracted = Delegate()
    onBuildProgress = Delegate()

    def DiscoverExtensions():
        discoveredExtensionPaths : list[str] = []
        for root, dirs, files in os.walk(os.path.join(os.getcwd(), 'Plugins')):
            for file in files:
                if file.endswith(".py"):
                    discoveredExtensionPaths.append(os.path.relpath(os.path.join(root, file)))
        return discoveredExtensionPaths

    def ExtractPackages():
        modules : list[tuple] = []
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
                    print(f'Plugin found in Plugins.{module_name}')
                    modules.append(Plugin(attribute, module))
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
        ExtensionLoader.onPackagesExtracted.emit(len(modules))
        return modules

    def buildPlugins():
        rawplugins : list[Plugin] = ExtensionLoader.ExtractPackages()
        processedplugins = {}
        for index, plugin in enumerate(rawplugins):
            category = plugin.plugin.role
            if category not in list(processedplugins.keys()):
                processedplugins[category] = [plugin]
            else:
                processedplugins[category].append(plugin)
            ExtensionLoader.onBuildProgress.emit(index, len(rawplugins))
        return processedplugins

    def reloadPlugins():
        for category, plugins in ExtensionLoader.plugins.items():
            for plugin in plugins:
                plugin.reload()

    def populatePlugins():
        if ExtensionLoader.plugins == {}:
            ExtensionLoader.plugins = ExtensionLoader.buildPlugins()
        else:
            ExtensionLoader.plugins = ExtensionLoader.reloadPlugins()

class Plugin():
    def __init__(self, pluginbase, module) -> None:
        self.module = module
        self.plugin : Plugins.PluginBase = pluginbase
    
    def run(self, *args, **kwargs):
        return self.plugin.run(*args, **kwargs)

    def reload(self):
        reload(self.module)
        for attribute_name in dir(self.module):
            attribute = getattr(self.module, attribute_name)

            if isclass(attribute) and issubclass(attribute, Plugins.PluginBase):
                self.plugin = attribute
                break