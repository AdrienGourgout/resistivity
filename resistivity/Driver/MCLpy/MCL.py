import json
import queue
import socket
import struct
import sys
import threading
import time

from resistivity.Driver.MCLpy.Config import Config
from resistivity.Driver.MCLpy.Data import Data

__all__ = ['MCL']

class MCL:
    """
    MCL class to control the MCL1-540 lockin amplifer measurement system.

    Properties
    ----------
    lidata_data_readings_l1 : namedtuple
    lidata_data_readings_l2 : namedtuple
        the lockin data of lockin sets 1/2
    ...

    Methods
    -------
    findSystems()
        Detect MCL systems on the local network
    connect(mcl_ip)
        Connect to the MCL system
    disconnect(mcl_ip)
        Disconnect from the MCL system

    """

    def __init__(self):
        MIN_PYTHON = (3, 7)
        if sys.version_info < MIN_PYTHON:
            sys.exit("The MCL library requires Python %s.%s or later.\n" % MIN_PYTHON)
        self._stop = False  # true to stop communication in different threads
        # ping counter for write connection
        self._ping_i_write = 0
        # write command queue
        self._write_queue = queue.Queue()

        self.config = Config(self._write_queue)
        self.data = Data()

        self._destinations = {}
        all_subclasses = self.config.children + self.data.children

        for subclass in all_subclasses:
            self._destinations[(subclass.data_type, subclass.data_kind)] = subclass

    def _get_destination_class(self, data_type, data_kind):
        try:
            return self._destinations[data_type, data_kind]
        except:
            return False

    def find_systems(self):
        """Detect systems on the local network.

        Parameters
        ----------
        none

        Returns
        -------
        system
            a dictionary of json strings, ip address as key
        """
        ports = [1901, 1902]
        threads = []
        replies = queue.Queue()
        # create reading threads
        for port in ports:
            port += 2  # read reply from higher port #
            threads.append(threading.Thread(target=self._find_systems_reply, args=[port, replies]))
        # start threads
        for t in threads:
            t.start()
        # send multicast query
        for port in ports:
            cs = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
            cs.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            cs.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, 8)
            cs.bind(('', port))
            cs.sendto(b'MCL?', ('239.255.255.250', port))
            cs.close()
        # Wait for all threads to complete
        for t in threads:
            t.join()
        # Read the queue
        systems = {}
        while not replies.empty():
            ip, system = replies.get()
            systems[ip] = system
        return systems

    def _find_systems_reply(self, port, replies):
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind(('', port))
        mreq = struct.pack("=4sl", socket.inet_aton("239.255.255.250"), socket.INADDR_ANY)
        sock.setsockopt(socket.IPPROTO_IP, socket.IP_ADD_MEMBERSHIP, mreq)
        sock.settimeout(1)
        while True:
            try:
                data, (ip, port) = sock.recvfrom(1024)  # buffer size is 1024 bytes
            except:  # no reply within one second
                # print('UDP read error')
                # print(sys.exc_info()[0])
                break
            if data[0:10] == b'MCL-REPLY:':
                replies.put((ip, json.loads(data[10:])))

    def connect(self, mcl_ip):
        """Connect to the MCL system

        Parameters
        ----------
        mcl_ip : str
            The IP address of the system

        Returns
        -------
        none
        """

        # Create a TCP/IP socket
        # read data from system, write data to system
        self._sock_read = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._sock_write = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # event to notify when all variables from the lockin are initilized
        init_event = threading.Event()

        # connect socket to the port
        self._server_address_read = (mcl_ip, 46000)
        self._server_address_write = (mcl_ip, 46001)
        print('connecting to %s port %s' % self._server_address_read, file=sys.stderr)
        try:
            self._sock_read.connect(self._server_address_read)
        except:
            print("Error: cannot open socket.")
            time.sleep(1)
            quit()
        print('connecting to %s port %s' % self._server_address_write, file=sys.stderr)
        self._sock_write.connect(self._server_address_write)
        # start communication threads
        # reading: send ping to keep read connection
        threading.Thread(target=self._ping_read_timer, daemon=True).start()
        # reading: read data
        threading.Thread(target=self._data_read, daemon=True, args=[init_event]).start()
        # sending: read ping for write connection
        threading.Thread(target=self._ping_write_receive, daemon=True).start()
        # sendimg: send data
        threading.Thread(target=self._data_write, daemon=True).start()
        # trigger update of user variables
        time.sleep(1)
        self.config.general.val = self.config.general.val._replace(updateuser=True)  # This calls send() internally
        # self._write_queue.put(self.config.general.send())

        # wait until all data is received/initialized
        print("Waiting to synchronize config variables...")
        init_event.wait()
        print("Connected, config variables synced")
        init_event.clear()

    def _ping_read_timer(self):
        """Send a ping to the system once a second to keep the connection alive."""
        ping_i = 0
        while not self._stop:
            # running timer
            time.sleep(1)
            # sending ping %i" % ping_i
            self._sock_read.sendall(ping_i.to_bytes(4, byteorder='big', signed=False))
            ping_i += 1

    def _ping_write_receive(self):
        chunks = bytearray()
        # bytes_recd = 0
        while not self._stop:
            # waiting for ping
            chunk = self._sock_write.recv(4)
            if chunk == b'':
                raise RuntimeError("socket connection broken")
            chunks += bytearray(chunk)
            while len(chunks) >= 4:
                # received ping %i' % i
                # i = int.from_bytes(chunks[0:4], byteorder='big', signed=False)
                del chunks[0:4]

    def _data_write(self):
        while not self._stop:
            to_send = self._write_queue.get()
            if to_send != b'':  # skip zero bytes, used for disconnecting
                self._sock_write.sendall(to_send)
            self._write_queue.task_done()

    def _data_read(self, init_event):
        chunks = bytearray()
        wait_for_header = True
        min_len = 7
        datalen = 0
        datakind = 0
        datatype = 0  # Controls = 0, Indicators = 1, Config = 2, Lock-in Data = 3, Waveforms = 4

        # check if datatypes are initiated, then notify init_event
        num_datatypes = [0, 0, 137, 2, 2]
        initiated_datatypes = [[], [], [False] * num_datatypes[2], [False] * num_datatypes[3],
                               [False] * num_datatypes[4]]
        is_initiated = False

        while not self._stop:
            # wating for data
            chunk = self._sock_read.recv(524288)
            # received data length = %i" %len(chunk)
            if chunk == b'':
                raise RuntimeError("socket connection broken")
            chunks += bytearray(chunk)
            # wait until full dataset is received
            while len(chunks) >= min_len:
                if (wait_for_header):
                    datatype = int.from_bytes(chunks[0:1], byteorder='big', signed=False)
                    datakind = int.from_bytes(chunks[1:3], byteorder='big', signed=False)
                    datalen = int.from_bytes(chunks[3:7], byteorder='big', signed=False)
                    del chunks[0:7]
                    min_len = datalen
                    wait_for_header = False
                if not wait_for_header and len(chunks) >= min_len:
                    if not is_initiated:
                        initiated_datatypes[datatype][datakind] = True
                        # if initiated_datatypes[2].count(True) + initiated_datatypes[3].count(True) +
                        # initiated_datatypes[4].count(True) >= sum(num_datatypes):
                        if initiated_datatypes[2].count(True) >= num_datatypes[2]:
                            is_initiated = True
                            init_event.set()

                    data = chunks[0:datalen]
                    if datatype == 0:
                        print(data)
                        time.sleep(1)

#                    if datatype == 2 and (datakind == 6 or datakind == 7):
#                        print("Receiving", datakind, data, list(data))


                    destination = self._get_destination_class(datatype, datakind)
                    if destination:
                        destination.receive(data)

                    wait_for_header = True
                    min_len = 7
                    del chunks[0:datalen]

    def disconnect(self):
        """Disconnect from the MCL system

        Parameters
        ----------
        none

        Returns
        -------
        none
        """

        self._stop = True
        self._write_queue.put(bytearray())
        time.sleep(2)
        self._sock_read.close()
        self._sock_write.close()
        self._ping_i_write = 0
