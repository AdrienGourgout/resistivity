"""
IView.py an interface for the 'View' part of the Model-
View-Controller design pattern for MultiPyVu.Server

@author: djackson
"""


from abc import ABC, abstractmethod


class IView(ABC):
    @classmethod
    def __subclasshook__(cls, subclass):
        return (
            hasattr(subclass, '__init__')
            and callable(subclass.__init__) and
            hasattr(subclass, 'create_display')
            and callable(subclass.create_display) and
            hasattr(subclass, 'get_connection_status')
            and callable(subclass.get_connection_status) and
            hasattr(subclass, 'set_connection_status')
            and callable(subclass.set_connection_status) and
            hasattr(subclass, 'mvu_flavor')
            and callable(subclass.mvu_flavor) and
            hasattr(subclass, 'start_gui')
            and callable(subclass.start_gui) and
            hasattr(subclass, 'quit_gui')
            and callable(subclass.quit_gui)

            or NotImplemented)

    # Quantum Design colors:
    # QD Red: RGB: 183/18/52 & QD "Black": RGB: 30/30/30
    qd_red = '#B71234'
    qd_black = '#1E1E1E'

    @abstractmethod
    def __init__(self, controller):
        self._controller = controller

    @abstractmethod
    def create_display(self):
        raise NotImplementedError

    @abstractmethod
    def get_connection_status(self):
        raise NotImplementedError

    @abstractmethod
    def set_connection_status(self):
        raise NotImplementedError

    @property
    @abstractmethod
    def mvu_flavor(self):
        raise NotImplementedError

    @abstractmethod
    def start_gui(self):
        raise NotImplementedError

    @abstractmethod
    def quit_gui(self):
        raise NotImplementedError
