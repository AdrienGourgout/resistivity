'''
ViewFactory.py is a factory pattern for instantiating an IView object
'''


from enum import IntEnum, auto

from .ViewTk import ViewTk


class ViewType(IntEnum):
    tk = auto()


class ViewFactory():
    def __init__(self):
        pass

    def create(self, type: ViewType, controller):
        if type == ViewType.tk:
            return ViewTk(controller)
        else:
            raise TypeError('Not Implemented')
