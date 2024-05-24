"""
Controller.py is the controller part of the Model-View-Controller design
pattern for MultiPyVu.py

@author: djackson
"""


import os
import sys
import subprocess
import re
from typing import List
from types import MethodType

from .MultiVuServer import Server
from .instrument import InstrumentList
from .ParseInputs import Inputs
from .ViewFactory import ViewType, ViewFactory
from .IController import IController
from .ServerEventManager import IObserver


class ServerInfo(IObserver):
    def __init__(self, model_method_obj, view_func):
        '''
        When the model object changes, it will update the view variables

        Parameters:
        -----------
        model_method_obj: class method, parameter, or variable
            This is the model properties that we have subscribed to
        view_func: callable method
            This is the view method that is called to get updated.
        '''
        self._model_param = model_method_obj
        self._view_func = view_func

    def update(self):
        '''
        Updates the view with information from the model
        '''
        if isinstance(self._model_param, MethodType):
            self._view_func(self._model_param())
        else:
            self._view_func(self._model_param)


class Controller(IController):
    def __init__(self, flags: List):
        super().__init__(flags)
        # scaffolding flag
        user_input = Inputs()
        flag_info = user_input.parse_input(flags)
        self._scaffolding = bool(flag_info['scaffolding_mode'])
        # the Server gets instantiated in .start_server()
        self.model = None
        self.view = ViewFactory().create(ViewType.tk, self)
        self.view.create_display()

    def is_client_connected(self) -> bool:
        return True

    def start_gui(self):
        self.view.start_gui()

    def quit_gui(self):
        self.view.quit_gui()

    def absolute_path(self, filename: str) -> str:
        abs_path = os.path.abspath(
            os.path.join(os.path.dirname(
                __file__), './'))
        return os.path.join(abs_path, filename)

    def _get_mvu_flavor(self):
        '''
        Get the PPMS flavor and make it look nice
        '''
        if self.model is None:
            return ''
        flavor = self.model.instr.name
        if flavor == InstrumentList.DYNACOOL.name:
            return 'DynaCool Running'
        elif flavor == InstrumentList.PPMS.name:
            return 'PPMS Running'
        elif flavor == InstrumentList.VERSALAB.name:
            return 'VersaLab Running'
        elif flavor == InstrumentList.MPMS3.name:
            return 'MPMS3 Running'
        elif flavor == InstrumentList.OPTICOOL.name:
            return 'OptiCool Running'
        else:
            raise ValueError(f"'{flavor}' not supported")

    @property
    def ip_address(self) -> str:
        ip_output_str = ''
        search_str = r'([0-9]{1,3}.[0-9]{1,3}.[0-9]{1,3}.[0-9]{1,3})'
        if sys.platform == 'win32':
            ip_addr_script = 'scripts/whats_my_ip_address.cmd'
            ip_addr_script = self.absolute_path(ip_addr_script)
            proc = subprocess.run([ip_addr_script],
                                  capture_output=True,
                                  text=True)
            if proc.returncode != 0:
                print(proc.stderr)
                raise Exception(proc.stderr)
            ip_result = re.findall(search_str, proc.stdout)
            if len(ip_result) == 1:
                self._ip_address = ip_result[0]
        else:
            # using this suggestion:
            # https://apple.stackexchange.com/questions/20547/how-do-i-find-my-ip-address-from-the-command-line
            ifconfig_proc = subprocess.Popen(["ifconfig"],
                                             stdout=subprocess.PIPE,
                                             text=True)
            grep_proc = subprocess.Popen(["grep", "inet"],
                                         stdin=ifconfig_proc.stdout,
                                         stdout=subprocess.PIPE,
                                         text=True)
            ip_output_str, err = grep_proc.communicate()
            if err is not None:
                print(err)
                raise Exception(grep_proc.stderr)
            ip_result = re.findall(search_str, ip_output_str)
            if '127.0.0.1' in ip_result:
                ip_result.remove('127.0.0.1')
            if len(ip_result) >= 1:
                self._ip_address = ip_result[0]
        return self._ip_address

    @ip_address.setter
    def ip_address(self, ip: str):
        self._ip_address = ip

    def get_scaffolding_mode(self) -> bool:
        return self._scaffolding

    def set_scaffolding_mode(self, scaffolding: bool) -> None:
        self._scaffolding = scaffolding

    def start_server(self, ip_address: str):
        '''
        Start the server using the specified IP address
        '''
        user_flags = []
        if ip_address != 'localhost':
            user_flags = [f'-ip={ip_address}']
        user_flags.extend(self._flags)
        self.model = Server(user_flags)
        self._is_client_connected = ServerInfo(self.model.is_client_connected,
                                               self.view.set_connection_status)
        self.model.subscribe(self._is_client_connected)
        self.view.mvu_flavor = self._get_mvu_flavor()
        return self.model.open()

    def stop_server(self):
        '''
        Disconnect the server.
        '''
        if self.model is not None:
            self.model.close()
            self.model.unsubscribe(self._is_client_connected)
            self.model = None
