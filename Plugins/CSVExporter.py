from PySide6.QtWidgets import QFileDialog
import os
import csv

from BBData import Plugins

class Plugin(Plugins.PluginBase):

    name = 'CSV Exporter'
    role = Plugins.PluginRole.EXPORT

    def run(*args, **kwargs):
        insys = kwargs.get('insys')
        fileName = QFileDialog.getSaveFileName(None, ("Save Project"), os.getcwd(), ("CSV Files (*.csv)"))[0]
        if fileName == '':
            return
        with open(fileName, 'w') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=list(insys.RL[0].public.keys()))
            writer.writeheader()
            for RElement in insys.RL:
                writer.writerow(RElement.public)
            
        return fileName

    def info():
        return {
            'name' : 'CSV Exporter',
            'author' : 'Max Fieschko',
            'description' : 'Export a project as a CSV file.',
            'version' : 'v1',
            'category' : 'Exporter'
        }