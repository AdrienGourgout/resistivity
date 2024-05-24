# -*- coding: utf-8 -*-
"""
CommandChamber has the information required to get and set the chamber state.

Created on Tue May 18 13:14:28 2021

@author: djackson
"""

from sys import platform
from abc import abstractmethod
from enum import IntEnum
from typing import Union, Dict, Tuple

from .exceptions import MultiPyVuError, PythoncomImportError
from .ICommand import ICommand


if platform == 'win32':
    try:
        import win32com.client as win32
        from pywintypes import com_error as pywin_com_error
    except ImportError:
        raise PythoncomImportError


class modeEnum(IntEnum):
    seal = 0
    purge_seal = 1
    vent_seal = 2
    pump_continuous = 3
    vent_continuous = 4
    high_vacuum = 5


units = ''

############################
#
# Base Class
#
############################


class CommandChamberBase(ICommand):
    def __init__(self, instrument_name: str):
        super().__init__()
        self.instrument_name = instrument_name

        # State code dictionary
        self.__state_dictionary = {
            0: 'Unknown',
            1: 'Purged and Sealed',
            2: 'Vented and Sealed',
            3: 'Sealed (condition unknown)',
            4: 'Performing Purge/Seal',
            5: 'Performing Vent/Seal',
            6: 'Pre-HiVac',
            7: 'HiVac',
            8: 'Pumping Continuously',
            9: 'Flooding Continuously',
            14: 'HiVac Error',
            15: 'General Failure'
        }

        self.mode = modeEnum

        self.units = units

    def mode_setting_correct(self,
                             mode_setting: IntEnum,
                             mode_readback):
        if mode_setting == self.mode.seal:
            returnTrue = [self.__state_dictionary[1],
                          self.__state_dictionary[2],
                          self.__state_dictionary[3],
                          ]
            if mode_readback in returnTrue:
                return True
        elif mode_setting == self.mode.purge_seal:
            return (mode_readback == self.__state_dictionary[1])
        elif mode_setting == self.mode.vent_seal:
            return (mode_readback == self.__state_dictionary[2])
        elif mode_setting == self.mode.pump_continuous:
            return (mode_readback == self.__state_dictionary[8])
        elif mode_setting == self.mode.vent_continuous:
            return (mode_readback == self.__state_dictionary[9])
        elif mode_setting == self.mode.high_vacuum:
            return (mode_readback == self.__state_dictionary[7])

    def convert_result(self, response: Dict) -> Tuple:
        '''
        Converts the CommandMultiVu response from get_state()
        to something usable for the user.

        Parameters:
        -----------
        response: Dict:
            command, result_string, code_in_words

        Returns:
        --------
        Value and error status returned from read/write
        '''
        r = response['result'].split(',')
        if len(r) == 3:
            n = 2
        elif len(r) == 1:
            n = 0
        else:
            msg = f'Invalid response: {response}'
            raise MultiPyVuError(msg)
        return ('', r[n])

    def prepare_query(self, mode: IntEnum) -> str:
        try:
            mode_as_int = mode.value
        except ValueError:
            msg = 'mode must be an integer. One could use the .modeEnum'
            raise ValueError(msg)
        return f'{mode_as_int}'

    def convert_state_dictionary(self, status_number):
        return self.__state_dictionary[status_number]

    @abstractmethod
    def get_state_server(self, value_variant, state_variant,  params=''):
        raise NotImplementedError

    @abstractmethod
    def set_state_server_imp(self, mode: int) -> Union[str, int]:
        raise NotImplementedError

    def set_state_server(self, arg_string) -> Union[str, int]:
        if self.instrument_name == 'OPTICOOL':
            err_msg = 'set_chamber() is not available for the OptiCool'
            raise MultiPyVuError(err_msg)
        if len(arg_string.split(',')) != 1:
            err_msg = 'Setting the chamber requires 1 input: mode'
            return err_msg
        set_mode = int(arg_string)
        if set_mode > len(self.mode) - 1:
            err_msg = f'The selected mode, {set_mode}, is '
            err_msg += 'out of bounds.  Must be one of the following:'
            for m in self.mode:
                err_msg += f'\n\t{m.value}: {m.name}'
            raise MultiPyVuError(err_msg)
        return self.set_state_server_imp(set_mode)

    def state_code_dict(self):
        return self.__state_dictionary


############################
#
# Standard Implementation
#
############################


class CommandChamberImp(CommandChamberBase):
    def __init__(self, multivu_win32com, instrument_name):
        '''
        Parameters:
        ----------
        multivu_win32com: Union[win32.dynamic.CDispatch, None]
        instrument_name: str
        '''
        super().__init__(instrument_name)
        self._mvu = multivu_win32com

    def get_state_server(self, value_variant, state_variant,  params=''):
        if self.instrument_name == 'OPTICOOL':
            err_msg = 'get_chamber() is not available for the OptiCool'
            raise MultiPyVuError(err_msg)
        error = self._mvu.GetChamber(state_variant)
        if error > 0:
            raise MultiPyVuError('Error when calling GetChamber()')
        return_state = int(state_variant.value)

        return '', return_state

    def set_state_server_imp(self, mode: int) -> Union[str, int]:
        error = self._mvu.SetChamber(mode)
        if error > 0:
            raise MultiPyVuError('Error when calling SetChamber()')
        return error


############################
#
# Scaffolding Implementation
#
############################


class CommandChamberSim(CommandChamberBase):
    def __init__(self, instrument_name: str):
        super().__init__(instrument_name)

        CommandChamberSim.set_mode = 1
        CommandChamberSim.return_state = 1

    def get_state_server(self, value_variant, state_variant,  params=''):
        if self.instrument_name == 'OPTICOOL':
            err_msg = 'get_chamber() is not available for the OptiCool'
            raise MultiPyVuError(err_msg)
        return '', CommandChamberSim.return_state

    def set_state_server_imp(self, mode: int) -> Union[str, int]:
        CommandChamberSim.set_mode = mode
        if mode == self.mode.seal.value:
            CommandChamberSim.return_state = 3
        elif (mode == self.mode.purge_seal.value
                or mode == self.mode.vent_seal.value):
            CommandChamberSim.return_state = mode
        elif mode == self.mode.pump_continuous.value:
            CommandChamberSim.return_state = 8
        elif mode == self.mode.vent_continuous.value:
            CommandChamberSim.return_state = 9
        elif mode == self.mode.high_vacuum.value:
            CommandChamberSim.return_state = 7
        error = 0
        return error
