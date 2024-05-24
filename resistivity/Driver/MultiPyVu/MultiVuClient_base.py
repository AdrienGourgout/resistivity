#!/usr/bin/env python3
"""
Created on Mon Jun 7 23:47:19 2021

MultiVuClient_base.py is a module for use on a network that has access to a
computer running MultiVuServer.py.  By running this client, a python script
can be used to control a Quantum Design cryostat.

This is the base class.  It has the basic communication commands.  The
MultiVuClient class has specific commands to be used with this class.

@author: D. Jackson
"""

import sys
import os
import socket
import traceback
import time
from typing import Dict, Union


from .SocketMessageClient import ClientMessage
from .create_logger import log
from .project_vars import (CLIENT_NAME,
                           HOST,
                           PORT,
                           )
from .exceptions import (MultiPyVuError,
                         ClientCloseError,
                         ServerCloseError,
                         SocketError
                         )

if sys.platform == 'win32':
    import msvcrt    # Used to help detect the esc-key


MAX_TRIES = 3


class ClientBase():
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

    def __init__(self,
                 host: str = HOST,
                 port: int = PORT,
                 socket_timeout: Union[float, None] = 2.5,
                 ):
        self._addr = (host, port)
        self._socket_timeout = socket_timeout
        self._message = None     # ClientMessage object
        self._sock = None
        self._request = {}
        self._response = {}
        self.log_event = log(CLIENT_NAME)
        self._instr = None
        self.instrument_name = ''

    def __enter__(self):
        # Configure logging
        self.logger = self.log_event.create(CLIENT_NAME,
                                            display_logger_name=True,
                                            )
        self.logger.info(f'Starting connection to {self._addr}')
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._sock.setblocking(False)
        self._sock.connect_ex(self._addr)

        self._message = ClientMessage(self._sock)
        # send a request to the sever to confirm a connection
        action = 'START'
        response = self.query_server(action)
        self.logger.info(response['result'])
        self._instr = self._message.instr
        self.instrument_name = self._message.instr.name
        return self

    def __exit__(self, exc_type, exc_value, exc_traceback) -> bool:
        exit_without_error = False
        # Error handling
        if isinstance(exc_value, SystemExit):
            exit_without_error = True
        if isinstance(exc_value, KeyboardInterrupt):
            self.logger.info('')
            self.logger.info('Caught keyboard interrupt, exiting')
            exit_without_error = True
        elif isinstance(exc_value, ServerCloseError):
            msg = 'Shutting down the server.'
            self.logger.info(msg)
            exit_without_error = True
        elif isinstance(exc_value, ClientCloseError):
            # Note that ServerCloseError (ConnectionAbortedError) and
            # ConnectionRefusedError are subclasses of
            # ClientCloseError (ConnectionError)
            exit_without_error = True
        elif isinstance(exc_value, TimeoutError):
            exit_without_error = True
        elif isinstance(exc_value, MultiPyVuError):
            exit_without_error = False
        elif isinstance(exc_value, SocketError):
            exit_without_error = True
        elif isinstance(exc_value, BaseException):
            msg = 'MultiVuClient: error: exception for '
            if self._message is not None:
                msg += f'{self._message.addr}:'
            msg += f'\n{traceback.format_exc()}'
            self.logger.info(msg)
            exit_without_error = False
        else:
            self.query_server('CLOSE')
            exit_without_error = True

        # Close things up for all cases
        if not exit_without_error:
            self.logger.info(traceback.format_exc())
            # using os._exit(0) instead of sys.exit(0) because we need
            # all threads to exit, and we don't know if there will be
            # threads running.  os._exit(0) is more forceful, but in
            # this case everything is wrapped up when calling
            # this method.  Note that this can not clean up anything
            # from other threads, though.
            # TODO - create exit codes to help show why the script quit
            self.log_event.remove()
            self.log_event.shutdown()
            os._exit(0)
        if self._message is not None:
            self._message.shutdown()
            self._message = None
        if self._sock is not None:
            self._sock.close()
        self.log_event.remove()
        self.log_event.shutdown()
        self._instr = None
        self.instrument_name = ''
        return exit_without_error

    ###########################
    #  Client Methods
    ###########################

    def open(self):
        '''
        This is the entry point into the MultiVuClient.  It connects to
        a running MultiVuServer

        Raises
        ------
        ConnectionRefusedError
            This is raised if there is a problem connecting to the server. The
            most common issue is that the server is not running.

        Returns
        -------
        None.

        '''
        self.__enter__()

    def close_client(self):
        '''
        This command closes the client, but keeps the server running
        '''
        # __close_and_exit() calls __exit__(), which will call
        # .query_server('CLOSE') after it confirms there is no
        # exception
        self.__close_and_exit()

    def close_server(self):
        '''
        This command closes the server
        '''
        self.query_server('EXIT')

    def __check_windows_esc(self) -> None:
        '''
        Windows looks for the ESC key to quit.

        Raises:
        -------
        Throws a KeyboardInterrupt if the esc key is hit.
        '''
        if sys.platform == 'win32':
            if (msvcrt.kbhit()
                    and msvcrt.getch().decode() == chr(27)):
                raise KeyboardInterrupt

    def __send_and_receive(self,
                           action: str,
                           query: str = '') -> Dict[str, str]:
        '''
        This takes an action and a query, and sends it to
        ._monitor_and_get_response() to let that method figure out what
        to do with the information.

        Parameters
        ----------
        action : str
            The general command going to MultiVu:  TEMP(?), FIELD(?), and
            CHAMBER(?).  If one wants to know the value of the action, then
            it ends with a question mark.  If one wants to set the action in
            order for it to do something, then it does not end with a question
            mark.
        query : str, optional
            The query gives the specifics of the command going to MultiVu.  For
            queries. The default is '', which is what is used when the action
            parameter ends with a question mark.

        Returns
        -------
        The response dictionary from the ClientMessage class.

        Raises:
        -------
        ClientCloseError
        TimeoutError
        KeyboardInterrupt
        MultiPyVuError
        '''
        if self._message is None:
            msg = 'Error:  '
            msg += 'No connection to the server.  Is the client connected?'
            raise ClientCloseError(msg)
        timeout_attempts = 0
        while True:
            self._message.create_request(action, query)
            try:
                response = self.__monitor_and_get_response()
                break
            except TimeoutError:
                if timeout_attempts >= MAX_TRIES:
                    # An empty list means the selector timed out
                    msg = 'Socket timed out after '
                    msg += f'{timeout_attempts} attempts.'
                    raise TimeoutError(msg)
                timeout_attempts += 1
        if response == {}:
            msg = 'No return value, which could mean that MultiVu '
            msg += 'is not running or that the connection has '
            msg += 'been closed.'
            raise ClientCloseError(msg)
        # reset the request and response to blank dicts
        self._request = {}
        self._response = {}
        return response

    def query_server(self, action: str,
                     query: str = '') -> Dict[str, str]:
        '''
        Queries the server using the action and query parameters.

        Parameters
        ----------
        action : str
            The general command going to MultiVu:  TEMP(?), FIELD(?), and
            CHAMBER(?), etc..  If one wants to know the value of the action,
            then it ends with a question mark.  If one wants to set the action
            in order for it to do something, then it does not end with a
            question mark.
        query : str, optional
            The query gives the specifics of the command going to MultiVu.  For
            queries. The default is '', which is what is used when the action
            parameter ends with a question mark.

        Returns:
        --------
        The response dictionary from the ClientMessage class.
        '''
        resp = {}
        for attempt in range(MAX_TRIES):
            try:
                resp: dict = self.__send_and_receive(action, query)
            except MultiPyVuError as e:
                self.logger.info(e)
                self.__close_and_exit()
            except ServerCloseError:
                self.__close_and_exit()
            except ClientCloseError:
                self.close_client()
            except SocketError:
                # No socket connection
                self.logger.info('Failed socket connection')
                self.__close_and_exit()
                sys.exit(0)
            except TimeoutError as e:
                # this includes ClientCloseError, ServerCloseError,
                # and TimeoutError
                msg = f'Attempt {attempt + 1} of {MAX_TRIES} failed:  {e}'
                self.logger.info(msg)
                if attempt >= MAX_TRIES - 1:
                    err_msg = 'Failed to make a connection to the '
                    err_msg += 'server.  Check if the MultiVuServer '
                    err_msg += 'is running.'
                    self.logger.info(err_msg)
                    self.__close_and_exit()
                    sys.exit(0)
                time.sleep(1)
            else:
                break
        return resp

    def __monitor_and_get_response(self) -> Dict[str, str]:
        '''
        This monitors the traffic going on.  It asks the SocketMessageClient
        class for help in understanding the data.  This is also used to handle
        the possible errors that SocketMessageClient could generate.

        Raises
        ------
        ConnectionRefusedError
            Could be raised if the server is not running.
        ClientCloseError
            Could be raised if there are connection issues with the server.
        KeyboardInterrupt
            This is used by the user to close the connection.
        MultiVuExeException
            Raised if there are issues with the request for MultiVu commands.

        Returns
        -------
        Message.response: Dict
            The information retrieved from the socket and interpreted by
            SocketMessageClient class.

        '''
        # increase the timeout length using command line arguments to
        # make it easier to debug the code and give extra time to make
        # the connection.  If the timeout is set to None it will block
        # until a connection is made.

        # TODO - add a counter here and if a connection fails after
        # so many attempts, bring up a question for the user if they
        # want to continue (which would reset the counter) or quit.
        # timeout_attempts = 0
        while True:
            events = self._message.get_events(self._socket_timeout)
            if events:
                # mask = 1 is read
                # mask = 2 is write
                for key, mask in events:
                    message: ClientMessage = key.data
                    try:
                        message.process_events(mask)
                    except ServerCloseError as e:
                        # Client closed the server
                        if self._request['action'] == 'EXIT':
                            self._message.close()
                        raise ServerCloseError(e.args[0]) from e
                    except ClientCloseError as e:
                        # Client closed the client
                        raise ClientCloseError(e.args[0]) from e
                    except SocketError as e:
                        raise SocketError(e.args[0]) from e
                    except Exception:
                        self.__close_and_exit()
                    else:
                        self.__check_windows_esc()
                        if message.is_write(mask):
                            self._request = message.request['content']
                        elif message.is_read(mask):
                            self._response = message.response
                            # check response answers a request
                            if self._request['action'] != self._response['action']:
                                msg = 'Received a response to the '
                                msg += 'wrong request:\n'
                                msg += f' request = {self._request}\n'
                                msg += f'response = {self._response}'
                                raise MultiPyVuError(msg)
                            # return the response
                            rslt: str = self._response['result']
                            if rslt.startswith('MultiPyVuError: '):
                                raise MultiPyVuError(rslt)
                            else:
                                return self._response
                        else:
                            raise IndexError
            else:
                # timeout_attempts += 1
                # if timeout_attempts > MAX_TRIES:
                #     # An empty list means the selector timed out
                #     msg = 'Socket timed out after '
                #     msg += f'{timeout} seconds.'
                #     raise TimeoutError(msg)
                # self._message.create_request('START', '')
                raise TimeoutError
            # Check for a socket being monitored to continue.
            if self._message is None \
                    or not self._message.connection_good():
                msg = 'Connection disrupted in MultiVuClient.py '
                msg += 'Socket connection broken '
                msg += 'in _monitor_and_get_response()'
                self.logger.info(msg)
                raise MultiPyVuError(msg)

    def __close_and_exit(self) -> bool:
        err_info = sys.exc_info()
        return self.__exit__(err_info[0], err_info[1], err_info[2])
