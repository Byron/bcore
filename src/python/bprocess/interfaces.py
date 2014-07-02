#-*-coding:utf-8-*-
"""
@package bprocess.interfaces
@brief Interfaces dealing with the startup engine for processes

@author Sebastian Thiel
@copyright [GNU Lesser General Public License](https://www.gnu.org/licenses/lgpl.html)
"""
from __future__ import unicode_literals
__all__ = ['IProcessControllerDelegate', 'IControlledProcessInformation']

from butility import (Interface,
                      abstractmethod)


class IProcessControllerDelegate(Interface):
    """A delegate used by the ProcessController to guide how to build the environment of the application"""
    # Can't do slots due to layout conflict issues
    # __slots__ = ('_app')

    # -------------------------
    ## @name Constants
    # @{

    ## Indicate the current process to be replaced by the launched one
    LAUNCH_MODE_REPLACE = 'replace/execve'

    ## Indicate you want to spawn the launched process as a child
    LAUNCH_MODE_CHILD = 'child/spawn'

    ## Indicate you want to fork the process, and maintain it as a sibling
    LAUNCH_MODE_SIBLING = 'sibling/fork'

    launch_modes = (LAUNCH_MODE_REPLACE, LAUNCH_MODE_CHILD, LAUNCH_MODE_SIBLING)

    ## -- End Constants -- @}

    def __init__(self, application, package_name):
        """initialize this instance with an Application. It will may be used for querying settings.
        It's important to never use the global one at bapp.main() to keep everything contained
        @param application Application instance, shared with parent ProcessController
        @param package_name the name of the package we are used for. Useful for querying your own configuration
        @note our _app must be considered read-only, unless specified otherwise in the respecitve method"""
        super(IProcessControllerDelegate, self).__init__()
        self._app = application

    # -------------------------
    ## @name Delegate Interface
    # Interface used by IProcessController
    # @{

    @abstractmethod
    def prepare_context(self, executable, environ, args, cwd):
        """A call to allow changing configuration based on other context that the controller may not know.
        This method is executed after the initial context configuration was performed by the controller, 
        based on the current working directory and the executable's location.
        The delegate should - if adequate - alter the applications context stack by pushing a new contexts on top to
        setup overrides, see Application.context() for more information.
        It may also change the environment variables (env), and modify the executable arguments (args).
        @param executable Path to executable that might be instantiated based on the most recent configuration.
        The path may still contain environment variables, but should be existing.
        If in doubt, don't make assumptions about a path which appears to exist on disk, but work with it on
        string level.
        @param environ dictionary with all environment variables to be used in the new process
        @param args a list of all process arguments
        @param cwd a Path instance to the current working directory
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
    def resolve_value(self, value, env):
        """Using the environment `env`, the value at an environment variable will be substituted recursively.
        This allows packages to communicate all kinds of information, using environment variables only, and 
        do so in a portable way.
        @param value a single string
        @param env a dict with variable:value pairs
        @return the substituted value"""
    
    @abstractmethod
    def pre_start(self, executable, env, args, cwd, resolve):
        """Called right before starting the process, and is meant to allow the delegate to see everything influencing 
        the soon-to-be-created process.
        The delegate can modify any of the arguments, or return them unchanged.
        @param executable an unverified bapp.path object to the executable the controller would try to launch.
        It does not contain environment variables anymore.
        @param env process environment as created from scratch by the controller
        @param args argument list as provided initially to the bootstrapper. You can parse them or adjust them
        to your liking. It does not contain the executable itself.
        Please note that the args produced here are handed to the application directly
        @param cwd path representing the current working directory
        @param resolve we will look for arguments that need substitution.
        This resolution could be any kind of transformation, like substiting commandline arguments
        @return (executable, env, args, cwd) containing possibly altered versions of the given variables
        @note even though it would be possible, the delegate must not attempt to start the program himself"""
    
    @abstractmethod
    def launch_mode(self):
        """@return one of the LAUNCH_MODE_* constants, or None in case you don't want to set an override.
        If launch_mode ends up not being LAUNCH_MODE_REPLACE, communicate() will be called afterwards, with 
        the spawned instance.
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


class IControlledProcessInformation(Interface):
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
    storage_environment_variable = 'BPROCESS_POST_LAUNCH_INFORMATION'
    
    
    ## A yaml-formatted data structure to provide information matching the process_schema
    process_information_environment_variable = 'BPROCESS_INFORMATION_YAML'
    
    
    ## A yaml-formatted structure keeping commandline overrides.
    commandline_overrides_environment_variable = 'BPROCESS_COMMANDLINE_OVERRIDES_YAML'

    ## An encoded storage for all yaml files which are part of our configuration which is stored 
    ## in BPROCESS_POST_LAUNCH_INFORMATION
    config_file_hash_map_environment_variable = 'BPROCESS_CONFIG_FILE_HASHMAP'
    
    ## -- End Configuration -- @}
    
    # -------------------------
    ## @name Query Interface
    # @{
    
    @abstractmethod
    def data(self):
        """@return an OrderedDict containing the complete data set as known to the bootstrapper, or None 
        if this process wasn't started that way.
        Its raw data, and you must know the schema's used to use it properly. Even though this interface doesn't
        enforce it, the client should use a kvstore + schemas to access it safely."""
        
    @classmethod
    @abstractmethod
    def has_data(cls, environ = None):
        """@return True if we have data, as we are launched through process control
        @param environ may be a dictionary with environment variables, which store information required to determine
        if we were launched with process control. Defaults to os.environ otherwise"""
        
        
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
        """@return hash map used by the HierarchicalContext type, based on all files we loaded
        in the wrapper's environment, or None if there is no such data
        """
    ## -- End Query Interface -- @}

    

# end class IPostLaunchInformation

