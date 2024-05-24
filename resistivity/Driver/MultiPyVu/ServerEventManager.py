'''
ServerEventManager.py has the base classes for the events
using the Observer design pattern.
'''

from abc import ABC, abstractmethod
from typing import List


class IObserver(ABC):
    @classmethod
    def __subclasshook__(cls, subclass):
        return (
            hasattr(subclass, 'update')
            and callable(subclass.update)
            or NotImplemented)

    @abstractmethod
    def update(self) -> None:
        raise NotImplementedError


class Subject():
    def __init__(self):
        self._events: List[IObserver] = []

    def subscribe(self, observer: IObserver) -> None:
        if observer not in self._events:
            self._events.append(observer)

    def unsubscribe(self, observer: IObserver) -> None:
        try:
            self._events.remove(observer)
        except ValueError:
            pass

    def notify(self) -> None:
        for observer in self._events:
            observer.update()
