#-*-coding:utf-8-*-
"""
@package tx.processcontrol.interfaces
@brief Interfaces dealing with the startup engine for processes

@copyright 2012 Sebastian Thiel
"""
__all__ = ['IProcessControllerDelegate', 'IPostLaunchProcessInformation']

import bcore
from bcore import abstractmethod


class IProcessControllerDelegate(tx.InterfaceBase):
    """brief docs"""
    __slots__ = ()

    # -------------------------
    ## @name Delegate Interface
    # Interface used by IProcessController
    # @{
    
    @abstractmethod
    def prepare_environment(self, executable, env, args, cwd):
        """A call to allow changing configuration based on other context that the controller may not know.
        This method is executed after the initial environment configuration was performed by the controller, 
        based on the current working directory and the executable's location.
        The delegate should - if adequate - alter the environment stack by pushing a new environment on top to
        setup overrides, see tx.environment for more information.
        It may also change the environment (env), and modify the executable arguments (args).
        @note for a variable description, see pre_start()
        @note you must not use this method to alter argument lists, see pre_start() for that reason"""
       
    @abstractmethod
    def variable_is_path(self, environment_variable):
        """@return True if the given environment variable is describing a path. If this is the case, 
        they can become lists of path using the OS dependent path separator"""
        return environment_variable.lower().endswith('path')
        
    @abstractmethod
    def variable_is_appendable(self, environment_variable, value):
        """@return True if the given environment variable (and/or it's additional/new value) can be appended to.
        If the return value is False, the value will be overridden. Otherwise the path will be appended using the
        platform's path separator
        @param environment_variable a variable name for which variable_is_path() returned True
        @param value the variables new or to-be-appended value, after verify_path() was called on it."""
        
    @abstractmethod
    def verify_path(self, environment_variable, path):
        """Check if the given Path instance is valid and accessible. It will be set in the given environment variable
        which was previously classified as path-related variable by variable_is_path().
        @param environment_variable the environment variable
        @param path Path instance with the resolved path that would be set
        @return the path that is to be set, or None if the path should be dropped
        @note its up to the implementor to log this incident"""
    
    @abstractmethod
    def pre_start(self, executable, env, args, cwd):
        """Called right before starting the process, and is meant to allow the delegate to see everything influencing 
        the soon-to-be-created process.
        The delegate can modify any of the arguments, or return them unchanged.
        @param executable an unverified tx.path object to the executable the controller would try to launch
        @param env process environment as created from scratch by the controller
        @param args argument list as provided initially to the bootstrapper. You can parse them or adjust them
        to your liking. It does not contain the executable itself.
        @param cwd path representing the current working directory
        @return (executable, env, args, cwd) containing possibly altered versions of the given variables
        @note even though it would be possible, the delegate must not attempt to start the program himself"""
    
    @abstractmethod
    def should_spawn_process(self):
        """@return True if the process must be spawned by the process controller. Otherwise it will be 
        called using execve. If True, communicate() will be called afterwards, with the spawned instance.
        @note called after pre_start
        """
        
    @abstractmethod
    def process_filedescriptors(self):
        """If the process is to be spawned, this method is called right before the process is instantiated
        and is expected to define its standard file descriptors based on the possible values allowed by 
        [Subprocess.Popen(...)](http://docs.python.org/2/library/subprocess.html#subprocess.Popen)
        @return (stdin, stdout, stderr) a tuple of 3 values, each defining the desired value for the [Popen
        constructor](http://docs.python.org/2/library/subprocess.html#subprocess.Popen)."""
        
    @abstractmethod
    def communicate(self, process):
        """Communicate to the spawned process until it is done with its execution
        @note this can also be used to manipulate its return value which may in turn affect the return value of
        the parent process
        @note not called when process replaced the current one
        @return the given process
        """
        
    ## -- End Delegate Interface -- @}

# end class IProcessControllerDelegate


class IPostLaunchProcessInformation(tx.InterfaceBase):
    """An interface to provide information about the currently running process as launched by the IProcessController.
    It works for spawned as well as for replaced processes (execv).
    
    The interface is entirely read-only, and works together with IProcessController implementations as those 
    have to deposit the information in the first place.
    """
    __slots__ = ()
    
    # -------------------------
    ## @name Configuration
    # Some basic variables to help unifying the way information is stored
    # @{
    
    ## Environment variable to hold formatted datastructure with information about the running process.
    # The actual format is an implementation detail.
    storage_environment_variable = 'TX_PROCESS_POST_LAUNCH_INFORMATION'
    
    
    ## A yaml-formatted data structure to provide information matching the process_schema
    process_information_environment_variable = 'TX_PROCESS_INFORMATION_YAML'
    
    
    ## A yaml-formatted structure keeping commandline overrides.
    commandline_overrides_environment_variable = 'TX_PROCESS_COMMANDLINE_OVERRIDES_YAML'

    ## An encoded storage for all yaml files which are part of our configuration which is stored 
    ## in TX_PROCESS_POST_LAUNCH_INFORMATION
    config_file_hash_map_environment_variable = 'TX_PROCESS_CONFIG_FILE_HASHMAP'
    
    ## -- End Configuration -- @}
    
    # -------------------------
    ## @name Query Interface
    # @{
    
    @abstractmethod
    def data(self):
        """@return an OrderedDict containing the complete data set known to the wrapper, or None if this process 
        wasn't started that way.
        Its raw data, and you must know the schema's used to use it properly. Even though this interface doesn't
        enforce it, the client should use a kvstore + schemas to access it safely.
        @note The implementation assures that this information is only available for the launched process, and
        not for its children"""
        
    @abstractmethod
    def has_data(self):
        """@return True if we have data, as we are launched through process control"""
        
        
    @abstractmethod
    def process_data(self):
        """@return a DictObject with data matching the process_schema or None if this process wasn't started
        with process-control"""
        
    @abstractmethod
    def commandline_overrides(self):
        """@return a Dict with commandline overrides specified at wrap time. This allows the calling 
        process to re-apply those overrides. It can be None if this process was not launched through the 
        wrapper, or if there where no commandline overrides. User has_data() as an indicate for a 
        wrapped process"""
        
    @abstractmethod
    def config_hashmap(self):
        """@return hash map used by the ConfigHierarchyEnvironment type, based on all files we loaded
        in the wrapper's environment, or None if there is no such data
        """
    ## -- End Query Interface -- @}

    

# end class IPostLaunchInformation

