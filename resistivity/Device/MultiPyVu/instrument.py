"""
instrument.py is used to hold information about MultiVu.  It has
the various flavors, and can determine which version of MultiVu is installed
on a machine.

Created on Tue May 18 13:14:28 2021

@author: djackson
"""

from sys import platform
import subprocess
import time
import re
import logging
from enum import Enum, auto
from typing import Tuple

from .Command_factory import create_command_mv
from .project_vars import SERVER_NAME, PYWIN32_VERSION, MIN_PYWIN32_VERSION
from .exceptions import MultiPyVuError, PythoncomImportError
from .__version import __version__ as mpv_version

if platform == 'win32':
    try:
        import pythoncom
        import win32com.client as win32
    except ImportError:
        raise PythoncomImportError


class InstrumentList(Enum):
    DYNACOOL = auto()
    PPMS = auto()
    VERSALAB = auto()
    MPMS3 = auto()
    OPTICOOL = auto()
    na = auto()


class Instrument():
    def __init__(self,
                 flavor: str = '',
                 scaffolding_mode: bool = False,
                 run_with_threading: bool = False,
                 verbose: bool = False
                 ):
        '''
        This class is used to detect which flavor of MultiVu is installed
        on the computer.  It is also used to return the name of the .exe
        and the class ID, which can be used by win32com.client.

        Parameters
        ----------
        flavor : string, optional
            This is the common name of the MultiVu flavor being used.  If
            it is left blank, then the class finds the installed version
            of MultiVu to know which flavor to use.  The default is ''.
        scaffolding_mode : bool, optional
            This flag puts the class in scaffolding mode, which simulates
            MultiVu.  The default is False.
        run_with_threading : bool, optional
            This flag is used to configure win32com.client to be used in
            a separate thread.  The default is False.
        verbose : bool, optional
            When set to True, the flavor of MultiVu is displayed
            on the command line. The default is False.
        '''
        # keep track of the number of times Instrument is instantiated
        self.logger = logging.getLogger(SERVER_NAME)
        self.scaffolding_mode = scaffolding_mode
        self.run_with_threading = run_with_threading
        self.verbose = verbose

        if (not self.scaffolding_mode) and (platform == 'win32'):
            if PYWIN32_VERSION < MIN_PYWIN32_VERSION:
                err_msg = f'Must use pywincom version {MIN_PYWIN32_VERSION} '
                err_msg += f'or higher (found version {PYWIN32_VERSION})'
                raise MultiPyVuError(err_msg)

        self.name = ''
        if flavor == '':
            if self.scaffolding_mode:
                err_msg = 'Must choose a MultiVu flavor to run in '
                err_msg += 'scaffolding mode.'
                for f in InstrumentList:
                    err_msg += f'\n\t{f.name}' if f != f.na else ''
                raise MultiPyVuError(err_msg)
        else:
            # If specified, check that it's a allowed flavor; if not,
            # print an error
            found = False
            for instrument in InstrumentList:
                if instrument.name.upper() == flavor.upper():
                    self.name = flavor.upper()
                    found = True
                    break
            if not found:
                err_msg = f'The specified MultiVu flavor, {flavor}, is not '
                err_msg += 'recognized. Please use one of the following:'
                for f in InstrumentList:
                    err_msg += f'\n\t{f}'
                raise MultiPyVuError(err_msg)

        self._got_threaded_win32 = False
        self.exe_name = ''
        self.class_id = ''
        self.mv_id = None
        self.multi_vu = None
        self._connect_to_MultiVu(self.name)

    def _exe_to_common_name(self, exe_name: str) -> str:
        '''
        Returns the common name of the MultiVu flavor.

        Parameters
        ----------
        exe_name : str
            The name of the MultiVu flavor executable.

        Returns
        -------
        TYPE
            A string of the specific MultiVu flavor .exe

        '''
        if exe_name.capitalize() == 'PpmsMvu.exe'.capitalize():
            name = InstrumentList.PPMS.name
        elif exe_name.capitalize() == 'SquidVsm.exe'.capitalize():
            name = InstrumentList.MPMS3.name
        elif exe_name.capitalize() == 'VersaLab.exe'.capitalize():
            name = InstrumentList.VERSALAB.name
        elif exe_name.capitalize() == 'OptiCool.exe'.capitalize():
            name = InstrumentList.OPTICOOL.name
        elif exe_name.capitalize() == 'DynaCool.exe'.capitalize():
            name = InstrumentList.DYNACOOL.name
        else:
            raise ValueError(f'{exe_name} is not a recognized executable name')
        return name

    def _get_class_id(self, inst: str) -> str:
        '''
        Parameters
        ----------
        inst : str
            The name of the MultiVu flavor.

        Returns
        -------
        string
            The MultiVu class ID.  Used for things like opening MultiVu.

        '''
        class_id = f'QD.MULTIVU.{inst}.1'
        return class_id

    def _connect_to_MultiVu(self, instrument_name: str) -> None:
        '''
        Detects the flavor of MultiVu running, and then sets
        the exe and class ID private member variables for
        MultiVu and then initializes the win32comm.

        Parameters:
        -----------
        instrument_name: str
            The expected MultiVu flavor.

        Raises:
        -------
        ValueError if the instrument_name does not match the
        automatically detected running flavor.
        MultiPyVuError if running on a non-Windows computer without
        scaffolding mode.
        '''
        if not self.scaffolding_mode:
            if platform != 'win32':
                err_msg  = 'The server only works on a Windows machine. '
                err_msg += 'However, the server\n'
                err_msg += 'can be tested using the -s flag,along with '
                err_msg += 'specifying \n'
                err_msg += 'the MultiVu flavor.'
                raise MultiPyVuError(err_msg)

            self.name, self.exe_name = self.detect_multivu()
            if self.name != instrument_name:
                if instrument_name == '':
                    msg = f'Found {self.name} running.'
                    self.logger.info(msg)
                    msg = f'MultiPyVu Version: {mpv_version}'
                    self.logger.debug(msg)
                else:
                    msg = f'User specified {instrument_name}, but detected '
                    msg += f'{self.name} running. Either leave out a '
                    msg += 'specific MultiVu flavor and use the detected '
                    msg += 'one, or have the specified flavor match the '
                    msg += 'running instance.'
                    raise ValueError(msg)
            self.class_id = self._get_class_id(self.name)
            self.initialize_multivu_win32com()

    def detect_multivu(self) -> Tuple[str, str]:
        '''
        This looks in the file system for a running version of
        MultiVu.  Once it is found, the function returns the a
        tuple with the common name and the executable name.

        Raises
        ------
        MultiVuExeException
            This is thrown if MultiVu is not running, or if multiple
            instances of MultiVu are running.

        Returns
        -------
        tuple[str]
            Returns the (common name, executable name) of the QD instrument.

        '''
        # Build a list of enum, instrumentType
        instrument_names = list(InstrumentList)
        # Remove the last item (called na)
        instrument_names.pop()

        # declare these variables so that they are available to return
        common_name = ''
        exe_name = ''

        # Use WMIC to get the list of running programs with 'multivu'
        # in their path
        cmd = 'WMIC PROCESS WHERE "COMMANDLINE like \'%multivu%\'" GET '
        cmd += 'Caption,Commandline,Processid'
        proc = subprocess.run(cmd, capture_output=True, text=True)
        if proc.returncode != 0:
            raise Exception(proc.stderr)
        # make a dictionary whose key is the MultiVu flavor, and the
        # value is a tuple with the exe path and process id
        exe_search = r'([\w]*).exe[ ]*\"([:\\\w]*.exe)"[ \/\-a-zA-Z]*([0-9]*)'
        open_mv_dict = {}
        for i in proc.stdout.split('\n\n'):
            exe_found = re.findall(exe_search, i)
            if len(exe_found) > 0:
                name, location, process_id = exe_found[0]
                exe_name = name + '.exe'
                common_name = self._exe_to_common_name(exe_name)
                open_mv_dict[common_name] = (location, process_id)

        # Declare errors if to few or too many are found; for one found,
        # declare which version is identified
        if len(open_mv_dict) == 0:
            err_msg  = 'No running instance of MultiVu was detected. Please\n'
            err_msg += 'start MultiVu and retry, or call this script using\n'
            err_msg += 'scaffolding (-s ppms, for example).'
            raise MultiPyVuError(err_msg)
        elif len(open_mv_dict) > 1:
            err_msg = 'There are multiple running instances of '
            err_msg += 'MultiVu running.'
            for flavor in open_mv_dict:
                err_msg += f'\n{open_mv_dict[flavor][0]}'
            err_msg += '\nPlease close all but one and retry, '
            err_msg += 'or specify the flavor to connect to.  See the '
            err_msg += 'help (-h)'
            raise MultiPyVuError(err_msg)
        else:
            name = list(open_mv_dict.keys())[0]
            msg = f"{name} detected here:  {open_mv_dict[name]}"
            if self.verbose:
                self.logger.info(msg)
            else:
                self.logger.debug(msg)
        return common_name, exe_name

    def initialize_multivu_win32com(self):
        '''
        This creates an instance of the MultiVu ID which is
        used for enabling win32com to work with threading.

        This method updates self.multi_vu and self.mv_id

        Raises
        ------
        MultiVuExeException
            No detected MultiVu running, and initialization failed.

        '''
        if not self.scaffolding_mode:
            max_tries = 3
            for attempt in range(max_tries):
                try:
                    # This will try to connect Python with MultiVu
                    if self.run_with_threading:
                        pythoncom.CoInitialize()
                    # Get an instance
                    self.multi_vu = win32.Dispatch(self.class_id)
                    # if self.run_with_threading:
                        # Create id
                        # self.mv_id = pythoncom.CoMarshalInterThreadInterfaceInStream(
                        #                                     pythoncom.IID_IDispatch,
                        #                                     self.multi_vu
                        #                                     )
                except pythoncom.com_error as e:
                    pythoncom_error = vars(e)['strerror']
                    err_msg = ''
                    if pythoncom_error == 'Invalid class string':
                        err_msg += f'PythonCOM error:  {pythoncom_error}:'
                        err_msg += 'Error instantiating wind32com.client.Dispatch '
                        err_msg += f'using class_id = {self.class_id}'
                        err_msg += '\nTry reinstalling MultiVu.'
                    if attempt < max_tries - 1:
                        time.sleep(0.3)
                    else:
                        err_msg += f'Quitting script after {attempt + 1} '
                        err_msg += 'failed attempts to detect a running copy '
                        err_msg += 'of MultiVu.'
                    raise MultiPyVuError(err_msg) from e
                finally:
                    break

    def get_multivu_win32com_instance(self) -> None:
        '''
        This method is used to get an instance of the win32com.client
        and is necessary when using threading.

        This method updates self.multi_vu

        Raises
        ------
        MultiVuExeException
            This error is thrown if it is unable to connect to MultiVu.

        Returns
        -------
        None.

        '''
        if self.run_with_threading \
                and not self.scaffolding_mode \
                and not self._got_threaded_win32:
            max_tries = 3
            for attempt in range(max_tries):
                try:
                    # This will try to connect Python with MultiVu
                    pythoncom.CoInitialize()
                    # Get an instance from the ID
                    # self.multi_vu = win32.Dispatch(
                    #         pythoncom.CoGetInterfaceAndReleaseStream(
                    #                         self.mv_id,
                    #                         pythoncom.IID_IDispatch
                    #                         )
                    #     )
                    self.multi_vu = win32.Dispatch(self.class_id)
                    break
                except (pythoncom.com_error, TimeoutError) as e:
                    if attempt >= max_tries-1:
                        err_msg = f'Quitting script after {attempt + 1} '
                        err_msg += 'failed attempts to connect to MultiVu.'
                        raise MultiPyVuError(err_msg) from e
                time.sleep(0.3)
            self._got_threaded_win32 = True
        # end by getting a CommandMultiVu object
        self.mvu_commands = create_command_mv(self.name, self.multi_vu)

    def end_multivu_win32com_instance(self):
        '''
        Remove the marshalled connection to the MultiVu instance.
        '''
        if self.run_with_threading and not self.scaffolding_mode:
            pythoncom.CoUninitialize()
            self._got_threaded_win32 = False

    def parse_cmd(self, arg_string: str) -> str:
        '''
        This takes the arg_string parameter to create a query for
        CommandMultiVu.

        Parameters
        ----------
        arg_string: str
            The string has the form:
                arg_string = f'{action} {query}'
            For example, if asking for the temperature, the query is blank:
                arg_string = 'TEMP? '
            Or, if setting the temperature:
                arg_string = 'TEMP set_point,
                              rate_per_minute,
                              approach_mode.value'
            The easiest way to create the query is to use:
                ICommand.prepare_query(set_point,
                                       rate_per_min,
                                       approach_mode,
                                       )

        Returns
        -------
        str
            The return string is of the form:
            '{action}?,{result_string},{units},{code_in_words}'

        '''
        split_string = r'([A-Z]+)(\?)?[ ]?([ :\-?\d.,\w]*)?'
        # this returns a list of tuples - one for each time
        # the groups are found.  We only expect one command,
        # so only taking the first element
        [command_args] = re.findall(split_string, arg_string)
        try:
            cmd, question_mark, params = command_args
            query = (question_mark == '?')
        except IndexError:
            return f'No argument(s) given for command {command_args}.'
        else:
            if query:
                return self.mvu_commands.get_state(cmd, params)
            else:
                return self.mvu_commands.set_state(cmd, params)
