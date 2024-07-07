"""
CommandTemperature.py has the information required to get and set the
temperature state.

Created on Tue May 18 13:14:28 2021

@author: djackson
"""

from sys import platform
from enum import IntEnum
import time
from threading import Thread, Lock
from typing import Union, Tuple, Dict
from abc import abstractmethod

from .ICommand import ICommand
from .exceptions import MultiPyVuError, PythoncomImportError

if platform == 'win32':
    try:
        import win32com.client as win32
        from pywintypes import com_error as pywin_com_error
    except ImportError:
        raise PythoncomImportError


class ApproachEnum(IntEnum):
    fast_settle = 0
    no_overshoot = 1


units = 'K'

############################
#
# Base Class
#
############################


class CommandTemperatureBase(ICommand):
    def __init__(self):
        super().__init__()

        # Temperature state code dictionary
        self._state_dictionary = {
            1: "Stable",
            2: "Tracking",
            5: "Near",
            6: "Chasing",
            7: "Pot Operation",
            10: "Standby",
            13: "Diagnostic",
            14: "Impedance Control Error",
            15: "General Failure",
        }

        self.approach_mode = ApproachEnum

        self.units = units

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
            t, _, status = r
        elif len(r) == 1:
            t = '0.0'
            [status] = r
        else:
            msg = f'Invalid response: {response}'
            raise MultiPyVuError(msg)
        temperature = float(t)
        return temperature, status

    def prepare_query(self,
                      set_point: float,
                      rate_per_minute: float,
                      approach_mode: IntEnum) -> str:
        try:
            set_point = float(set_point)
        except ValueError:
            err_msg = 'set_point must be a float (set_point = '
            err_msg += "'{set_point}')"
            raise ValueError(err_msg)

        try:
            rate_per_minute = float(rate_per_minute)
            rate_per_minute = abs(rate_per_minute)
        except ValueError:
            err_msg = 'rate_per_minute must be a float '
            err_msg += f'(rate_per_minute = \'{rate_per_minute}\')'
            raise ValueError(err_msg)

        return f'{set_point},{rate_per_minute},{approach_mode.value}'

    def convert_state_dictionary(self, status_number):
        if isinstance(status_number, str):
            return status_number
        else:
            return self._state_dictionary[status_number]

    def state_code_dict(self):
        return self._state_dictionary

    @abstractmethod
    def get_state_server(self, arg_string: str) -> Union[str, int]:
        raise NotImplementedError

    @abstractmethod
    def _set_state_imp(self,
                       temperature: float,
                       set_rate_per_min: float,
                       set_approach: int
                       ) -> Union[str, int]:
        raise NotImplementedError

    def set_state_server(self, arg_string: str) -> Union[str, int]:
        if len(arg_string.split(',')) != 3:
            err_msg = 'Setting the temperature requires three numeric inputs, '
            err_msg += 'separated by a comma: '
            err_msg += 'Set Point (K), '
            err_msg += 'rate (K/min), '
            err_msg += 'approach:'
            for mode in self.approach_mode:
                err_msg += f'\n\t{mode.value}: approach_mode.{mode.name}'
            return err_msg
        temperature, rate, approach = arg_string.split(',')
        temperature = float(temperature)
        if temperature < 0:
            err_msg = "Temperature must be a positive number."
            return err_msg
        set_rate_per_min = float(rate)
        set_approach = int(approach)
        if set_approach > len(self.approach_mode) - 1:
            err_msg = f'The approach, {approach}, is out of bounds.  Must be '
            err_msg += 'one of the following'
            for mode in self.approach_mode:
                err_msg += f'\n\t{mode.value}: approach_mode.{mode.name}'
            return err_msg
        return self._set_state_imp(temperature,
                                   set_rate_per_min,
                                   set_approach)


############################
#
# Standard Implementation
#
############################

class CommandTemperatureImp(CommandTemperatureBase):
    def __init__(self, multivu_win32com, instrument_name):
        '''
        Parameters:
        ----------
        multivu_win32com: Union[win32.dynamic.CDispatch, None]
        mvu_flavor: str
        '''
        super().__init__()
        self._mvu = multivu_win32com
        self.instrument_name = instrument_name

    def get_state_server(self, value_variant, state_variant, params=''):
        can_error = self._mvu.GetTemperature(value_variant, state_variant)
        if can_error > 0:
            raise MultiPyVuError('Error when calling GetTemperature()')
        temperature = value_variant.value
        return_state = int(state_variant.value)

        return temperature, return_state

    def _set_state_imp(self,
                       temperature: float,
                       set_rate_per_min: float,
                       set_approach: int
                       ) -> Union[str, int]:
        try:
            can_error = self._mvu.SetTemperature(temperature,
                                             set_rate_per_min,
                                             set_approach)
        except pywin_com_error:
            raise MultiPyVuError('No pywin32 connection to MultiVu.  Is MultiVu running?')
        else:
            if self.instrument_name == 'PPMS':
                if can_error > 1:
                    raise MultiPyVuError('Error when calling SetTemperature()')
                else:
                    # returning this string makes CommandMultiVu_base happy
                    return 'Call was successful'
            elif can_error > 0:
                raise MultiPyVuError('Error when calling SetTemperature()')
        return can_error


############################
#
# Scaffolding Implementation
#
############################


class CommandTemperatureSim(CommandTemperatureBase):
    def __init__(self):
        super().__init__()

        CommandTemperatureSim.set_point = 300
        CommandTemperatureSim.set_rate_per_min = 1
        CommandTemperatureSim.set_approach = 1
        CommandTemperatureSim.return_state = 1
        CommandTemperatureSim._thread_running = False
        CommandTemperatureSim.delta_seconds = 0.3

    def get_state_server(self, value_variant, state_variant, params=''):
        return CommandTemperatureSim.set_point, CommandTemperatureSim.return_state

    def _set_state_imp(self,
                       temperature: float,
                       set_rate_per_min: float,
                       set_approach: int
                       ) -> Union[str, int]:
        # stop any other threads
        CommandTemperatureSim._thread_running = False
        time.sleep(2*CommandTemperatureSim.delta_seconds)
        mutex = Lock()
        CommandTemperatureSim.set_rate_per_min = set_rate_per_min
        CommandTemperatureSim.set_approach = set_approach
        T = Thread(target=self._simulate_temperature_change,
                   name='set_state_server temperature',
                   args=(temperature, set_rate_per_min, mutex),
                   daemon=True)
        CommandTemperatureSim._thread_running = True
        T.start()
        error = 0
        return error

    def _simulate_temperature_change(self, temp: float,
                                     rate_per_min: float,
                                     mutex: Lock):
        starting_temp = CommandTemperatureSim.set_point
        mutex.acquire()
        CommandTemperatureSim.return_state = 1
        mutex.release()
        delta_seconds = 0.3
        start_time = time.time()
        while time.time() - start_time < 1:
            time.sleep(delta_seconds)
            if not CommandTemperatureSim._thread_running:
                return

        delta_temp = temp - starting_temp
        rate_per_sec = rate_per_min / 60
        rate_per_sec *= -1 if delta_temp < 0 else 1
        rate_time = delta_temp / rate_per_sec
        start_time = time.time()
        mutex.acquire()
        CommandTemperatureSim.return_state = 2
        mutex.release()
        while (time.time() - start_time) < rate_time:
            time.sleep(delta_seconds)
            mutex.acquire()
            CommandTemperatureSim.set_point += delta_seconds * rate_per_sec
            mutex.release()
            if not CommandTemperatureSim._thread_running:
                return

        mutex.acquire()
        CommandTemperatureSim.return_state = 5
        mutex.release()
        start_time = time.time()
        while time.time() - start_time < 5:
            time.sleep(delta_seconds)
            if not CommandTemperatureSim._thread_running:
                return
        mutex.acquire()
        CommandTemperatureSim.set_point = temp
        CommandTemperatureSim.return_state = 1
        mutex.release()
