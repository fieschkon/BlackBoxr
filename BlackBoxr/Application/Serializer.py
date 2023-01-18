import json

#from BlackBoxr.Application.Canvas.GUITypes import ThemedColor


class JSONEncoder(json.JSONEncoder):

    # overload method default
    def default(self, obj):

        # Match all the types you want to handle in your converter
        
        if obj.__class__.__name__ == 'ThemedColor':
            return obj.toDict()
        # Call the default method for other types
        return json.JSONEncoder.default(self, obj)


class JSONDecoder(json.JSONDecoder):
    def __init__(self, *args, **kwargs):
        json.JSONDecoder.__init__(
            self, object_hook=self.object_hook, *args, **kwargs)

    def object_hook(self, obj):

        # handle your custom classes
        if isinstance(obj, dict):
            if 'type' in obj.keys() and obj['type'] == ThemedColor.__class__.__name__:
                return ThemedColor.fromDict(obj)

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