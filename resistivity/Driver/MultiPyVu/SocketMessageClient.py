# -*- coding: utf-8 -*-
"""
SocketMessageClient.py inherits SocketMessage and is used by the client
to communicate with socket server via SocketMessageServer

Created on Mon Jun 7 23:47:19 2021

@author: D. Jackson
"""

import re
import logging
import time

from .SocketMessage import Message
from .instrument import Instrument
from .project_vars import CLIENT_NAME
from .exceptions import ClientCloseError


class ClientMessage(Message):
    def __init__(self, sock):
        super().__init__(sock)
        time.sleep(0.3)
        self.logger = logging.getLogger(CLIENT_NAME)

    #########################################
    #
    # Private Methods
    #
    #########################################

    def _process_response_json_content(self):
        content = self.response
        if content['action'] == 'START':
            options_dict = self._str_to_start_options(content['query'])
            self.verbose = options_dict['verbose']
            self.scaffolding = options_dict['scaffolding']
            self.server_threading = options_dict['threading']
            resp = content.get('result')
            search = r'Connected to ([\w]*) MultiVuServer'
            self.mvu_flavor = re.findall(search, resp)[0]
            # the Instrument class is used to hold info and
            # can be instantiated with scaffolding mode so that
            # it does not try to connect with a running MultiVu
            self.instr = Instrument(self.mvu_flavor,
                                    True,   # instantiate in scaffolding mode
                                    self.server_threading,
                                    self.verbose)

    def _reset_read_state(self):
        self._jsonheader_len = 0
        self.jsonheader = {}
        self.request = {}

    def _check_close(self):
        '''
        Checks to see if the client has requested to close the connection
        to the server.

        Raises
        ------
        ClientCloseError
            This error is used to let the program know the client
            is closing, but the server will remain open.

        Returns
        -------
        None.

        '''
        close_sent = self.response['action'] == 'CLOSE'
        closing_received = self.response['query'] == 'CLOSE'
        try:
            if close_sent and closing_received:
                self.shutdown()
                # Client has requested to close the connection
                raise ClientCloseError('Close client')
        except KeyError:
            # connection closed by the other end
            pass

    #########################################
    #
    # Public Methods
    #
    #########################################

    def read(self):
        # read sockets
        try:
            self._read()
        except ClientCloseError as e:
            # This is thrown if the server or the client shut down. If
            # the server shuts down, the client needs to also shut down
            if self.request['content']['action'] == 'START':
                err_msg = 'No connection to the sever upon start.  Is the '
                err_msg += 'server running?'
                self.logger.info(err_msg)
            self.shutdown()
            raise ClientCloseError(e.args[0]) from e

        if self._jsonheader_len == 0:
            self.process_protoheader()

        if self._jsonheader_len > 0:
            if self.jsonheader == {}:
                self.process_jsonheader()

        if self.jsonheader:
            self.process_response()

        self._set_selector_events_mask('w')
        self._check_close()
        self._check_exit()
        self._reset_read_state()

    def write(self):
        if not self._request_queued:
            self.queue_request()

        self._write()

        # This tells selector.select() to stop monitoring for write events
        # and reset the _request_queued flag
        if self._request_queued:
            if not self._send_buffer:
                # Set selector to listen for read events; we're done writing.
                # Keep this socket a read socket until we are ready
                # to write anything.
                self._set_selector_events_mask('r')
                self._request_queued = False

    def queue_request(self):
        content = self.request['content']
        content_type = self.request['type']
        content_encoding = self.request['encoding']
        content_binary = self._json_encode(content, content_encoding)

        req = {
            'content_bytes': content_binary,
            'content_type': content_type,
            'content_encoding': content_encoding,
            }
        message = self._create_message(**req)
        self._send_buffer += message
        self._request_queued = True

    def process_response(self):
        content_len = self.jsonheader["content-length"]
        if len(self._recv_buffer) < content_len:
            return

        data = self._recv_buffer[:content_len]
        self._recv_buffer = self._recv_buffer[content_len:]
        encoding = self.jsonheader["content-encoding"]
        self.response = self._json_decode(data, encoding)
        self._log_received_result(repr(self.response))
        self._process_response_json_content()
