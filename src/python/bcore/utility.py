#-*-coding:utf-8-*-
"""
@package bcore.utility
@brief Contains utilities with minimal dependencies

@copyright 2014 Sebastian Thiel
"""
__all__ = ['ApplicationSettingsClient', 'LogConfigurator', 'StackAwareHierarchicalContext']

import os
import warnings
import hashlib
import logging
import logging.config

from butility import (Path,
                      OrderedDict)

from bkvstore import KeyValueStoreSchema
from bcontext import HierarchicalContext
import bcore



# ==============================================================================
## @name Types
# ------------------------------------------------------------------------------
## @{

class ApplicationSettingsClient(object):
    """Base implementation to allow anyone to safely use the context of the global Context stack.
    Everyone using the global context should derive from it to facilitate context usage and to allow the 
    ContextStack to verify its data.
    
    This type basically brings together a schema with another type, to make data access to any context easy
    @todo this system is for review, as there will be no 'global' state that we may know here. This would go to the bapplication interface
    """
    __slots__ = ()

    ## Schema specifying how we would like to access the global context 
    ## It must be set by subclasses if they access the context
    ## The base implementation of schema() will just return this class-level instance, per instance 
    ## schemas are generally possible though
    _schema = None 
    
    @classmethod
    def settings_schema(cls):
        """@return our schema instance, by default it will return the class level instance
        """
        assert isinstance(cls._schema, KeyValueStoreSchema), "Subclass must provide a schema instance"
        return cls._schema
        
    @classmethod
    def settings_value(cls, context = None, resolve=True):
        """@return a nested dict with getattr access as obtained from the current ContextStack's context, 
        validated against our schema.
        @param cls
        @param context if not None, use the given context (KeyValueStoreProvider) instead of the global one
        @param resolve if True, string values will be resolved
        @note use this method when you need access to the datastructure matching your schema"""
        return (context or bcore.app().context().settings()).value_by_schema(cls.settings_schema(), resolve=resolve)


# end class ApplicationSettingsClient


class StackAwareHierarchicalContext(HierarchicalContext):
    """A context which will assure a configuration file is never loaded twice.
    This can happen if paths have common roots, which is the case almost always.

    To prevent duplicate loads, which in turn may yield somewhat unexpected application settings, this implementation 
    uses the current applications stack to find other Contexts of our type.
    """
    __slots__ = ('_hash_map')

    def __init__(self, directory, **kwargs):
        super(StackAwareHierarchicalContext, self).__init__(directory, **kwargs)
        self._hash_map = OrderedDict()

    def _iter_application_contexts(self):
        """@return iterator yielding environments of our type on the stack, which are not us"""
        for ctx in bcore.app().context().stack():
            # we should be last, but lets not assume that
            if ctx is self or not isinstance(ctx, StackAwareHierarchicalContext):
                continue
            yield ctx
        # end for each environment
        
    def _filter_directories(self, directories):
        """@note default implementation will ignore directories that have already been loaded by other environments
        on the stack
        """
        # for now, just iterate the environment stack directly, lets just pretend we know it very well
        # as we are an environment !
        # We keep file ordering
        current_dirs = set()
        for ctx in self._iter_application_contexts():
            current_dirs |= set(ctx.config_directories())
        # end for each stack environment
        return filter(lambda dir: dir not in current_dirs, directories)

    def _filter_files(self, files):
        """@note our implementation will compare file hashes in our own hash map with ones of other
        instances of this type on the stack to assure we don't accidentally load the same file
        @note This method will update our _hash_map member"""
        for config_file in files:
            self._hash_map[hashlib.md5(open(config_file).read()).digest()] = config_file
        #end for each file
        
        # subtract all existing hashes
        our_files = set(self._hash_map.keys())
        for env in self._iter_application_contexts():
            our_files -= set(env._hash_map.keys())
        #end for each environment
        
        # return all remaining ones
        # Make sure we don't change the sorting order !
        return list(self._hash_map[key] for key in self._hash_map if key in our_files) 

    # -------------------------
    ## @name Interface
    # @{

    def hash_map(self):
        """@return a dictionary of a mapping of md5 binary strings to the path of the loaded file"""
        return self._hash_map
    
    ## -- End Interface -- @}

# end class StackAwareHierarchicalContext


class _KVStoreLoggingVerbosity(object):
    """Implements a valid verbosity"""
    __slots__ = ('level')
    
    def __init__(self, value = 'INFO'):
        if not hasattr(logging, value):
            raise ValueError("Invalid logging verbosity: %s" % value) 
        # end check if value exists
        self.level = getattr(logging, value)

# end class _KVStoreLoggingVerbosity


class LogConfigurator(ApplicationSettingsClient):
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
                                                        # NOTE: At some point we should control it precisely
                                                        # enough to never use this flag
                                                        # NOTE: it is up to the configuration to enable this one
                                              'disable' : True
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
            if not log_config_file:
                warnings.warn("logging.inifile is not set, resorting to standard logging setup")
            else:
                warnings.warn("log config file '%s' wasn't accessible, resorting to standard logging setup" % log_config_file)
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

## -- End Types -- @}
