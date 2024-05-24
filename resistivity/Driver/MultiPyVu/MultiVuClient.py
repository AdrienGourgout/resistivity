#!/usr/bin/env python3
"""
Created on Mon Jun 7 23:47:19 2021

MultiVuClient.py is a module for use on a network that has access to a
computer running MultiVuServer.py.  By running this client, a python script
can be used to control a Quantum Design cryostat.

This inherits the MultiVuClientBase class.  The base has the basic 
communication commands, and this has specific commands for communicating
with MultiVu.

@author: D. Jackson
"""

from sys import exc_info
from enum import IntEnum
import time
from threading import Thread, Lock
import traceback
from typing import Union, Tuple

from .MultiVuClient_base import ClientBase
from .instrument import InstrumentList
from . import Command_factory
from .CommandTemperature import ApproachEnum as temperature_approach_mode
from .CommandTemperature import units as temperature_units
from .CommandField import ApproachEnum as field_approach_mode
from .CommandField import drivenEnum
from .CommandField import units as field_units
from .CommandChamber import modeEnum
from .CommandChamber import units as chamber_units
from .sdo_object import SdoObject, val_type
from .BRT import Brt
from .project_vars import (HOST,
                           PORT,
                           )
from .exceptions import (MultiPyVuError,
                         ServerCloseError,
                         CanError,
                         can_err_enum,
                         abort_err_enum,
                         )


class Client(ClientBase):
    '''
    This class is used for a client to connect to a computer with
    MutliVu running MultiVuServer.py.

    Parameters
    ----------
    host: str (optional)
        The IP address for the server.  Default is 'localhost.'
    port: int (optional)
        The port number to use to connect to the server.
    socket_timeout: float, None (optional)
        The time in seconds that the client will wait to try
        and connect to the server.  Value of None will wait
        indefinitely.  Default is 2.5 sec.
    '''
    class TemperatureAdapter():
        def __init__(self):
            t_class = Command_factory.create_command_temp()
            self.units = temperature_units
            self.approach_mode = temperature_approach_mode
            self.state_code_dict = t_class.state_code_dict
            self.waitfor = 1
    temperature = TemperatureAdapter()

    class FieldAdapter():
        def __init__(self):
            self.units = field_units
            self.approach_mode = field_approach_mode
            self.driven_mode = drivenEnum
            f_class = Command_factory.create_command_field()
            self.state_code_dict = f_class.state_code_dict
            self.waitfor = 2
    field = FieldAdapter()

    class ChamberAdapter():
        def __init__(self):
            self.units = chamber_units
            self.mode = modeEnum
            c_class = Command_factory.create_command_chamber()
            self.state_code_dict = c_class.state_code_dict
            self.waitfor = 4
    chamber = ChamberAdapter()

    def __init__(self,
                 host: str = HOST,
                 port: int = PORT,
                 socket_timeout: Union[float, None] = 2.5,
                 ):
        super().__init__(host, port, socket_timeout)
        self.resistivity = Brt(self)
        '''
        The resistivity option provides capabilities to measure
        electrical resistance.  This includes configuring the
        measurements from within python.
        '''

        self._thread_running = False

        class Subsystem(IntEnum):
            no_subsystem = 0
            temperature = 1
            field = 2
            chamber = 4
        self.subsystem = Subsystem

        # variables to hold the set points and status info
        self._set_pointT = 300.0
        self._set_pointH = 0.0
        self._set_chamb = self.chamber.mode.seal

    ###########################
    #  Command Methods
    ###########################

    def get_sdo(self, sdo_obj: SdoObject) -> Tuple[Union[float, str], str]:
        '''
        This returns the value of an sdo query.

        Parameters:
        -----------
        sdo_obj: sdo_object

        Returns
        -------
        A tuple of (value, status).
        '''
        if self._message is None:
            raise ServerCloseError('Not connected to the server')
        response = self.query_server('SDO?', str(sdo_obj))
        try:
            can_sdo = Command_factory.create_command_sdo()
            value, status = can_sdo.convert_result(response)
        except MultiPyVuError as e:
            tb = traceback.extract_tb(exc_info()[2])
            formatted_traceback = ''.join(traceback.format_list(tb))
            self.logger.info(f'{e}\nTraceback:\n {formatted_traceback}')
            value = 0
            status = e.value
        return value, status

    def set_sdo(self,
                sdo_obj: SdoObject,
                write_val: Union[str, int, float]) -> None:
        '''
        This sets an SDO value.

        Parameters:
        -----------
        sdo_obj: sdo_object

        write_val: str or int or float
            The value to be written.  The type must match the type
            specified in the sdo_object.

        Returns
        -------
        None.

        '''
        try:
            can_sdo = Command_factory.create_command_sdo()
            query = can_sdo.prepare_query(write_val, sdo_obj)
        except ValueError as e:
            self.logger.info(e)
            raise ValueError

        self.query_server('SDO', query)

    def get_temperature(self) -> Tuple[float, str]:
        '''
        This gets the current temperature, in Kelvin, from MultiVu.

        Returns
        -------
        A tuple of (temperature, status).

        '''
        response = self.query_server('TEMP?', '')
        try:
            temperature = Command_factory.create_command_temp()
            temperature, status = temperature.convert_result(response)
        except MultiPyVuError as e:
            tb = traceback.extract_tb(exc_info()[2])
            formatted_traceback = ''.join(traceback.format_list(tb))
            self.logger.info(f'{e}\nTraceback:\n {formatted_traceback}')
            temperature = 0
            status = e.value
        return temperature, status

    def set_temperature(self,
                        set_point: float,
                        rate_per_min: float,
                        approach_mode: IntEnum
                        ):
        '''
        This sets the temperature.

        Parameters
        ----------
        set_point : float
            The desired temperature, in Kelvin.
        rate_per_min : float
            The rate of change of the temperature in K/min
        approach_mode : IntEnum
            This uses the MultiVuClient.temperature.approach_mode enum.
            Options are:
                temperature.approach_mode.fast_settle
                temperature.approach_mode.no_overshoot

        Returns
        -------
        None.
        '''
        temperature = Command_factory.create_command_temp()
        try:
            query = temperature.prepare_query(set_point,
                                              rate_per_min,
                                              approach_mode,
                                              )
            self._set_pointT = set_point
        except ValueError as e:
            self.logger.info(e)
            raise ValueError
        else:
            self.query_server('TEMP', query)

    def get_aux_temperature(self) -> Tuple[float, str]:
        '''
        This is used to get the OptiCool auxiliary temperature,
        in Kelvin.  This command gets it's value directly from
        the OptiCool rather than reading the value from MultiVu.

        Returns:
        --------
        A tuple of (temperature, read_status).

        Raises:
        -------
        MultiPyVuException
            This command is only used for OptiCool
        '''
        if self.instrument_name != InstrumentList.OPTICOOL.name:
            msg = "'get_aux_temperature()' is only used for OptiCool"
            raise MultiPyVuError(msg)
        sdo = SdoObject(3, 0x6001, 0x4, val_type.double_t)
        temperature, status = self.get_sdo(sdo)
        return float(temperature), status

    def __monitor_temp_stability(self, timeout_sec, mutex):
        '''
        This private method is used to monitor the temperature. It waits for
        the status to become not 'stable,' and then waits again for the status
        to become 'stable.'

        Parameters
        ----------
        timeout_sec : float
            This is the timeout set by the user for when the temperature
            monitoring will quit, even if the temperature is not stable.
        mutex : threading.Lock
            The mutex lock.

        Returns
        -------
        None.

        '''
        start = time.time()
        mutex.acquire()
        t, status = self.get_temperature()
        mutex.release()
        max_time_to_start = 5.0
        while status == 'Stable':
            time.sleep(0.3)
            mutex.acquire()
            t, status = self.get_temperature()
            mutex.release()
            measure_time = time.time()
            if measure_time - start > max_time_to_start:
                break
            if timeout_sec > 0:
                if measure_time - start > timeout_sec:
                    return
            # check if the main thread has killed this process
            if not self._thread_running:
                return

        while status != 'Stable':
            time.sleep(0.3)
            mutex.acquire()
            t, status = self.get_temperature()
            mutex.release()
            if timeout_sec > 0:
                if time.time() - start > timeout_sec:
                    return
            # check if the main thread has killed this process
            if not self._thread_running:
                return

    def get_field(self) -> Tuple[float, str]:
        '''
        This gets the current field, in Oe, from MultiVu.

        Returns
        -------
        A tuple of (field, status)

        '''
        response = self.query_server('FIELD?', '')
        try:
            field = Command_factory.create_command_field()
            field, status = field.convert_result(response)
        except MultiPyVuError as e:
            tb = traceback.extract_tb(exc_info()[2])
            formatted_traceback = ''.join(traceback.format_list(tb))
            self.logger.info(f'{e}\nTraceback:\n {formatted_traceback}')
            field = 0
            status = e.value
        return field, status

    def set_field(self,
                  set_point: float,
                  rate_per_sec: float,
                  approach_mode: IntEnum,
                  driven_mode=None,
                  ):
        '''
        This sets the magnetic field.

        Parameters
        ----------
        set_point : float
            The desired magnetic field, in Oe.
        rate_per_sec : float
            The ramp rate, in Oe/sec.
        approach_mode : IntEnum
            This uses the .field_approach_mode enum.  Options are:
                field.approach_mode.linear
                field.approach_mode.no_overshoot
                field.approach_mode.oscillate
        driven_mode : IntEnum, Only used for PPMS
            This uses the .field.driven_mode, and is only used
            by the PPMS, for which the options are:
                .field.driven_mode.Persistent
                .field.driven_mode.Driven

        Raises
        ------
        ValueError
            Thrown if the set_point and rate_per_sec are not numbers.

        Returns
        -------
        None.

        '''
        try:
            field = Command_factory.create_command_field()
            query = field.prepare_query(set_point,
                                        rate_per_sec,
                                        approach_mode,
                                        driven_mode)
            self._set_pointH = set_point
        except ValueError as e:
            self.logger.info(e)
            raise ValueError
        else:
            self.query_server('FIELD', query)

    def __monitor_field_stability(self, timeout_sec, mutex):
        '''
        This private method is used to monitor the magnetic field. It waits for
        the status to start with 'Holding,' and then waits again for the status
        to not start with 'Holding.'

        Parameters
        ----------
        timeout_sec : float
            This is the timeout set by the user for when the field
            monitoring will quit, even if the field is not stable.
        mutex : threading.Lock
            The mutex lock.

        Returns
        -------
        None.

        '''
        start = time.time()
        mutex.acquire()
        f, status = self.get_field()
        mutex.release()
        max_time_to_start = 5.0
        while status.startswith('Holding'):
            time.sleep(0.3)
            mutex.acquire()
            f, status = self.get_field()
            mutex.release()
            measure_time = time.time()
            if measure_time - start > max_time_to_start:
                return
            if timeout_sec > 0:
                if measure_time - start > timeout_sec:
                    return
            # check if the main thread has killed this process
            if not self._thread_running:
                return

        while not status.startswith('Holding'):
            time.sleep(0.3)
            mutex.acquire()
            f, status = self.get_field()
            mutex.release()
            if timeout_sec > 0:
                if time.time() - start > timeout_sec:
                    return
            # check if the main thread has killed this process
            if not self._thread_running:
                return

    def get_chamber(self) -> str:
        '''
        This gets the current chamber setting.

        Returns
        -------
        str
            The chamber status.

        '''
        response = self.query_server('CHAMBER?', '')
        chamber = Command_factory.create_command_chamber()
        try:
            status = chamber.convert_result(response)
        except MultiPyVuError as e:
            tb = traceback.extract_tb(exc_info()[2])
            formatted_traceback = ''.join(traceback.format_list(tb))
            self.logger.info(f'{e}\nTraceback:\n {formatted_traceback}')
            status = (0, e.value)
        return status[1]

    def set_chamber(self, mode: IntEnum):
        '''
        This sets the chamber status.

        Parameters
        ----------
        mode : IntEnum
            The chamber is set using the MultiVuClient.chamber.Mode enum.
            Options are:
                chamber.mode.seal
                chamber.mode.purge_seal
                chamber.mode.vent_seal
                chamber.mode.pump_continuous
                chamber.mode.vent_continuous
                chamber.mode.high_vacuum

        Raises
        ------
        MultiVuExeException

        Returns
        -------
        None.

        '''
        try:
            chamber = Command_factory.create_command_chamber()
            query = chamber.prepare_query(mode)
        except ValueError as e:
            self.logger.info(e)
            raise ValueError
        else:
            self._set_chamb = mode
            self.query_server('CHAMBER', query)

    def __monitor_chamber_stability(self, timeout_sec, mutex):
        start = time.time()
        mutex.acquire()
        mode = self.get_chamber()
        mutex.release()

        chamber = Command_factory.create_command_chamber()
        while not chamber.mode_setting_correct(self._set_chamb, mode):
            time.sleep(0.3)
            mutex.acquire()
            mode = self.get_chamber()
            mutex.release()
            if timeout_sec > 0:
                if time.time() - start > timeout_sec:
                    return
            # check if the main thread has killed this process
            if not self._thread_running:
                return

    def wait_for(self, delay_sec, timeout_sec=0, bitmask=0):
        '''
        This command pauses the code until the specified criteria are met.

        Parameters
        ----------
        delay_sec : float
            Time in seconds to wait after stability is reached.
        timeout_sec : float, optional
            If stability is not reached within timeout (in seconds), the
            wait is abandoned. The default timeout is 0, which indicates this
            feature is turned off (i.e., to wait forever for stability).
        bitmask : int, optional
            This tells wait_for which parameters to wait on.  The best way
            to set this parameter is to use the MultiVuClient.subsystem enum,
            using bitewise or to wait for multiple parameters.  For example,
            to wait for the temperature and field to stabilize, one would set
            bitmask = (Client.temperature.waitfor
                       | MultiVuClient.field.waitfor).
            The default is MultiVuClient.no_subsystem (which is 0).

        '''
        max_mask = self.temperature.waitfor | self.field.waitfor
        if self.instrument_name != InstrumentList.OPTICOOL.name:
            max_mask = max_mask | self.chamber.waitfor
        if bitmask > max_mask:
            err_msg = f'The mask, {bitmask}, is out of bounds.  Must be '
            err_msg += 'one of the following'
            for s in self.subsystem:
                if (self.instrument_name != InstrumentList.OPTICOOL.name
                        and s is not self.chamber.waitfor):
                    err_msg += f'\n\t{s.name}: {s.value}'
            raise MultiPyVuError(err_msg)

        mutex = Lock()
        threads = list()
        # stop any other threads
        self._thread_running = False
        if (bitmask & self.temperature.waitfor
                == self.temperature.waitfor):
            t = Thread(target=self.__monitor_temp_stability,
                       name='wait_for temperature',
                       args=(timeout_sec, mutex))
            threads.append(t)
            self._thread_running = True
            t.start()
        if bitmask & self.field.waitfor == self.field.waitfor:
            f = Thread(target=self.__monitor_field_stability,
                       name='wait_for field',
                       args=(timeout_sec, mutex))
            threads.append(f)
            self._thread_running = True
            f.start()
        if bitmask & self.chamber.waitfor == self.chamber.waitfor:
            c = Thread(target=self.__monitor_chamber_stability,
                       name='wait_for chamber',
                       args=(timeout_sec, mutex))
            threads.append(c)
            self._thread_running = True
            c.start()

        for thread in threads:
            thread.join()
        time.sleep(delay_sec)
