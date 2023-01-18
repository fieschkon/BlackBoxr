import inspect

from Serializer import json_decode, json_encode


class Settings:
    testVarA = 'Yo'
    testVarB = 6

    def serializeSettings():
        attributes = inspect.getmembers(Settings, lambda a:not(inspect.isroutine(a)))
        serializedDict = {a[0] : a[1] for a in attributes if not(a[0].startswith('__') and a[0].endswith('__'))}
        return json_encode(serializedDict)

    def loadSettings(indict : dict):
        for key, value in indict.items():
            setattr(Settings, key, json_decode(value))

