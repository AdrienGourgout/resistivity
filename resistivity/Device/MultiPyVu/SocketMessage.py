# -*- coding: utf-8 -*-
"""
SocketMessage.py is the base class for sending information across sockets.  It
has two inherited classes, SocketMessageServer.py and SocketMessageClient.py

Created on Mon Jun 7 23:47:19 2021

@author: D. Jackson
"""

import sys
import socket
import selectors
import json
import io
import logging
import struct
import time
from typing import Dict, Union

from .exceptions import (ClientCloseError,
                         ServerCloseError,
                         SocketError
                         )


class Message:
    def __init__(self, sock: socket.socket):
        '''
        This is the base class for holding data when sending or receiving
        sockets.  The class is instantiated by Server() and
        Client().

        The data is sent (.request['content']) and received (.response) as
        a dictionary of the form:
                action (ie, 'TEMP?', '', 'FIELD',...)
                query
                result

        The information goes between sockets using the following format:
            Header length in bytes
            JSON header (.jsonheader) dictionary with keys:
                byteorder
                content-type
                content-encoding
                content-length
            Content dictionary with key:
                action
                query
                result

        The entry method into the class is process_events(mask).

        The class also has methods for read(), write(), and close().

        Note that the server should set the following attributes:
        verbose : bool
            With this turned on, a notice will be printed showing everything
            sent and received across a socket.

        Parameters
        ----------
        sock : socket.socket
            The socket object.

        '''
        self.logger = logging      # this is defined in the child classes
        self.selector = selectors.DefaultSelector()
        self.sock = sock
        self.addr = sock.getsockname()
        self.request: dict = {}
        self._recv_buffer = b''
        self._send_buffer = b''
        self._request_queued = False     # only used by the client
        self._jsonheader_len: int = 0
        self.jsonheader = {}
        self.response_created = False    # only used by the server
        self._sent_success = False       # only used by the server
        self.response: dict = {}         # only used by the client
        self.mvu_flavor = None
        self.verbose = False
        self.scaffolding = False
        self.server_threading = False

    #########################################
    #
    # Private Methods
    #
    #########################################

    def _start_to_str(self) -> str:
        query_list = []
        if self.verbose:
            query_list.append('v')
        if self.scaffolding:
            query_list.append('s')
        if self.server_threading:
            query_list.append('t')
        return ';'.join(query_list)

    def _str_to_start_options(self, server_options: str) -> Dict:
        options_list = server_options.split(';')
        options_dict = {}
        options_dict['verbose'] = 'v' in options_list
        options_dict['scaffolding'] = 's' in options_list
        options_dict['threading'] = 't' in options_list
        return options_dict

    def _set_selector_events_mask(self, mode):
        """Set selector to listen for events: mode is 'r', 'w', or 'rw'."""
        if mode == "r":
            events = selectors.EVENT_READ
        elif mode == "w":
            events = selectors.EVENT_WRITE
        elif mode == "rw":
            events = selectors.EVENT_READ | selectors.EVENT_WRITE
        else:
            raise ValueError(f"Invalid events mask mode {repr(mode)}.")
        self.selector.modify(self.sock, events, data=self)

    def _read(self):
        try:
            # Should be ready to read
            data = self.sock.recv(4096)
        except BlockingIOError:
            # Resource temporarily unavailable (errno EWOULDBLOCK)
            pass
        else:
            if data:
                self._recv_buffer += data
            else:
                raise ClientCloseError('Close client')

    def _write(self):
        # until the sock is sent, this flag should be False
        self._sent_success = False

        if self._send_buffer:
            self._log_send()
            try:
                # Should be ready to write
                sent = self.sock.send(self._send_buffer)
            except BlockingIOError:
                # Resource temporarily unavailable (errno EWOULDBLOCK)
                self._sent_success = False
            except BrokenPipeError:
                # Resource temporarily unavailable
                self._sent_success = False
            # Note that OSError is a base class with the following subclasses:
            # ClientCloseError (ConnectionError)
            # ServerCloseError (ConnectionAbortedError)
            # ConnectionRefusedError
            except OSError:
                # No socket connection
                self._sent_success = False
                err_msg = 'No socket connection.  Please make sure '
                err_msg += 'MultiVuServer is running, that '
                err_msg += 'MultiVuClient is using the same IP address, '
                err_msg += 'that the IP address is correct, that the server '
                err_msg += 'can accept connections, etc.'
                raise SocketError(err_msg)
            else:
                self._sent_success = True
                self._send_buffer = self._send_buffer[sent:]

    def _log_received_result(self, message: str):
        msg = f';from {self.addr}; Received request {message}'
        self.log_message(msg)

    def _log_send(self):
        msg = f';to {self.addr}; Sending {repr(self._send_buffer)}'
        self.log_message(msg)

    def _check_exit(self):
        '''
        Checks to see if the client has requested to exit the program, meaning
        the client closes the connection and the server exits

        Raises
        ------
        ServerCloseError
            This error is used to let the program know the server
            is getting shut down (EXIT received)

        Returns
        -------
        None.

        '''
        exit_sent = self.response['action'] == 'EXIT'
        exit_received = self.response['query'] == 'EXIT'
        try:
            if exit_sent and exit_received:
                self.shutdown()
                raise ServerCloseError('Close server')
        except KeyError:
            # connection closed by the other end
            pass

    def _json_encode(self, obj, encoding):
        return json.dumps(obj, ensure_ascii=False).encode(encoding)

    def _json_decode(self, json_bytes, encoding):
        tiow = io.TextIOWrapper(
            io.BytesIO(json_bytes), encoding=encoding, newline=""
        )
        obj = json.load(tiow)
        tiow.close()
        return obj

    def _create_message(self,
                        *,
                        content_bytes,
                        content_type,
                        content_encoding):
        header = {
            'byteorder': sys.byteorder,
            'content-type': content_type,
            'content-encoding': content_encoding,
            'content-length': len(content_bytes),
        }
        header_bytes = self._json_encode(header, 'utf-8')
        message_hdr = struct.pack('>H', len(header_bytes))
        message = message_hdr + header_bytes + content_bytes
        return message

    #########################################
    #
    # Public Methods
    #
    #########################################

    def log_message(self, msg: str):
        if self.verbose:
            self.logger.info(msg)
        else:
            self.logger.debug(msg)

    def get_events(self, timeout: Union[float, None]) -> list:
        '''
        This is used to get the selectors events

        Parameters:
        -----------
        If timeout > 0, this specifies the maximum wait time, in
        seconds. If timeout <= 0, the call won't block, and will
        report the currently ready file objects. If timeout is
        None, the call will block until a monitored file object
        becomes ready.

        Returns:
        --------
        A list of (key, events) tuples, one for each ready file object.
        Key is the SelectorKey instance corresponding to a ready file
        object. Events is a bitmask of events ready on this file object.
        '''
        return self.selector.select(timeout)

    def connection_good(self) -> bool:
        '''
        Calls selectors.get_key(socket) to see if the connection is good.
        '''
        sel_key = None
        try:
            # Check for a socket being monitored to continue.
            sel_key = self.selector.get_key(self.sock)
        except ValueError:
            # can get this if self.sock is None
            pass
        except KeyError:
            # no selector is registered
            pass
        return bool(sel_key)

    def is_read(self, mask: int) -> bool:
        '''
        Uses the mask value to see if it is for a reading event
        '''
        return bool(mask & selectors.EVENT_READ)

    def is_write(self, mask: int) -> bool:
        '''
        Uses the mask value to see if it is for a writing event
        '''
        return bool(mask & selectors.EVENT_WRITE)

    def register_read_socket(self, new_selector=False):
        '''
        Register a file object for selection, monitoring it for I/O events.
        This starts with the connection being a read event.

        Parameters:
        -----------
        new_selector, bool (optional)
            When the server is first connecting to a selector, this
            should be true.  Remainder of times this is false.
        '''
        d = None if new_selector else self
        self.selector.register(self.sock, selectors.EVENT_READ, data=d)

    def unregister(self):
        '''
        Unregister a file object from selection, removing it from
        monitoring. A file object shall be unregistered prior to
        being closed.
        '''
        if not self.connection_good():
            return self.selector.unregister(self.sock)

    def process_events(self, mask):
        '''
        This is the entry-point for the Message base class.

        Parameters:
        -----------
        mask : int
            The events mask returned via key, mask = sel.select().

        Returns:
        --------
        None.

        Raises:
        -------
        ServerCloseError:
            Server closed
        ClientCloseError:
            Broken connection after three retries
        '''
        if mask & selectors.EVENT_READ:
            self.read()
        if mask & selectors.EVENT_WRITE:
            max_tries = 3
            for attempt in range(max_tries):
                try:
                    self.write()
                except ServerCloseError as e:
                    # Server closed, but don't want to show the message
                    # from the ClientCloseError.  This is needed since
                    # ServerCloseError (ConnectionAbortedError) is a subclass
                    # of ClientCloseError (ConnectionError)
                    raise ServerCloseError(e.args[0]) from e
                except ClientCloseError as e:
                    time.sleep(1)
                    if attempt == max_tries - 1:
                        err_msg = 'Socket connection failed after '
                        err_msg += f'{attempt +1} attempts.'
                        self.log_message(err_msg)
                        raise ClientCloseError(e.args[0]) from e
                else:
                    break

    def read(self):
        # this method needs to be overridden
        raise NotImplementedError()

    def write(self):
        # this method needs to be overridden
        raise NotImplementedError()

    def close(self):
        '''
        Unregister the Selector
        '''
        if self.connection_good():
            msg = f'Closing connection to {self.addr}'
            self.logger.info(msg)
            self.unregister()

    def shutdown(self):
        '''
        Unregister the Selector (via close()) and close the socket
        '''
        self.close()
        if self.sock is not None:
            try:
                self.sock.close()
            except OSError as e:
                msg = 'error: socket.close() exception for '
                msg += f'{self.addr}: {repr(e)}'
                self.log_message(msg)
            finally:
                # Delete reference to socket object for garbage collection
                self.sock = None

    def process_protoheader(self):
        hdrlen = 2
        if len(self._recv_buffer) >= hdrlen:
            # format = >H, which means:
            #   > = big-endian
            #   H = unsigned short, length = 2 bytes
            # This returns a tuple, but only the first item has a value,
            # which is why the line ends with [0]
            self._jsonheader_len = struct.unpack(
                '>H',
                self._recv_buffer[:hdrlen])[0]
            if len(self._recv_buffer) > self._jsonheader_len:
                # Now that we know how big the header is, we can trim
                # the buffer and remove the header length info
                self._recv_buffer = self._recv_buffer[hdrlen:]

    def process_jsonheader(self):
        hdrlen = self._jsonheader_len

        # The buffer holds the header and the data.  This makes sure
        # that the buffer is at least as long as we expect.  It will
        # be longer if there is data.
        if len(self._recv_buffer) >= hdrlen:
            # parse the buffer to save the header
            self.jsonheader = self._json_decode(
                self._recv_buffer[:hdrlen],
                'utf-8')

            # This ensures that the header has all of the required fields
            for reqhdr in (
                    'byteorder',
                    'content-length',
                    'content-type',
                    'content-encoding',
                    ):
                if reqhdr not in self.jsonheader:
                    raise ValueError(f'Missing required header "{reqhdr}".')

            # Then cut the buffer down to remove the header so that
            # now the buffer only has the data.
            self._recv_buffer = self._recv_buffer[hdrlen:]

    def create_request(self, action: str, query: str):
        self.request = {
            'type': 'text/json',
            'encoding': 'utf-8',
            'content': dict(action=action.upper(), query=query, result=''),
            }
        events = selectors.EVENT_READ | selectors.EVENT_WRITE
        try:
            self.selector.modify(self.sock, events, data=self)
        except KeyError:
            self.selector.register(self.sock, events, data=self)
        except ValueError as e:
            self.log_message('Warning:  No server/client connection')
            raise ClientCloseError(e.args[0]) from e
        return self.request
