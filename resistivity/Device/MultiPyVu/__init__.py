'''
MultiPyVu provides the ability to control the temperature, magnetic field,
and chamber status of Quantum Design, Inc. products using python.  This
module includes Server(), which runs on the same computer as MultiVu,
and Client(), which is where one writes the python script to control
MultiVu.  Client() can be used within the same script as
Server(), or within its own script that runs either on the same
computer as MultiVu, or any other computer that has TCP access to the
computer running Server().  The module also contains DataFile(), which
is used to save data to a MultiVu .dat file, and read a .dat file into
a Pandas DataFrame.

One can open a gui to start the Server by calling:

> python3 -m MultiPyVu

And scripts can import the module, for example:

Import MultiPyVu as mpv
'''

'''
The UML for the project is shown below:

________________
| Subject       |
|---------------|
| subscribe     |
| unsubscribe   |
| notify        |
-----------------
        |
________\/_______________                           ________________________
|  Server               |                           |     ClientBase        |
|-----------------------|                           |-----------------------|
| open                  |                           | open                  |
| close                 |                           | close_client          |
| is_client_connected   |---                        | close_server          |
| client_address        |  |                        | query_server          |
| config_sock           |  |                        |                       |
-------------------------  |                        |                       |
                           |                        -------------------------
                           |                                |
 ________________          |                        ________\/_______________
| Inputs        |          |                        |     Client            |
|---------------|          |                        |-----------------------|
| path_leaf     |          |                        | get_sdo               |
| parse_input   |*---------|                        | set_sdo               |
| help_text     |          |                        | get_temperature       |
-----------------          |                        | set_temperature       |
                           |                        | get_aux_temperature   |
                           |                        | get_field             |
                           |   _________________    | set_field             |-|
                           |   | log           |    | get_chamber           | |
                           |   |---------------|    | set_chamber           | |
                           |   | create        |    | wait_for              | |
                           |--*| remove        |    | get_brt_temperature   | |
                           |   | shutdown      |*---| get_brt_resistance    | |
                           |   | get_logger    |    |                       | |
                           |   -----------------    |                       | |
                           |                        |                       | |
                           |                        ------------------------- |
                           |                                                  |
 |-------------------------|                                                  |
 |                                                                            |
 |                          _________________________                         |
 |                          | Message               |                         |
 |                          |-----------------------|                         |
 |                          | log_message           |                         |
 |                          | get_events            |                         |
 |                          | connection_good       |                         |
 |                          | is_read               |                         |
 |                          | is_write              |                         |
 |                          | register_read_socket  |                         |
 |                          | unregister            |                         |
 |                          | process_events        |                         |
 |                          | close                 |                         |
 |                          | shutdown              |                         |
 |                          | process_protoheader   |                         |
 |                          | process_jsonheader    |                         |
 |                          | create_request        |                         |
 |                          | read (abstract)       |                         |
 |                          | write (abstract)      |                         |
 |                          |                       |                         |
 |                          -------------------------                         |
 |                                      |                                     |
 |            |----------------------------------------------|                |
 |  __________\/_________                           _________\/__________     |
 |  |  ServerMessage    |                           | ClientMessage     |     |
 |  |-------------------|                           |-------------------|     |
 |  | read (override)   |                           | read (override)   |     |
 |-*| write (override)  |                           | write (override)  |*----|
 |  | process_read      |                           | queue_request     |     |
 |  | process_request   |                           | process_response  |     |
 |  | create_response   |                           |                   |     |
 |  | connect_sock      |                           ---------------------     |
 |  |                   |                                                     |
 |  ---------------------                                                     |
 |                                                                            |
 |                                                                            |
 |  _________________________________                                         |
 |  |   Instrument                  |                                         |
 |  |-------------------------------|                                         |
 |  | detect_multivu                |*----------------------------------------|     _________________
 |-*| initialize_multivu_win32com   |                                         |----*| SdoObject     |
    | get_multivu_win32com_instance |                                         |     | (see below)   |
    | end_multivu_win32com_instance |                                         |     -----------------
    | parse_cmd                     |                                         |             *
    ---------------------------------                                         |             |
                            |                                                 |    ------------------------
                            |                                                 |    | Brt                   |
                            |                                                 |    |-----------------------|
                            |           _____________________________         |---*| bridge_setup          |
                            |           | Command_factory           |         |    | channel_on            |
                            |           | - a module                |         |    | get_resistance        |
                            |           |---------------------------|         |    | get_current           |
                            |           | create_command_mv ------  |         |    | set_current           |
                            |----------*| _______________________ | |         |    | current_limit         |
                                        |                         | |*--------|    | power_limit           |
                                        | create_command_temp *---| |              | voltage_limit         |
                                        | create_command_field *--| |----------    | * get_temperature *   |
                                        | create_command_chamber*-| |         |    | * not implemented *   |
                                        | create_command_sdo *----| |         |    |                       |
                                        -----------------------------         |    -------------------------    
                                                                              |
                ____________________________           _____________________  |
                | CommandMultiVuBase        |          | CommandMultiVuSim |  |
                |---------------------------|          |-------------------|  |
                | get_state                 |          | _get_state_imp    |*-|
                | set_state                 |--------->|  (override)       |  |
                | _get_state_imp (abstract) |      |   ---------------------  |
                -----------------------------      |   _____________________  |
                                                   |   | CommandMultiVuImp |  |
                                                   |   |-------------------|  |
                                                   |-->| _get_state_imp    |*-|
                                                       |  (override)       |  |
                                                       ---------------------  |
                                                                              |
_____________________________                                                 |
| ICommand (abstract class) |                                                 |
|---------------------------|                                                 |
| convert_result            |                                                 |
| prepare_query             |                                                 |
| convert_state_dictionary  |                                                 |
| get_state_server          |                                                 |
| set_state_server          |                                                 |
| state_code_dict           |                                                 |
|                           |                                                 |
-----------------------------                                                 |
    |___________________                                                      |
    |   _______________\/________________       _________________________     |
    |   | CommandTemperatureBase        |       | CommandTemperatureImp |     |
    |   |-------------------------------|       |-----------------------|     |
    |   | convert_result                |       | get_state_server      |*----|
    |   | prepare_query                 |------>|  (override)           |     |
    |   | convert_state_dictionary      |   |   -------------------------     |
    |   | state_code_dict               |   |                                 |
    |   | get_state_server (abstract)   |   |                                 |
    |   | set_state_server              |   |_______________                  |
    |   ---------------------------------       ___________\/____________     |
    |                                           | CommandTemperatureSim |     |
    |                                           |-----------------------|     |
    |                                           | get_state_server      |*----|
    |                                           |  (override)           |     |
    |                                           -------------------------     |
    |___________________                                                      |
    |   _______________\/________________       _________________________     |
    |   | CommandFieldBase              |       | CommandFieldImp       |     |
    |   |-------------------------------|       |-----------------------|     |
    |   | convert_result                |       | get_state_server      |*----|
    |   | prepare_query                 |------>|  (override)           |     |
    |   | convert_state_dictionary      |   |   | set_state_server_imp  |     |
    |   | state_code_dict               |   |   |  (override)           |     |
    |   | get_state_server (abstract)   |   |   -------------------------     |
    |   | set_state_server (abstract)   |   |                                 |
    |   | set_state_server_imp (abs.)   |   |_______________                  |
    |   ---------------------------------       ___________\/____________     |
    |                                           | CommandFieldSim       |     |
    |                                           |-----------------------|     |
    |                                           | get_state_server      |*----|
    |                                           |  (override)           |     |
    |                                           | set_state_server_imp  |     |
    |                                           |  (override)           |     |
    |                                           -------------------------     |
    |                                                                         |
    |____________________                                                     |
    |   ________________\/_______________       _________________________     |
    |   | CommandChamberBase            |       | CommandChamberImp     |     |
    |   |-------------------------------|       |-----------------------|     |
    |   | convert_result                |       | get_state_server      |*----|
    |   | prepare_query                 |------>|  (override)           |     |
    |   | convert_state_dictionary      |   |   | set_state_server_imp  |     |
    |   | state_code_dict               |   |   |  (override)           |     |
    |   | get_state_server (abstract)   |   |   -------------------------     |
    |   | set_state_server              |   |                                 |
    |   | set_state_server_imp (abs.)   |   |                                 |
    |   | mode_setting_correct          |   |_______________                  |
    |   ---------------------------------       ___________\/____________     |
    |                                           | CommandChamberSim     |     |
    |                                           |-----------------------|     |
    |                                           | get_state_server      |*----|
    |                                           |  (override)           |     |
    |                                           | set_state_server_imp  |     |
    |                                           |  (override)           |     |
    |                                           -------------------------     |
    |                                                                         |
    |____________________                                                     |
        ________________\/_______________       _________________________     |
        | CommandSdoBase                |       | CommandSdoImp         |     |
        |-------------------------------|       |-----------------------|     |
        | convert_result                |       | get_state_server      |*----|
        | prepare_query                 |------>|  (override)           |     |
        | convert_state_dictionary      |   |   | set_state_server_imp  |     |
        | state_code_dict               |   |   |  (override)           |     |
        | get_state_server (abstract)   |   |   | read_sdo              |     |
        | set_state_server_imp (abs.)   |   |   | write_sdo             |     |
        |                               |   |   -------------------------     |
        ---------------------------------   |_______________                  |
                        |                       ___________\/____________     |
                        |                       | CommandSdoSim         |     |
                        |                       |-----------------------|     |
                        |                       | get_state_server      |*----|
                        |                       |  (override)           |
                        |                       | set_state_server_imp  |
                        |                       |  (override)           |
                        |                       -------------------------
                        |
                ________*_____________
                | SdoObject           |
                |---------------------|
                | str_to_obj (static) |
                -----------------------
                              |
    _________________________ |
    | generate_sdo_object   | |
    |  - a module           |*-
    | This is a separate    |
    | project for converting|
    | a .cop file           |
    |-----------------------|

______________________________________________________________________________
Model-View-Controller GUI for the Server
    In this representation, the Model is the Server class.  The code
    uses the ViewFactory class to instantiate a view.  The IView interface
    defines the necessary commands, and ViewTk is the concrete class.

     _______________
    | ViewFactory   |
    |---------------|
    | create()      |       ________________________
    -----------------       | IView                 |
            |               |-----------------------|
            |               | create_display        |
            |               | get_connection_status |
            |               | set_connection_status |
            |               | mvu_flavor (property) |
            |               | start_gui             |
            |               | quit_gui              |
            |               -------------------------
            |                     |
            |       ______________\/_________
            |       | ViewTk                |
            |       |-----------------------|
            |       | create_display        |
            |------*| get_connection_status |
                    | set_connection_status |
                    | mvu_flavor (property) |
                    | start_gui             |
                    | quit_gui              |
                    -------------------------

    _________________________
    | IController           |       _____________
    |-----------------------|       | IObserver |
    | is_client_connected   |       |-----------|
    | start_gui             |       | update    |
    | quit_gui              |       -------------
    | absolute_path         |             |
    | ip_address (property) |       _____\|/_________
    | start_server          |       | ServerInfo    |
    | stop_server           |       |---------------|
    -------------------------       | update        |
               |                    -----------------
        ______\|/________________          /|\
        | Controller            |           |
        |-----------------------|           |
        | is_client_connected   |           |
        | start_gui             |           |
        | quit_gui              |           |
        | absolute_path         |           |
        | ip_address (property) |           |
        | get_scaffolding_mode  |           |
        | set_scaffolding_mode  |           |
        | start_server          |-----------|
        | stop_server           |
        -------------------------

______________________________________________________________________________

    ________________________________
    | MultiVuDataFile               |
    |-------------------------------|
    | get_comment_col               |
    | get_time_col                  |
    | test_label                    |
    | bit_not                       |
    | add_column                    |
    | add_multiple_columns          |
    | create_file_and_write_header  |
    | set_value                     |
    | get_value                     |
    | get_fresh_status              |
    | set_fresh_status              |
    | write_data                    |
    | write_data_using_list         |
    | parse_MVu_data_file           |
    |                               |
    ---------------------------------


_______________________________________________________________________________

A list of errors.  The star (*) tells where an exception is caught.
Carrot (^) represents an unhandled error.  A called method is shown
with an arrow (->).  For each group, the original calling method is
first, and the method that throws the error is last.
_______________________________________________________________________________
Server List of MultiPyVuErrors (these should never crash a script):
- * Server.__init__():
    - Catches MultiPyVuError from instantiating Instrument
    - Exits the script if it gets this error
    -> Instrument.__init__(): Called from Server.__init__()
        - Error for old pythoncom version
        - Error if scaffolding mode doesn't specify a flavor
        - Invalid flavor chosen
        -> Instrument._connect_to_multiVu(): Called from .__init__()
            - Calling this from a non-Windows computer and not using scaffolding mode
            -> Instrument.detect_multivu(): Called from ._connect_to_multiVu()
                - no running MultiVu
                - multiple MultiVu's
            -> Instrument.initialize_multivu_win32com(): Called from ._connect_to_multiVu()
                - failed to detect a running MultiVu

- * ServerMessage.create_response(): Catches a MultiPyVuError from Instrument.parse_cmd() and returns the error message as a response (note this calls CommandMultiVuBase.get_state() and CommandMultiVuBase.set_state())
    -> Instrument.parse_cmd()
        -> CommandMultiVuBase.get_state():
            -> CommandMultiVuBase._check_command_name():
                - Unknown command
            - Catch AttributeError from calling ._get_state_imp()
            -> CommandMultiVuImp._get_state_imp(): Calls the ICommand classes
                -> ICommand.get_state_imp():
                    -> CommandChamberImp.get_state_server():
                        - Error from calling GetChamber()
                    -> CommandFieldBase.get_state_server():
                        - Error from calling GetField()
                    -> CommandTemperatureImp.get_state_server():
                        - Error from calling GetTemperature()
                    -> CommandSdoBase.get_state_server()
                        -> CommandSdoImp.readSdo():
                            - Error from calling ReadSDO()
            - Catch a KeyError from invalid state dictionary option
                -> ICommand.convert_state_dictionary():
                    -> CommandChamberBase.convert_state_dictionary()
                    -> CommandFieldBase.convert_state_dictionary()
                    -> CommandTemperatureBase.convert_state_dictionary()
                    -> CommandSdoBase.convert_state_dictionary()
        -> CommandMultiVuBase.set_state(): Catches and re-raises MultiPyVuError from .set_state_server()
            -> ICommand.set_state_server():
                -> CommandMultiVuBase._check_command_name():
                    - Unknown command
                -> ICommand.set_state_server(): These all call set_state_server_imp()
                    -> CommandChamberImp.set_state_server_imp():
                        - Error from calling SetChamber()
                    -> CommandFieldImp.set_state_server_imp():
                        - Error from calling SetField()
                    -> CommandFieldBase.set_state_server()
                        - Invalid approach_mode
                        - invalid driven_mode
                    -> CommandTemperatureImp.set_state_server():
                        - Error from calling SetTemperature()
                    -> CommandSdoImp.set_state_server()

- Server.__enter__():
    -> * Server._monitor_socket_connection():
        -> Server._accept_wrapper():
            - Called once if message is None (no socket connection)
            - Called if message.process_events() gets a ServerCloseError
            -> Instrument.get_multivu_win32com_instance(): Called from Server._accept_wrapper()
                - failed to detect a running MultiVu

- * Server.__exit__(): If MultiPyVuError comes into __exit__(), it logs the error and sets the 'safe_exit' flag to True (in other words, this is an accounted for error)

______________________________________________________________________________
Server list of ClientCloseErrors:
    This error is used to let the program know the client
    is getting shut down (CLOSE received)

- Server.__enter__():
    -> * Server._monitor_socket_connection():
        - Logs the info, calls ._update_connection_status(False), returns None
        -> ._update_connection_status()
            -> .close()
                -> __exit__()
        -> Message.process_events():
            -> ServerMessage.read():
                -> ServerMessage.process_read():
                    -> ServerMessage.process_request():
                        -> Message.create_request(): Catches a ValueError from selectors.modify
                            - ValueError indicates no server/client connection
                            - Raises a ClientCloseError from the ValueError
- Server.__enter__():
    -> * Server._monitor_socket_connection():
        - Logs the info, calls ._update_connection_status(False), returns None
        -> ._update_connection_status()
            -> .close()
                -> __exit__()
        -> Message.process_events()
            -> ServerMessage.write():
                -> ServerMessage.process_read():
                    -> ServerMessage.process_request():
                        -> Message.create_request(): Catches a ValueError from selectors.modify
                            - ValueError indicates no server/client connection
                            - Raises a ClientCloseError from the ValueError

- Server.__enter__():
    -> * Server._monitor_socket_connection(): Catches an error from Message.process_events()
        - Logs the info, calls ._update_connection_status(False), returns None
        -> ._update_connection_status()
            -> .close()
                -> __exit__()
        -> Message.process_events():
            -> * ServerMessage.read(): Catches a ClientCloseError from ._read()
                -> Message._read()
                    - This is thrown if the server or the client shut down. If the client shuts down, the server should just keep waiting for a new client to appear, so nothing happens

- Server.__enter__():
    -> * Server._monitor_socket_connection(): Catches an error from Message.process_events()
        - Logs the info, calls ._update_connection_status(False), returns None
        -> ._update_connection_status()
            -> .close()
                -> __exit__()
        -> Message.process_events(): Catches exception from self.write()
            - sleeps for 1 sec, then try .write() again.
            - throws ClientCloseError after max_tries failed attempts
            -> ServerMessage.write():
                -> Message._write():
                    - Catches OSError from sock.send() and raises a ClientCloseError

- Server.__enter__():
    -> * Server._monitor_socket_connection():
        -> Message.process_events():
            -> ServerMessage.read():
                -> ServerMessage.process_read()
                    -> ServerMessage.process_request():
                        - This is called three different times: once of the socket data is text, once if the socket data is JSON (only one fully implemented), and once if the socket data i binary
                        -> Message.create_request(): Catches a ValueError from selectors.modify
                            - ValueError indicates no server/client connection
                            - Raises a ClientCloseError from the ValueError
- Server.__enter__():
    -> *  Server._monitor_socket_connection():
        -> Message.process_events():
            -> ServerMessage.write(): Catches exception from self.write()
                - sleeps for 1 sec, then try .write() again.
                - throws ClientCloseError after max_tries failed attempts
                -> ServerMessage.process_read()
                    -> ServerMessage.process_request():
                        - This is called three different times: once of the socket data is text, once if the socket data is JSON (only one fully implemented), and once if the socket data i binary
                        -> Message.create_request(): Catches a ValueError from selectors.modify
                            - ValueError indicates no server/client connection
                            - Raises a ClientCloseError from the ValueError


______________________________________________________________________________
Server list of ServerCloseError:
    This error is used to let the program know the server
    is getting shut down (EXIT received)

- Server.__enter__():
    -> *  Server._monitor_socket_connection():
        - If process_events() comes back empty or with the 'query' of 'CLOSE' it will try to reconnect to the client
        -> Message.process_events():
            - Catches the error from .write()
            - re-raise the ServerCloseError
            -> ServerMessage.write():
                -> ServerMessage.create_response():
                    - raises a ServerCloseError if the 'action' is 'EXIT'
- Server.__enter__():
    -> *  Server._monitor_socket_connection():
        - If process_events() comes back empty or with the 'query' of 'CLOSE' it will try to reconnect to the client
        -> Message.process_events():
            -> ServerMessage.write():
                -> Message._check_exit():
                    - Checks the response 'action' and 'query' to see if they both have 'EXIT' and then calls .shutdown()


______________________________________________________________________________
Client List of MultiPyVuErrors (the Client can result in unhandled MultiPyVuErrors, shown with ^):

- ^ Client.get_aux_temperature(): Flavor must be OptiCool
- ^ Client.wait_for(): bitmask out of bounds

-> ^ ClientBase._monitor_and_get_response():
    - request['action'] is different from response['action']
    - result['result'] starts with 'MultiPyVuError: ' in order to catch errors from the Server
    - message is None and connection has broken

- * ClientBase.query_server(): Catches an error from self.__send_and_receive()
    -> ClientBase.__send_and_receive():
        - Error if response = self._monitor_and_get_response() return blanks.

- * Client.get_sdo():
    -> CommandSdoBase.convert_result():
        -Invalid response from Server
- * Client.get_temperature():
    -> CommandTemperatureBase.convert_result():
        - Invalid response from Server
- * Client.get_field():
    -> CommandFieldBase.convert_result():
        - Invalid response from Server
- * Client.get_chamber():
    -> CommandChamberBase.convert_result()
        - Invalid response from Server

- * ClientBase.__exit__():
    - If MultiPyVuError comes into __exit__(), it logs the error and sets the 'exit_without_error' flag to False (in other words, this is an unaccounted for error) so that:
        - It prints the traceback info.
        - Calls os._exit(0) to quit the script and all running threads

______________________________________________________________________________
Client list of ClientCloseErrors (indicates ClientBase._message is None):
    This error is used to let the program know the client
    is getting shut down (CLOSE received)

- ClientBase.__enter__():
    - Catches an OSError, which is the base class for ClientCloseError, ServerCloseError, and TimeoutError
    - Means it failed to make a connection to the server
    - Calls .__close_and_exit()
    -> * ClientBase.query_server():
        - Catches an error from self.__send_and_receive()
        - calls .__close_client() to close the Client
        -> ClientBase.__send_and_receive():
            - Catches an error from the Server if MultiVu is not running
        -> ClientBase.__send_and_receive():
            - self._message is None (which means no connection)
        -> ClientBase.__send_and_receive():
            -> Message.create_request(): Catches a ValueError from selectors.modify
                - ValueError indicates no server/client connection
                - Raises a ClientCloseError from the ValueError
        -> ClientBase.__send_and_receive():
            - ^ ClientBase.__monitor_and_get_response(): Catches an error from ClientMessage.process_events()
                -> Message.process_events(): Catches exception from self.write()
                    - sleeps for 1 sec, then try .write() again.
                    - throws ClientCloseError after max_tries failed attempts
                    -> ClientMessage.write(): Catches an error in Message._write()
                        -> Message._write():
                            - Catches OSError from sock.send() and raises a ClientCloseError
        -> ClientBase.__send_and_receive():
            -> ClientBase.__monitor_and_get_response():
                - Catches a ClientCloseError from Message.process_events()
                - means the client closed the client.
                - re-raises the ClientCloseError
                -> Message.process_events():
                    - ^ ClientMessage.read(): Catches error from Message._read()
                        - This is thrown if the server or the client shut down. If the server shuts down, the client needs to also shut down
                        - If the 'action' is 'START' and this error happens, then logs that there was no connection from the start.
                        - Calls Message.shutdown() which closes out the connection
                        -> Message._read():
                            - Raises ClientCloseError if the received data is None
                    - ^ ClientMessage.read():
                        -> Message._check_close():
                            - Used to let the program know the client is closing, but the server will remain open.
                            - Calls Message.shutdown(), which closes the connection, then re-raises the error

- ClientBase.__enter__():
- ClientBase.__exit__():
- ClientBase.close_server():
- Client.get_sdo():
- Client.set_sdo():
- Client.get_temperature():
- Client.set_temperature():
- Client.get_field():
- Client.set_field():
- Client.get_chamber():
- Client.set_chamber():
    -> * ClientBase.query_server():
        - Means it failed or lost the connection to the server (this could be on purpose with the user quitting the client, server, or both)
        - Calls .__close_client()

- * ClientBase.__exit__(): sets the exit_without_error flag to True

- * ClientBase.__exit__():
    - if this can't find the known errors coming in, then it sends 'CLOSE' to .query_server()
    - sets the exit_without_error flag to True
    -> * ClientBase.query_server(): Catches an error from self.__send_and_receive()
        -> ClientBase.__send_and_receive():
            - self._message is None (which means no connection)
    -> * ClientBase.query_server()
        -> ClientBase.__send_and_receive():
            -> Message.create_request(): Catches a ValueError from selectors.modify
                - ValueError indicates no server/client connection
                - Raises a ClientCloseError from the ValueError
    -> * ClientBase.query_server():
        -> ClientBase.__send_and_receive():
            - ^ ClientBase.__monitor_and_get_response(): Catches an error from ClientMessage.process_events()
                -> Message.process_events(): Catches exception from self.write()
                    - sleeps for 1 sec, then try .write() again.
                    - throws ClientCloseError after max_tries failed attempts
                    -> ClientMessage.write(): Catches an error in Message._write()
                        -> Message._write():
                            - Catches OSError from sock.send() and raises a ClientCloseError


______________________________________________________________________________
Client list of ServerCloseError:
    This error is used to let the program know the server
    is getting shut down (EXIT received)

- ^ Client.get_sdo():
    - Raise if self._message is None

- * ClientBase.close_server():
    - Sends 'EXIT' to .query_server(), and then catches the ServerCloseError (which means the server is closing) then:
        -> .__close_and_exit()
            -> .__exit__()

- ClientBase.__enter__():
- ClientBase.__exit__():
- ClientBase.close_server():
- Client.get_sdo():
- Client.set_sdo():
- Client.get_temperature():
- Client.set_temperature():
- Client.get_field():
- Client.set_field():
- Client.get_chamber():
- Client.set_chamber():
    -> * ClientBase.query_server():
        - Means it failed or lost the connection to the server (this could be on purpose with the user quitting the client, server, or both)
        - Calls .__close_and_exit()
        -> ClientBase.__send_and_receive():
            -> ClientBase.__monitor_and_get_response():
                - Means the Client closed the server
                - Catches a ServerCloseError from message.process_events()
                - re-raises the error
                    -> Message.process_events():
                        - Catches the error from .write()
                        - re-raise the ServerCloseError
                        - I do not think that the code raises a ServerCloseError in Message.write()

- ClientBase.__exit__():
    - If a ServerCloseError is received, it logs shutting down the server and sets exit_without_error to True

______________________________________________________________________________

@author: Damon D Jackson
'''


from pandas import DataFrame
from enum import IntEnum, auto
from typing import Union

from .__version import __version__
from .MultiVuServer import Server
from .MultiVuClient import Client
from .MultiVuDataFile.MultiVuDataFile import (MultiVuDataFile,
                                              TScaleType,
                                              TStartupAxisType,
                                              TTimeUnits,
                                              TTimeMode,
                                              LabelResult,
                                              MultiVuFileException,
                                             )
from .exceptions import MultiPyVuError

__version__ = __version__
__author__ = 'Damon D Jackson'
__credits__ = 'Quantum Design, Inc.'
__license__ = 'MIT'


# create a new class which inherits MultiVuDataFile,
# but modifies the enums to make them simpler.

class Scale_T(IntEnum):
    linear_scale = auto()
    log_scale = auto()


class Startup_Axis_T(IntEnum):
    none = 0
    X = 1
    Y1 = 2
    Y2 = 4
    Y3 = 8
    Y4 = 16


class Time_Units_T(IntEnum):
    minutes = auto()
    seconds = auto()


class Time_Mode_T(IntEnum):
    relative = auto()
    absolute = auto()


class DataFile():
    '''
    This class is used to save data in the proper MultiVu file format.
    An example for how to use this class may be:
        >
        > import MultiPyVu as mpv
        >
        > data = mpv.MultiVuDataFile()
        > mv.add_column('myY2Column', data.startup_axis.Y2)
        > mv.add_multiple_columns(['myColumnA', 'myColumnB', 'myColumnC'])
        > mv.create_file_and_write_header('myMultiVuFile.dat', 'Using Python')
        > mv.set_value('myY2Column', 2.718)
        > mv.set_value('myColumnA', 42)
        > mv.set_value('myColumnB', 3.14159)
        > mv.set_value('myColumnC', 9.274e-21)
        > mv.write_data()
        >
        > myDataFrame = data.parse_MVu_data_file('myMultiVuFile.dat')

    '''
    def __init__(self):
        # references to enums
        self.scale = Scale_T
        self.startup_axis = Startup_Axis_T
        self.time_units = Time_Units_T
        self.time_mode = Time_Mode_T
        self.data_file = MultiVuDataFile()

    def get_comment_col(self) -> str:
        return self.data_file.get_comment_col()

    def get_time_col(self) -> str:
        return self.data_file.get_time_col()

    def test_label(self, label) -> LabelResult:
        '''
        Return the type of label.

        Parameters
        ----------
        label : string

        Returns
        -------
        LabelResult.success : LabelResults

        Example
        -------
        >>> test_label('Comment')
            success
        '''
        return self.data_file.test_label(label)

    def add_column(self,
                   label: str,
                   startup_axis: Startup_Axis_T = Startup_Axis_T.none,
                   scale_type: Scale_T = Scale_T.linear_scale,
                   persistent: bool = False,
                   field_group: str = ''
                   ) -> None:
        '''
        Add a column to be used with the datafile.

        Parameters
        ----------
        label : string
            Column name
        startup_axis : Startup_Axis_T, optional
            Used to specify which axis to use when plotting the column.
            .startup_axis.none (default)
            .startup_axis.X (default is the time axis)
            .startup_axis.Y1
            .startup_axis.Y2
            .startup_axis.Y3
            .startup_axis.Y4
        scale_type : Time_Units_T, optional
            .time_units.linear_scale (default)
            .time_units.log_scale
        Persistent : boolean, optional
            Columns marked True have the previous value saved each time data
            is written to the file.  Default is False
        field_group : string, optional

        Raises
        ------
        MultiVuFileException
            Can only write the header once.

        Returns
        -------
        None.

        Example
        -------
        >>> add_column('MyDataColumn')
        '''
        start = TStartupAxisType(startup_axis)
        scale = TScaleType(scale_type)
        return self.data_file.add_column(label,
                                         start,
                                         scale,
                                         persistent,
                                         field_group,
                                         )

    def add_multiple_columns(self, column_names: list) -> None:
        '''
        Add a column to be used with the datafile.

        Parameters
        ----------
        column_names : list
            List of strings that have column names

        Returns
        -------
        None.

        Example
        -------
        >>> add_multiple_columns(['MyDataColumn1', 'MyDataColumn2'])
        '''
        return self.data_file.add_multiple_columns(column_names)

    def create_file_and_write_header(self,
                                     file_name: str,
                                     title: str,
                                     time_units: Time_Units_T = Time_Units_T.seconds,
                                     time_mode: Time_Mode_T = Time_Mode_T.relative
                                     ):
        units = TTimeUnits(time_units)
        mode = TTimeMode(time_mode)
        return self.data_file.create_file_and_write_header(file_name,
                                                           title,
                                                           units,
                                                           mode)

    def set_value(self, label: str, value: Union[str, int, float]):
        '''
        Sets a value for a given column.  After calling this method, a call
        to write_data() will save this to the file.

        Parameters
        ----------
        label : string
            The name of the data column.
        value : string, int, or float
            The data that needs to be saved.

        Raises
        ------
        MultiVuFileException
            The label must have been written to the file.

        Returns
        -------
        None.

        Example
        -------
        >>> set_value('myColumn', 42)

        '''
        return self.data_file.set_value(label, value)

    def get_value(self, label: str) -> Union[str, int, float]:
        '''
        Returns the last value that was saved using set_value(label, value)

        Parameters
        ----------
        label : str
            Column name.

        Raises
        ------
        MultiVuFileException
            The label must have been written to the file.

        Returns
        -------
        str, int, or float
            The last value saved using set_value(label, value).

        Example
        -------
        >>> get_value('myColumn')
        >>> 42

        '''
        return self.data_file.get_value(label)

    def get_fresh_status(self, label: str) -> bool:
        '''
        After calling set_value(label, value), the value is considered Fresh
        and is waiting to be written to the MultiVu file using write_data()

        Parameters
        ----------
        label : str
            Column name.

        Raises
        ------
        MultiVuFileException
            The label must have been written to the file.

        Returns
        -------
        boolean
            True means the value has not yet been saved to the file

        Example
        -------
        >>> get_fresh_status('myColumn')
        >>> True

        '''
        return self.data_file.get_fresh_status(label)

    def set_fresh_status(self, label: str, status: bool):
        '''
        This allows one to manually set the Fresh status, which is used
        to decide if the data will be written to the file when calling
        write_data()

        Parameters
        ----------
        label : str
            Column name.
        status : boolean
            True (False) means the value in the column label
            will (not) be written.

        Raises
        ------
        MultiVuFileException
            The label must have been written to the file.

        Returns
        -------
        None.

        Example
        -------
        >>> set_fresh_status('myColumn', True)
        '''
        return self.data_file.set_fresh_status(label, status)

    def write_data(self, get_time_now: bool = True):
        '''
        Writes all fresh or persistent data to the MultiVu file.

        Parameters
        ----------
        get_time_now : boolean, optional
            By default, the time when this method is called will be
            written to the MultiVu file. The default is True.

        Raises
        ------
        MultiVuFileException
            create_file_and_write_header() must be called first.

        Returns
        -------
        None.

        Example
        -------
        >>> write_data()
        '''
        return self.data_file.write_data(get_time_now)

    def write_data_using_list(self, data_list: list, get_time_now: bool = True):
        '''
        Function to set values fromm list and then write them to data file
        Format of list is ColKey1, Value1, ColKey2, Value2, ...
        The list can contain values for all columns or a subset of columns,
        in any order

        Parameters
        ----------
        data_list : list
            A list of column names and values.
        get_time_now : boolean, optional
            By default, the time when this method is called will be
            written to the MultiVu file. The default is True.

        Raises
        ------
        MultiVuFileException
            The number of columns and data must be equal, which means
            that the list needs to have an even number of items.

        Returns
        -------
        None.

        Example
        -------
        >>> write_data_using_list(['myColumn1', 42, 'myColumn2', 3.14159])
        '''
        return self.data_file.write_data_using_list(data_list, get_time_now)

    def parse_MVu_data_file(self, file_path: str) -> DataFrame:
        '''
        Returns a pandas DataFrame of all data points in the given file

        Parameters
        ----------
        file_path : str
            Path to the MultiVu file.

        Returns
        -------
        pandas.DataFrame
            A DataFrame which includes all of the columns and data.

        Example
        -------
        >>> parse_MVu_data_file('myMvFile.dat')

        '''
        return self.data_file.parse_MVu_data_file(file_path)


# TODO - these are here just to be compatible with
# the first release of the software.  They should
# be removed after version 2 gets updated
# TODO - also remove the src/MultiPyVuDataFile folder
# and everything inside it.
from warnings import warn
class old_MultiVuClient():

    def MultiVuClient(self, *args, **kwargs):
        adapter = self.Client_v1_adapter(*args, **kwargs).get_instance()
        return adapter

    class Client_v1_adapter(Client):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            self.temperature = Client.temperature
            self.field = Client.field
            self.chamber = Client.chamber

        def get_instance(self):
            return self

        def __enter__(self):
            msg = '\n|DEPRECATION WARNING: Instantiating this class using this '
            msg += 'method has been deprecated.  Rather than importing the module '
            msg += 'using:\n'
            msg += '|\tfrom MultiPyVu import MultiVuClient as mvc\n'
            msg += '|and then instantiating it using:\n'
            msg += '|\twith mvc.MultiVuClient() as client:\n'
            msg += '|---------------------------------------\n'
            msg += '|Use the following simpler method:\n'
            msg += '|\timport MultiPyVu as mpv\n'
            msg += '|\twith mpv.Client() as client:\n'
            msg += '|\t\tT, sT = client.get_temperature()\n'
            msg += '|\t\tclient.set_temperature(set_point,\n'
            msg += '|\t\t                       rate,\n'
            msg += '|\t\t                       client.temperature.approach_mode.no_overshoot\n'
            msg += '|\t\t                       )\n'
            msg += '|\t\tclient.set_field(set_point,\n'
            msg += '|\t\t                 rate,\n'
            msg += '|\t\t                 client.field.approach_mode.oscillate,\n'
            msg += '|\t\t                 client.field.driven_mode.driven\n'
            msg += '|\t\t                 )\n'
            msg += '|\t\tclient.set_chamber(client.chamber.mode.pump_continuous)\n'
            msg += '|---------------------------------------\n\n'
            warn(msg, FutureWarning, stacklevel=2)
            return super().__enter__()


MultiVuClient = old_MultiVuClient()


class old_MultiVuServer():

    def MultiVuServer(self, *args, **kwargs):
        adapter = self.Server_v1_adapter(*args, **kwargs).get_instance()
        return adapter

    class Server_v1_adapter(Server):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)

        def get_instance(self):
            return self

        def __enter__(self):
            msg = '\n|DEPRECATION WARNING: Instantiating this class using this '
            msg += 'method has been deprecated.  Rather than importing the module '
            msg += 'using:\n'
            msg += '|\tfrom MultiPyVu import MultiVuServer as mvs\n'
            msg += 'and then instantiating it using:\n'
            msg += '|\ts = mvs.MultiVuServer(keep_server_open=True)\n'
            msg += '|\ts.open()\n'
            msg += '|---------------------------------------\n'
            msg += '|Use the following simpler method:\n'
            msg += '|\timport MultiPyVu as mpv\n'
            msg += '|\ts = mpv.Server(keep_server_open=True)\n'
            msg += '|\ts.open()\n'
            msg += '|---------------------------------------\n\n'
            warn(msg, FutureWarning, stacklevel=2)
            return super().__enter__()


MultiVuServer = old_MultiVuServer()
