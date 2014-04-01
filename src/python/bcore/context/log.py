#-*-coding:utf-8-*-
"""
@package bcore.context.log
@brief A module to help initializing the logging system

@copyright 2013 Sebastian Thiel
"""
__all__ = ['LogConfigurator']

import os
import sys
import warnings

from .utility import ContextStackClient
from bkvstore import KeyValueStoreSchema

from butility import Path

import logging
import logging.config



# ==============================================================================
## @name Classes
# ------------------------------------------------------------------------------
## @{

class _KVStoreLoggingVerbosity(object):
    """Implements a valid verbosity"""
    __slots__ = ('level')
    
    def __init__(self, value = 'INFO'):
        if not hasattr(logging, value):
            raise ValueError("Invalid logging verbosity: %s" % value) 
        # end check if value exists
        self.level = getattr(logging, value)

# end class _KVStoreLoggingVerbosity


class LogConfigurator(ContextStackClient):
    """Implements the ILog interface and allows to initialize the logging system using context configuration"""
    __slots__ = ()
    
    # -------------------------
    ## @name Configuration
    # @{
    
    _schema = KeyValueStoreSchema('logging', {'logdir' : Path,      
                                                        # Directory into which to drop files. If empty, there
                                                        # will be no file logger
                                              'inifile' : Path,
                                                        # Ini file to read to configure logging.
                                              'verbosity' : _KVStoreLoggingVerbosity,
                                                        # Disables any kind of logging configuration
                                                        # which may be provided by the host application
                                                        # NOTE: At some point we should control it precise
                                                        # enough to never use this flag
                                              'disable' : False
                                            })
    
    ## -- End Configuration -- @}
    
    @classmethod
    def initialize(cls):
        """Initialize the logging system using the information provided by the context
        @note at some point we might want to implement a more sophisticated yaml based log initialization"""
        # definition of possible overrides (i.e. which configuration file to use)
        value = cls.settings_value()
        log_config_file = value.inifile
        
        # See #6239
        # NOTE: at least the environment variable can probably be removed once the actual culprit is found
        # Why does our configuration kill pythons logging entirely in case of katana at least ?
        if value.disable or 'BCORE_LOGGING_INITIALIZATION_DISABLE' in os.environ:
            return
        # end no init if disabled
    
        # initialize fallback defaults if no configuration file was found
        if not log_config_file or not os.path.isfile(log_config_file):
            warnings.warn("logging system using basic configuration, log config file '%s' wasn't accessible" % log_config_file)
            logging.basicConfig()
        else:
            # BUGFIX 3369
            # HOW STUPID IS THIS ? Now os throws different WindowsError on ... Windows ?? To add insult
            # to injury ... it doesn't even exist on linux ... so we have to except all here
            import __builtin__
            additional_exception = getattr(__builtin__, 'WindowsError', IOError)
            
            # BUGFIX 2759
            # make sure the appropriate path exists and is writable, otherwise warn and use different temporary
            # directory..
            try:
                # DO NOT DISABLE LOGGERS CREATED SO FAR ! What a shitty default !
                logging.config.fileConfig(log_config_file, disable_existing_loggers=False)
            except (IOError, additional_exception), err:
                warnings.warn("logging configuration from ini file failed with error: %s" % str(err))
                base_setup()
            #end handle unwritable paths
        #end create configuration if not yet set
    
        log = logging.root
        log.setLevel(value.verbosity.level)
        
        # Setup logfile
        if value.logdir:
            if not value.logdir.isdir():
                try:
                    value.logdir.makedirs()
                    # Make sure that everyone can write into that folder - especially important for the farm
                    # available on windows
                    value.logdir.chmod(0777)
                except (OSError, IOError):
                    log.error("Could not create log directory at %s", value.logdir)
            # end handle logdir creation
            
            if value.logdir.isdir():
                try:
                    logfile_handler = handlers.DefaultLogFileHandler(value.logdir)
                    logfile_handler.setFormatter(formatters.LogFileFormatter())
                    log.addHandler(logfile_handler)
                except (OSError, IOError):
                    log.error("Could not write log into directory '%s'", value.logdir)
                # end handle write problems - we must never abort ... 
            else:
                log.error("Log directory at %s did not exist - file logging disabled", value.logdir)
            # end handle logdir exists
        else:
            log.debug("Logging to directory disabled")
        # end handle logdir exists
        
# end class LogConfigurator

## -- End Classes -- @}
