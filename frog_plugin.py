
from frog.plugin import FrogPlugin

class MyPLug(FrogPlugin):
    def buttonHook(self):
        data = {
            'label': 'MyApp',
            'callback': 'undefined',
            'js': ['frog/j/libs/frog.gallery.js']
        }

        return data 