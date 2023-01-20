from importlib import import_module
import logging
import os
import subprocess
import sys

from inspect import isclass
from pkgutil import iter_modules, walk_packages
from pathlib import Path
from importlib import import_module, reload
from time import sleep
from types import ModuleType
import json

from BBData import Plugins, Delegate

from BlackBoxr import utilities

class Plugin():
    def __init__(self, pluginbase : Plugins.PluginBase, module) -> None:
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

class ExtensionLoader():

    plugins : dict[str : list[Plugin]] = {}
    onPackagesExtracted = Delegate()
    onBuildProgress = Delegate()

    def discoverDependencies():
        logging.info('Searching for plugin helper files...')
        dependencies = []
        files = utilities.getFilesWithExtension([os.path.join(os.getcwd(), 'Plugins')], recursive=True)
        for file in files:
            logging.info(f'Parsing {file}...')
            with open(file) as json_file:
                data : dict = json.load(json_file)
                dependencies += data.get('requires', [])
        return dependencies

    def DiscoverExtensions():
        logging.info(f'Discovering extensions...')
        discoveredExtensionPaths : list[str] = []
        for root, dirs, files in os.walk(os.path.join(os.getcwd(), 'Plugins')):
            for file in files:
                if file.endswith(".py"):
                    discoveredExtensionPaths.append(os.path.relpath(os.path.join(root, file)))
        return discoveredExtensionPaths

    def getAllPlugins() -> list[Plugin]:
        return [item for sublist in list(ExtensionLoader.plugins.values()) for item in sublist]

    def installDependencies(dependencies : list):
        logging.info('Starting to install plugin dependencies...')
        for dependency in dependencies:
            logging.info(f'Installing {dependency}...')
            pipcode = subprocess.check_call([sys.executable, '-m', 'pip', 'install', dependency])
            match pipcode:
                case 0: #success
                    logging.info(f'{dependency} installed successfully.')
                case 1: #error
                    logging.critical(f'{dependency} errored on install.')
                case 2: #unknown error
                    logging.critical(f'{dependency} errored on install.')
                case 23: #no matches found
                    logging.critical(f'{dependency} could not be resolved.')
                case _:
                    logging.critical(f'{dependency} could not be installed due to unknown pip error.')

    def initializePlugins():
        logging.info('Initializing Plugins...')
        for plugin in ExtensionLoader.getAllPlugins():
            plugin.plugin.initialize()

    def ExtractPackages():
        modules : list[tuple] = []
        files = ExtensionLoader.DiscoverExtensions()
        logging.info(f'{len(files)} files found while searching for plugins.')
        logging.debug(f'Files found: {files}')
        #files = [path.replace(os.sep, '.') for path in files]

        for (_, module_name, _) in utilities.iter_modules_recursive([os.path.join(os.getcwd(), 'Plugins')], relativeto=os.getcwd()):
            logging.info(f'Found {module_name}, checking for plugin data...')
            # import the module and iterate through its attributes
            module = import_module(f"{module_name}")
            for attribute_name in dir(module):
                attribute = getattr(module, attribute_name)

                if isclass(attribute) and issubclass(attribute, Plugins.PluginBase):
                    #globals()[attribute_name] = attribute
                    logging.info(f'Plugin found in {module_name}')
                    modules.append(Plugin(attribute, module))
        ExtensionLoader.onPackagesExtracted.emit(len(modules))
        return modules

    def buildPlugins():
        rawplugins : list[Plugin] = ExtensionLoader.ExtractPackages()
        logging.info(f'Mounting plugins...')
        processedplugins = {}
        for index, plugin in enumerate(rawplugins):
            category = plugin.plugin.role
            if category not in list(processedplugins.keys()):
                processedplugins[category] = [plugin]
            else:
                processedplugins[category].append(plugin)
            logging.info(f'Mounted {plugin.module}.')
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

