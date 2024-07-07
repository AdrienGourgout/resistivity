"""
This provides an interface for MultiVu commands (CommandTemperature,
                                                 CommandField,
                                                 and CommandChamber)

It requires ABCplus (Abstract Base Class plus), which is found here:
    https://pypi.org/project/abcplus/

Created on Tue May 18 12:59:24 2021

@author: djackson
"""

from typing import Union, Dict, Tuple
from abc import ABC, abstractmethod


class ICommand(ABC):
    @classmethod
    def __subclasshook__(cls, subclass):
        return (
            hasattr(subclass, 'convert_result')
            and callable(subclass.convert_result) and

            hasattr(subclass, 'prepare_query')
            and callable(subclass.prepare_query) and

            hasattr(subclass, 'convert_state_dictionary')
            and callable(subclass.convert_state_dictionary) and

            hasattr(subclass, 'get_state_server')
            and callable(subclass.get_state_server) and

            hasattr(subclass, 'set_state_server')
            and callable(subclass.set_state_server) and

            hasattr(subclass, 'state_code_dict')
            and callable(subclass.state_code_dict)

            or NotImplemented)

    @abstractmethod
    def __init__(self):
        self.units = ''

    @abstractmethod
    def convert_result(self, result: Dict) -> Tuple:
        raise NotImplementedError

    @abstractmethod
    def prepare_query(self, *args):
        raise NotImplementedError

    @abstractmethod
    def convert_state_dictionary(self, statusNumber):
        raise NotImplementedError

    @abstractmethod
    def get_state_server(self, statusCode, stateValue, params: str = ''):
        raise NotImplementedError

    @abstractmethod
    def set_state_server(self, arg_string: str) -> Union[str, int]:
        raise NotImplementedError

    @abstractmethod
    def state_code_dict(self) -> Dict:
        raise NotImplementedError
