# -*- coding: utf-8 -*-
"""
Created on Fri Sep 24 09:36:10 2021

create_logger.py creates a custom logging event

@author: djackson
"""

import logging
import logging.handlers

from .project_vars import LOG_NAME


class log():
    def __init__(self, logger_name: str = ''):
        self.logger = None
        self.handler = None
        self.verbose_handler = None
        self.logger_name = logger_name

    def create(self,
               name: str = '',
               display_logger_name: bool = True,
               log_file: str = LOG_NAME,
               ) -> logging.Logger:
        '''
        This creates a logging event that will make the text sent to the
        command line interface to have a similar appearance when using
        MultiVuServer.py and MultiVuClient.py by having each line
        start with the 'name' if display_logger_name is True.

        This also creates the logger to be used with the 'verbose' flag
        using a DEBUG level that saves to a file.

        Parameters
        ----------
        name : str, optional
            Name to display at the start of each logging.info() event.
            This can be omitted if a name was supplied when instantiating
            the class.  If the name is blank in both cases, this will throw
            a ValueError.
        display_logger_name : bool, optional
            When True, this will display the name, otherwise it will
            just display the message. This is helpful for when running
            the server in a single thread (no need to display the name)
            compared to running it with multi-threading, where the
            MultiVuServer and MultiVuClient might be running in the same
            program. The default is True.
        log_file : str, optional
            The filename used for logging when the 'verbose' flag is set.
            The default is 'MultiVuSocket.log'

        Returns
        -------
        logger : logging.Logger
            This is the logger after being properly configured.

        Raises
        ------
        ValueError if a logger name was not supplied here or when
        instantiating the class.
        '''
        if name == '':
            if self.logger_name == '':
                raise ValueError('Must supply a logger_name')
            name = self.logger_name

        self.logger = self.get_logger(name)
        # In case the logger was not removed properly (as can happen
        # when something crashes), remove the handlers for this
        # logger and start over.
        self.remove()
        self.logger = self.get_logger(name)
        self.logger.setLevel(logging.DEBUG)

        # Configure the error handler for info messages to the std.out
        self.handler = logging.StreamHandler()
        self.handler.setLevel(logging.INFO)

        if display_logger_name:
            log_format = logging.Formatter('%(name)s - %(message)s')
        else:
            log_format = logging.Formatter('%(message)s')
        self.handler.setFormatter(log_format)

        self.handler.set_name(f'{name}-info')

        self.logger.addHandler(self.handler)

        # Configure the error handler for debug messages (including
        # messages used with the 'verbose' flag) to a log file
        self.verbose_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=2**22,
            backupCount=2)
        self.verbose_handler.setLevel(logging.DEBUG)
        f = '%(asctime)-27s %(name)-20s %(levelname)-8s %(message)s'
        verbose_format = logging.Formatter(f)
        self.verbose_handler.setFormatter(verbose_format)

        self.verbose_handler.set_name(f'{name}-debug')

        self.logger.addHandler(self.verbose_handler)

        return self.logger

    def remove(self) -> None:
        '''
        Removes all references to handlers for the logger and closes the logger
        '''
        if self.logger is not None:
            while self.logger.hasHandlers():
                if len(self.logger.handlers) == 0:
                    self.logger = None
                    break
                else:
                    for handler in self.logger.handlers:
                        handler.close()
                        self.logger.removeHandler(handler)

    def shutdown(self) -> None:
        '''
        Informs the logging system to perform an orderly
        shutdown by flushing and closing all handlers. This
        should be called at application exit and no further
        use of the logging system should be made after this
        call.
        '''
        logging.shutdown()

    def get_logger(self, log_name) -> logging.Logger:
        '''
        Return a logger with the specified name, creating it if
        necessary. If no name is specified, return the root logger.
        '''
        self.logger = logging.getLogger(log_name)
        return self.logger
