#!/usr/bin/env python2.6
#-*-coding:utf-8-*-
"""
@package bcore.bin.wrapper
@brief bootstrapper to allow importing bcore with the actual implementation

@note this is an executable which is not meant to be imported. All dependencies are included in the file

@copyright 2012 Sebastian Thiel
"""
__all__ = ['Bootstrapper']

import sys
import os
import traceback
import logging
from itertools import chain

basename = os.path.basename
dirname = os.path.dirname


# Make sure bcore doesn't initialize the environment as the wrapper logic takes care of that
os.environ['BCORE_INIT_ENVIRONMENT_DISABLE'] = '1'

# BASIC LOGGING SETUP
#####################
logging.basicConfig()
# default stream output will be to stderr, which is good to separate output of program and wrapper
# in case there really is something to say
# Set lowest logging verbosity for a start
for item in chain([logging.root], logging.root.handlers):
    item.setLevel(logging.ERROR)
# end handle logging init



class Bootstrapper(object):
    """Contains for logic required to import bcore and launch the actual implementation from our root package.
    It implements the following algorithm
    
    * Find the wrapper's original, non-symlinked location and see if it is within its source tree. The following 
      locations are tried in order
    ** read BCORE_PIPE_PACKAGE_PATH variable to the location from which root_package_name can be imported
    ** follow symlink of this file
    ** On windows, a side-by-side file will be read for the path to follow.
    * finally, adjust the path to initialize the root package and pass control to its implementation
    
    @note this bootstrapper needs to be symlinked to a certain location/basename to work 
    """
    __slots__ = ( )
    
    # -------------------------
    ## @name Configuration
    # @{
    
    ## A variable we can use to override the pipeline root package location, useful for testing
    pipe_package_env_var = 'BCORE_PIPE_PACKAGE_PATH'
    
    ## Name of the root package that contains all of the core code
    root_package_name = 'bcore'
    
    ## module path to wrapper engine interface
    engine_interface_module_name = 'processcontrol'
    
    ## module path to the core implementation
    engine_module_name = 'processcontrol'
    
    
    ## Process controller interface name
    process_controller_interface_name = 'ProcessController'
    
    ## -- End Configuration -- @}

    # -------------------------
    ## @name Utiltiies
    # @{
    
    def _resolve_winlink(self, executable):
        """Read a path from a side-by-side file and resolve it like a symlink"""
        symlink_file = os.path.join(os.path.dirname(executable), '.' + os.path.basename(executable))
        if not os.path.isfile(symlink_file):
            msg = "Side-by-side symlink file '%s' symlink file did not exist - first line should be the location of the wrapper implementation"
            raise EnvironmentError(msg % symlink_file)
        # end handle missing ifle
        
        try:
            link = open(symlink_file, 'rt').readline()
        except (OSError, IOError), err:
            raise EnvironmentError("Could not access symlink file '%s' for reading: %s" % (symlink_file, str(err)))
        # end handle exception
        
        if os.path.isabs(link):
            return link
        # handle absolute paths
        
        # otherwise, treat it as relative to the executable dir
        return os.path.join(os.path.dirname(executable), link)
        
    def _process_controller_class(self, executable):
        """Try to make our root-package available which should include the components framework
        to do that actual woractual_executablek for us
        Raise an error if that didn't work
        @return controller clas"""
        
        # If we have an override, use it
        if self.pipe_package_env_var in os.environ:
            root_package_path = os.environ[self.pipe_package_env_var]
        else:
            
            # on windows, we read the link from a side-by-side file
            if os.name == 'nt':
                actual_executable = self._resolve_winlink(executable)
            else:
                actual_executable = os.path.realpath(executable)
            # end handle windows
            
            # Currently we need this. We could overcome the issue with environment variables or a config file 
            # being read here, but it would just complicate matters - we can always have symlinks
            # NOTE: this wouldn't work on windows, as read-link doesn't work there - its all done by samba underneath
            # Therefore we would need some configuration/pseudo-link there
            assert actual_executable != executable, "The executable %s must be as symlink to the bootstrapper implementation"
            executable = actual_executable
            
            root_package_path = self._root_package_path(executable)
            if root_package_path is None:
                msg = "Unable to find our root-package from wrapper location at %s"
                msg += " - please make sure you symlink it from its source to the destination"
                raise AssertionError(msg % executable)
            # end handle root_package not found
        # end allow environment override of rootpackage 
            
        module = self._init_root_package_from_path(root_package_path)
        
        try:
            return getattr(module, self.process_controller_interface_name)
        except AttributeError:
            raise AssertionError("Didn't find %s interface in module %s" % (self.process_controller_interface_name, str(module)))
        # end handle envrionment error
       
    def _root_package_path(self, executable):
        """@return a string to the folder containing the bcore.package or None if it wasn't found.
        We try to guesstimage it just by name
        @param executable possibly the original executable"""
        root_path = dirname(dirname(executable))
        if basename(root_path) == self.root_package_name:
            return dirname(root_path)
        return None
        
    def _init_root_package_from_path(self, root_package_path):
        """Initialize the given root package to make component services available
        @return module containing main interfaces"""
        sys.path.append(root_package_path)
        fmt = '%s.%s'
        module_for_import = fmt % (self.root_package_name, self.engine_interface_module_name)
        try:
            imported_module = __import__(module_for_import, globals(), locals(), [module_for_import])
            # get implementation 
            core_module = fmt % (self.root_package_name, self.engine_module_name)
            __import__(core_module, globals(), locals(), [core_module])
        except ImportError, err:
            traceback.print_exc()
            raise ImportError("Failed to import root package %s from path %s - cannot proceed without main \
implementation: %s" % (module_for_import, root_package_path, str(err)))
        # end handle import
        
        # assertion
        import __builtin__
        assert 'new_service' in __builtin__.__dict__, "Expected to receive component framework when importing %s" % module_for_import
        
        return imported_module
    ## -- End Utiltiies -- @}
    
    # -------------------------
    ## @name Interface
    # @{
    
    def main(self, executable, args = list()):
        """Main entry point
        Initialize this instance
        @param executable file we are running (never /bin/python)
        @param args all arguments the program received"""
        interface = self._process_controller_class(executable)

        # allow extensions to be used transparently to help starting the right interpreter on windows.
        # No special handling though to assure similar operation on all platforms
        executable = os.path.splitext(executable)[0]

        try:
            controller = new_service(interface).init(executable, args)
        except Exception, err:
            if interface._is_debug_mode():
                raise
            else:
                sys.stderr.write("%s\n" % str(err))
                sys.stderr.write("(Add ---debug flag for more information)\n")
            # end handle debugging
            sys.exit(2)
        #end 
        # if we are spawned, we return with whatever the spawned process says. Otherwise, this 
        # will not return
        sys.exit(controller.execute().returncode)
        
    ## -- End Interface -- @}
# end class Bootstrapper


if __name__ == '__main__':
    Bootstrapper().main(__file__, sys.argv[1:])
    

