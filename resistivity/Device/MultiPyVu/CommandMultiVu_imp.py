# -*- coding: utf-8 -*-
"""
This is a base class factory method to call lup the specific MultiVu commands

Created on Sat June 12 17:35:28 2021

@author: djackson
"""

from sys import platform
from typing import Tuple

from .CommandMultiVu_base import CommandMultiVuBase
from .ICommand import ICommand
from .exceptions import PythoncomImportError


if platform == 'win32':
    try:
        import win32com.client as win32
        import pythoncom
    except ImportError:
        raise PythoncomImportError


class CommandMultiVuImp(CommandMultiVuBase):
    def __init__(self, cmd_dict: dict):
        super().__init__(cmd_dict)

    def _get_state_imp(self, mv_command: ICommand,
                       params: str = '') -> Tuple:

        # Setting up a by-reference (VT_BYREF) double (VT_R8)
        # variant.  This is used to get the value.
        value_variant = (win32.VARIANT(
            pythoncom.VT_BYREF | pythoncom.VT_R8, 0.0))
        # Setting up a by-reference (VT_BYREF) integer (VT_I4)
        # variant.  This is used to get the status code.
        state_variant = (win32.VARIANT(
            pythoncom.VT_BYREF | pythoncom.VT_I4, 0))
        result, status_number = mv_command.get_state_server(value_variant,
                                                            state_variant,
                                                            params)
        return (result, status_number)
