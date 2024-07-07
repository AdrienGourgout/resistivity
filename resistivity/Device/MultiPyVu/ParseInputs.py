# -*- coding: utf-8 -*-
"""
_ParseInputs.py contains the Input class, which is a tool to parse the
command-line inputs

"""

import sys
import re
import ntpath
import logging
from typing import Union, Dict, List

from .instrument import InstrumentList
from .project_vars import (SERVER_NAME,
                           HOST,
                           PORT,
                           )


class Inputs():
    def __init__(self):
        self.logger = logging.getLogger(SERVER_NAME)

    def path_leaf(self, path):
        '''
        Used to split a path up to get the path to a filename.

        Parameters
        ----------
        path : str
            The path and file location.

        Returns
        -------
        str
            Path to file.

        '''
        head, tail = ntpath.split(path)
        return tail or ntpath.basename(head)

    def parse_input(self, input_args_list: List[str]) -> Dict[str, Union[str, bool, None]]:
        '''
        Parses the input_args_list text

        Parameters
        ----------
        input_args_list : list
             Arguments flags are:
            --h(elp) to display the help text
            --s for scaffolding in order to simulate the script
            --ip=<host address> to specify the host IP
                address (default = 'localhost')
            --p(ort)=.port number. to specify the port (default is 5000)
            --v(erbose) to turn on the verbose text when the server
                sends/receives info

            An argument without a flag is the instrument.

        Returns
        -------
        dict
            Dictionary with keys: 'instrument_str',
            'scaffolding_mode', 'host', 'port', 'verbose'.

        Exceptions
        ----------
        A UserWarning exception is thrown if displaying the help text. This
        can also be thrown if the instrument name does not match a valid
        MultiVu flavor (or if the flag is unknown).
        '''
        flag_dict = dict()
        # convert the input_args_list into a string.
        input_args = ' '.join(input_args_list)

        # reg-ex for finding flags in the input
        help_args = re.compile(r'-[-]?(h)(elp)?', re.IGNORECASE)
        sim_args = re.compile(r'-[-]?(s)', re.IGNORECASE)
        verbose_args = re.compile(r'-[-]?(v)', re.IGNORECASE)
        ip_rg = r'-[-]?(ip)[=]?(\d{1,3}.\d{1,3}.\d{1,3}.\d{1,3}|localhost)'
        ip_args = re.compile(ip_rg, re.IGNORECASE)
        p_rg = r'-[-]?(p|(?:port)?)[=](\d{4,5}){1}[ |\n]?'
        port_args = re.compile(p_rg, re.IGNORECASE)
        i_rg = r'\w*(?<!-|[a-zA-Z])([a-zA-Z]+3?)'
        inst_args = re.compile(i_rg, re.IGNORECASE)

        flag_dict['instrument_str'] = ''
        flag_dict['scaffolding_mode'] = False
        flag_dict['host'] = HOST
        flag_dict['port'] = PORT
        flag_dict['verbose'] = False

        show_help = True
        additional_help_info = f'{input_args} is not a valid flag.'

        if input_args == '':
            return flag_dict

        # check for help string
        if help_args.search(input_args):
            additional_help_info = ''
            pass
        # check if the filename input flag is used, and get the filename
        # if thread_args.search(input_args):
        #     flag_dict['run_with_threading'] = True
        #     show_help = False
        if sim_args.search(input_args):
            flag_dict['scaffolding_mode'] = True
            show_help = False
        if verbose_args.search(input_args):
            flag_dict['verbose'] = True
            show_help = False
        if ip_args.search(input_args):
            _, flag_dict['host'] = ip_args.findall(input_args)[0]
            show_help = False
        if port_args.search(input_args):
            _, flag_dict['port'] = port_args.findall(input_args)[0]
            # cast the string as an integer
            try:
                flag_dict['port'] = int(flag_dict['port'])
                show_help = False
            except ValueError:
                additional_help_info = 'The specified port must be '
                additional_help_info += 'an integer (received '
                additional_help_info += f'"{flag_dict["port"]})"'
        if inst_args.search(input_args):
            instrument_list = inst_args.findall(input_args)
            if len(instrument_list) > 1:
                additional_help_info = 'Can only accept one instrument. '
                additional_help_info += f'Found {instrument_list}'
            else:
                instrument_str = instrument_list[0]
                # Check to see if the input is a valid instrument_str
                if (instrument_str.upper() not in InstrumentList._member_names_
                        or instrument_str == InstrumentList.na):
                    additional_help_info = 'The specified instrument,'
                    additional_help_info += f'"{instrument_str}", is not '
                    additional_help_info += 'a valid MultiVu flavor.  See '
                    additional_help_info += 'the above help for information.'
                else:
                    msg = f'{instrument_str} MultiVu specified by user.'
                    self.logger.info(msg)
                    show_help = False
                    flag_dict['instrument_str'] = instrument_str

        if show_help:
            msg = self.help_text(additional_help_info)
            raise UserWarning(msg)

        return flag_dict

    def help_text(self, additional_help_info='') -> str:
        program_name = self.path_leaf(sys.argv[0])
        help_text = f"""
INPUT OPTIONS:
    To display this help text:
        $ python {program_name} -h
    To run the scaffolding (python is simulating MultiVu)
    and test the server (must also specify the MultiVu flavor):
        $ python {program_name} -s
    To specify the host IP address (default = 'localhost'):
        $ python {program_name} -ip=<host IP address>
    To specify the port (default = 5000):
        $ python {program_name} -p=<port number>
        Note that non-privileged ports are 1023 < 65535
    To run in verbose mode and have the server print to the
    command line all of the data it sends/receives:
        $ python {program_name} -v

MultiVu must be running before starting the server.  Usually
MultiVu.Server will figure out which MultiVu flavor to run
and the specific flavor does not need to be specified.  However,
if the flavor must be specified, then use one of the following
options:"""

        for i in InstrumentList.__members__.values():
            if i.name != InstrumentList.na.name:
                instr_name = i.name.capitalize()
                help_text += f'\n\t$ python {program_name} {instr_name}'

        help_text += """

Once the server is started, a python script can control the cryostat
by using MultiVu.Client.  Please reference example_client.py to
see how to control a cryostat using MultiVu.Client in your own
scripts.

If the client script is going to be running on the same computer
as MultiVu, then one can put the server and client in a single
program.  Please reference example_server_and_client.py for an
example.
"""

# TODO - The following help text is only valid if the telnet
# part of the code is working.

# One may also control the cryostat via telnet.  In that case, the
# command line interface options are:

# COMMAND LINE INTERFACE OPTIONS:
#     TEMP? - returns the temperature, unit of measurement,
#         and status.
#     TEMP target,rate,mode - sets the target
#         temperature (K), rate (K/min), and mode.
#         MODE:
#             0: Fast Settle
#             1: No Overshoot

#     FIELD? - returns the field (oe) and the state.
#     FIELD field, rate, approach mode, field mode - sets the field
#         set point (oe), the rate to reach field (Oe/s),
#         the Approach mode, and Field mode.
#         APPROACH MODE:
#             0: Linear
#             1: No Overshoot
#             2: Oscillate
#         FIELD MODE:
#             0: Persistent (PPMS and MPMS3 only)
#             1: Driven

#     CHAMBER? - returns the chamber state
#     CHAMBER mode - sets the chamber mode:
#         MODE:
#             0: Seal
#             1: Purge/Seal
#             2: Vent/Seal
#             3: Pump continuous
#             4: Vent continuous
#             5: High vacuum"""

        if additional_help_info != '':
            help_text += '\n\n------------------------------------------\n\n'
            help_text += additional_help_info
        return help_text
