from importlib import import_module
import os
import sys

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
        for path in ExtensionLoader.DiscoverExtensions():
            path = os.path.splitext(path)[0]
            path = path.replace(os.sep, '.')
            p = Plugin(path)
            modules.append(p)
            print(f'Found package {path}')

        return modules

class Plugin():
    def __init__(self, path) -> None:
        self.mod = import_module(path)
        self.func = getattr(self.mod, 'Plugin')
    
    def run(self, *args, **kwargs):
        return self.func.run(*args, **kwargs)

    def info(self):
        return self.func.info()