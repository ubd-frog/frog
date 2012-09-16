""" plugin api """


class FrogPluginRegistry(type):
    plugins = {}
    def __init__(cls, name, bases, attrs):
        if name != 'FrogPlugin' and name not in FrogPluginRegistry.plugins.keys():
            FrogPluginRegistry.plugins[name] = cls

class FrogPlugin(object):
    __metaclass__ = FrogPluginRegistry

    def buttonHook(self):
        """ 
        Return a dict with label, callback, js, and css lists
        """
        return None

    def managerHook(self):
        """ 
        Return a dict with label, callback, js, and css lists
        """
        return None