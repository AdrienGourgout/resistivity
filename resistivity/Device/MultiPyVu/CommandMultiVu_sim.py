# -*- coding: utf-8 -*-
"""
This is a base class factory method to call lup the specific MultiVu commands

Created on Sat June 12 17:35:28 2021

@author: djackson
"""

from typing import Tuple

from .CommandMultiVu_base import CommandMultiVuBase
from .ICommand import ICommand


class CommandMultiVuSim(CommandMultiVuBase):
    def __init__(self, cmd_dict: dict):
        super().__init__(cmd_dict)

    def _get_state_imp(self, mv_command: ICommand,
                       params: str = '') -> Tuple:
        value_variant = None
        state_variant = None
        result, status_number = mv_command.get_state_server(value_variant,
                                                            state_variant,
                                                            params)
        return (result, status_number)
