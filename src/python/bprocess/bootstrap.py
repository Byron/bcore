#!/usr/bin/env python2.6
#-*-coding:utf-8-*-
"""
@package bprocess.bootstrap
@brief bootstrapper to allow importing the bprocess framework.

Using it's own location, it will alter the python path so that the bprocess package can be imported. 
It assumes that within that path, it will find all packages it depends on, which are all expected to be part
of the core repository.

@note this is an executable which is not meant to be imported. All dependencies are included in the file.

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

# BASIC LOGGING SETUP
#####################
logging.basicConfig()

# default stream output will be to stderr, which is good to separate output of program and bootstrapper
# in case there really is something to say
# Set lowest logging verbosity for a start
for item in chain([logging.root], logging.root.handlers):
    item.setLevel(logging.ERROR)
# end handle logging init



class Bootstrapper(object):
    """Contains for logic required to import bapp and launch the actual implementation from our root package.
    It implements the following algorithm
    
    * Find the bootstraps original, non-symlinked location and see if it is within its source tree. The following 
      locations are tried in order
    ** read BPROCESS_PACKAGE_PATH variable to the location from which root_package_name can be imported
    ** follow symlink of this file
    ** On windows, a side-by-side file will be read for the path to follow.
    * finally, adjust the path to initialize the root package and pass control to its implementation
    
    @note this bootstrapper needs to be symlinked to a certain location/basename to work 
    """
    __slots__ = ( )
    
    # -------------------------
    ## @name Configuration
    # @{
    
    ## A variable we can use to override the path which contains the bprocess package, useful for testing
    package_path_env_var = 'BPROCESS_PACKAGE_PATH'
    
    ## Name of the root package that contains all of the process controller code
    root_package_name = 'bprocess'
    
    ## Process controller interface name
    process_controller_type_name = 'ProcessController'
    
    ## -- End Configuration -- @}

    # -------------------------
    ## @name Utiltiies
    # @{
    
    def _resolve_winlink(self, executable):
        """Read a path from a side-by-side file and resolve it like a symlink"""
        symlink_file = os.path.join(os.path.dirname(executable), '.' + os.path.basename(executable))
        if not os.path.isfile(symlink_file):
            msg = "Side-by-side symlink file at '%s' did not exist - first line should be the location of the bootstrapper implementation"
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
        @return root module, controller type"""
        # If we have an override, use it
        if self.package_path_env_var in os.environ:
            root_package_path = os.environ[self.package_path_env_var]
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
            assert actual_executable != executable, "The executable %s must be as symlink to the bootstrapper implementation" % executable
            executable = actual_executable
            
            root_package_path = self._root_package_path(executable)
            if root_package_path is None:
                msg = "Unable to find our 'bprocess' package from bootstrapper location at %s"
                msg += " - please make sure your executable is a symbolic link to the bootstrapper"
                raise AssertionError(msg % executable)
            # end handle root_package not found
        # end allow environment override of rootpackage 
            
        module = self._init_root_package_from_path(root_package_path)
        
        try:
            return module, getattr(module, self.process_controller_type_name)
        except AttributeError:
            raise AssertionError("Didn't find %s interface in module %s" % (self.process_controller_type_name, str(module)))
        # end handle envrionment error
       
    def _root_package_path(self, executable):
        """@return a string to the folder containing the bapp.package or None if it wasn't found.
        We try to guesstimage it just by name
        @param executable possibly the original executable"""
        root_path = dirname(executable)
        if basename(root_path) == self.root_package_name:
            return dirname(root_path)
        return None
        
    def _init_root_package_from_path(self, root_package_path):
        """Initialize the given root package to make component instances available
        @return module containing main interfaces"""
        sys.path.append(root_package_path)
        module_for_import = self.root_package_name
        try:
            imported_module = __import__(module_for_import, globals(), locals(), [module_for_import])
        except ImportError, err:
            traceback.print_exc()
            raise ImportError("Failed to import root package %s from path %s - cannot proceed without main \
implementation: %s" % (module_for_import, root_package_path, str(err)))
        # end handle import
        
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
        root_module, process_controller_type = self._process_controller_class(executable)

        # allow extensions to be used transparently to help starting the right interpreter on windows.
        # No special handling though to assure similar operation on all platforms
        executable = os.path.splitext(executable)[0]
        controller = process_controller_type(executable, args)

        try:
            # if we are spawned, we return with whatever the spawned process says. Otherwise, this 
            # will not return
            sys.exit(controller.execute().returncode)    
        except root_module.DisplayHelpException, err:
            sys.stderr.write(err.help_string)
        except root_module.DisplayContextException:
            sys.stderr.write(controller.application().context()._contents_str())
        except Exception, err:
            if process_controller_type.is_debug_mode():
                # sys.stderr.write(controller.application().context()._contents_str())
                sys.stderr.write("AN UNHANDLED EXCEPTION OCCURRED WHEN TRYING TO LAUNCH PROGRAM\n")
                print "Controller-Delegate: ", controller.delegate()
                raise
            else:
                sys.stderr.write("ERROR: %s\n" % str(err))
                sys.stderr.write("(Add ---debug flag or set BAPP_STARTUP_LOG_LEVEL=DEBUG environment variable for more information)\n")
            # end handle debugging
            
        #end 

        # If we end up here, there was an exceptional condition
        sys.exit(2)
        
        
    ## -- End Interface -- @}
# end class Bootstrapper


if __name__ == '__main__':
    Bootstrapper().main(__file__, sys.argv[1:])
    

