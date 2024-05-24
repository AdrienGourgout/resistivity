'''
IController.py is an interface for the Controller part
of the Model-View-Controller pattern for MultiPyVu.

Note that this class has a concrete __init__() method
which should be called using super().__init__(flags) in
any inherited classes.  The reason for this is that
the member variables such as 'model' and 'view' are
necessary.  But note that this does not define what
those variables should be, leaving that to the concrete
classes.
'''


from abc import ABC, abstractmethod
from typing import List


class IController(ABC):
    @classmethod
    def __subclasshook__(cls, subclass) -> bool:
        return (
            hasattr(subclass, 'is_client_connected')
            and callable(subclass.is_client_connected) and
            hasattr(subclass, 'start_gui')
            and callable(subclass.start_gui) and
            hasattr(subclass, 'quit_gui')
            and callable(subclass.quit_gui) and
            hasattr(subclass, 'absolute_path')
            and callable(subclass.absolute_path) and
            hasattr(subclass, 'ip_address')
            and callable(subclass.ip_address) and
            hasattr(subclass, 'start_server')
            and callable(subclass.start_server) and
            hasattr(subclass, 'stop_server')
            and callable(subclass.stop_server)

            or NotImplemented)

    def __init__(self, flags: List):
        self._flags = flags
        self.model = None
        self.view = None
        self._ip_address = 'localhost'

    @abstractmethod
    def is_client_connected(self) -> bool:
        raise NotImplementedError

    @abstractmethod
    def start_gui(self):
        raise NotImplementedError

    @abstractmethod
    def quit_gui(self):
        raise NotImplementedError

    @abstractmethod
    def absolute_path(self, filename: str) -> str:
        raise NotImplementedError

    @property
    @abstractmethod
    def ip_address(self) -> str:
        raise NotImplementedError

    @ip_address.setter
    @abstractmethod
    def ip_address(self, ip: str):
        raise NotImplementedError

    @abstractmethod
    def start_server(self, ip_address: str):
        raise NotImplementedError

    @abstractmethod
    def stop_server(self):
        raise NotImplementedError
