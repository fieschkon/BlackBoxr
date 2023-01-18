import json
from PySide6.QtGui import QColor
from BlackBoxr.Application.Canvas.GUITypes import ThemedColor


class JSONEncoder(json.JSONEncoder):

    # overload method default
    def default(self, obj):

        # Match all the types you want to handle in your converter
        
        if isinstance(obj, ThemedColor):
            return obj.toDict()
        elif isinstance(obj, QColor):
            return {
                'type' : QColor.__class__.__name__,
                'color' : (obj.red(), obj.green(), obj.blue())
            }
        # Call the default method for other types
        return json.JSONEncoder.default(self, obj)


class JSONDecoder(json.JSONDecoder):
    def __init__(self, *args, **kwargs):
        json.JSONDecoder.__init__(
            self, object_hook=self.object_hook, *args, **kwargs)

    def object_hook(self, obj):
        # handle your custom classes
        if isinstance(obj, dict):
            if 'type' in obj.keys():
                print(f'Object is of scannable type {obj.keys()[0]}')
                if obj['type'] == ThemedColor.__class__.__name__:
                    return ThemedColor.fromDict(obj)
                elif obj['type'] == QColor.__class__.__name__:
                    return QColor(obj['color'][0], obj['color'][1], obj['color'][2])

        # handling the resolution of nested objects
        if isinstance(obj, dict):
            for key in list(obj):
                obj[key] = self.object_hook(obj[key])

            return obj

        if isinstance(obj, list):
            for i in range(0, len(obj)):
                obj[i] = self.object_hook(obj[i])

            return obj

        return obj

def json_encode(data):
    return JSONEncoder().encode(data)

def json_decode(string):
    return JSONDecoder().decode(string)