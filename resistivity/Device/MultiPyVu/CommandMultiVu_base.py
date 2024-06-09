# -*- coding: utf-8 -*-
"""
This is a base class factory method to call lup the specific MultiVu commands

Created on Sat June 12 17:35:28 2021

@author: djackson
"""

from abc import abstractmethod
from typing import Tuple

from .ICommand import ICommand
from .exceptions import MultiPyVuError


class CommandMultiVuBase():
    def __init__(self, cmd_dict: dict):
        self.cmd_dict = cmd_dict

    def _check_command_name(self, input_command):
        if input_command not in self.cmd_dict:
            raise MultiPyVuError(f'Unknown command: "{input_command}".')

    @abstractmethod
    def _get_state_imp(self, mv_command: ICommand, params: str = '') -> Tuple:
        raise NotImplementedError

    def get_state(self, command: str, params: str = '') -> str:
        '''
        Gets and returns a query from MultiVu.

        Parameters
        ----------
        command: str
            The name of the command.  Possible choices are the keys
            listed in .cmd_dict.
        params: str, optional
            Input parameters for the command.  Used for reading SDO's

        Raises
        ------
        MultiVuExeException
            Raises an error if the command is not in the cmd_dict.

        Returns
        -------
        str
            result_string, units, code_in_words.

        '''
        self._check_command_name(command)
        mv_command = self.cmd_dict[command]
        try:
            result, status_number = self._get_state_imp(mv_command, params)
        except AttributeError as e:
            raise MultiPyVuError(f'Potential threading error:  {e}')
        try:
            # Get the translated state code
            code_in_words = mv_command.convert_state_dictionary(status_number)
        except KeyError:
            msg = f'Returning value = {result} and '
            msg += f'status = {status_number}, '
            msg += 'which could mean MultiVu is not running.'
            raise MultiPyVuError(msg)

        result_string = result if type(result) == str else f'{result:.4f}'
        return f'{result_string},{mv_command.units},{code_in_words}'

    def set_state(self, command, arg_string) -> str:
        '''
        Sets the state for a given command using the arg_string for parameters

        Parameters
        ----------
        command : str
            The name of the command.  Possible choices are the keys
            listed in .cmd_dict.
        arg_string : str
            The arguments that should be passed on to the command.
                TEMP: set point, rate, mode
                FIELD: set point, rate, approach, and magnetic state.
                CHAMBER: mode

        Returns:
        --------
        str:  Error message

        Raises
        ------
        MultiVuExeException
            Raises an error if the command is not in the cmd_dict.
        '''
        self._check_command_name(command)
        mv_command = self.cmd_dict[command]
        try:
            err = mv_command.set_state_server(arg_string)
        except MultiPyVuError as e:
            raise MultiPyVuError(e.value) from e
        else:
            if isinstance(err, int):
                if err == 0:
                    return f'{command} Command Received'
                else:
                    msg = f'Error when setting the {command} {arg_string}: '
                    msg += f'error = {err}'
                    raise MultiPyVuError(msg)
                
            if isinstance(err, str):
                can_error_msg = mv_command.convert_state_dictionary(err)
                if can_error_msg == 'Call was successful':
                    return f'{command} Command Received'
                else:
                    msg = f'Error when setting the {command} {arg_string}: '
                    msg += f'{can_error_msg}'
                    raise MultiPyVuError(msg)
