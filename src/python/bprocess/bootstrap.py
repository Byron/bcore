#!/usr/bin/env python
#-*-coding:utf-8-*-
"""
@package bprocess.bootstrap
@brief bootstrapper to allow importing the bprocess framework.

Using it's own location, it will alter the python path so that the bprocess package can be imported. 
It assumes that within that path, it will find all packages it depends on, which are all expected to be part
of the core repository.

@note this is an executable which is not meant to be imported. All dependencies are included in the file.

@author Sebastian Thiel
@copyright [GNU Lesser General Public License](https://www.gnu.org/licenses/lgpl.html)
"""
__all__ = ['Bootstrapper']

import sys
import os
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
    ** follow symlink of this file
    ** On windows, a side-by-side file will be read for the path to follow.
    * finally, adjust the path to initialize the root package and pass control to its implementation
    
    @note this bootstrapper needs to be symlinked to a certain location/basename to work 
    """
    __slots__ = ( )
    
    # -------------------------
    ## @name Configuration
    # @{
    
    ## Name of the root package that contains all of the process controller code
    root_package_name = 'bprocess'
    
    ## Process controller interface name
    process_controller_type_name = 'ProcessController'

    ## a per-directory file carrying information on where to find the bootstrapper
    boot_info_file = '.bprocess_path'

    ## -- End Configuration -- @}

    # -------------------------
    ## @name Utiltiies
    # @{

    def _resolve_win_link(self, executable):
        """Read a path from a side-by-side file and resolve it like a symlink"""
        try:
            link = open(os.path.join(os.path.dirname(executable), self.boot_info_file), 'rt').readline()
        except IOError:
            raise OSError
        return self._to_absolute_symlink(executable, link)
        
    def _to_absolute_symlink(self, executable, link_destination):
        """@return the resolved absolute symlink destination, similar to what the OS would do"""
        if os.path.isabs(link_destination):
            return link_destination
        # handle absolute paths
        
        # otherwise, treat it as relative to the executable dir
        return os.path.join(os.path.dirname(executable), link_destination)

    def _resolve_posix_symlink(self, executable):
        """@return the absolute resolved posix link"""
        return self._to_absolute_symlink(executable, os.readlink(executable))

    def _resolve_link(self, executable):
        """@return the next hop of the executable, assuming it has at least one level of symbolic 
        linking. It's possible for it to either be a standard symlink, or have a side-by-side
        text file to point the direction.
        The returned value is None if this is the last hop
        """
        try:
            if os.name == 'nt':
                return self._resolve_win_link(executable)
            else:
                try:
                    return self._resolve_posix_symlink(executable)
                except OSError:
                    # on posix, this means we might have failed to read a symbolic link, which can easily
                    # happen if we are on a smb share
                    # So we try to read the windows-style links (maybe one day even junctions using win32 lib)
                    # if this fails again, we are done
                    # This also means on linux, we always do extra FS queries ... but can't help it
                    return self._resolve_win_link(executable)
                # end 
            # end handle windows
        except OSError:
            return None
        # end handle no symlink case
        
    def _boot_info(self, executable):
        """Try to make our root-package available which should include the components framework
        to do that actual woractual_executablek for us
        Raise an error if that didn't work
        The returned hops are excluding the actual executable (first hop) and the last one, the bootstrapper 
        location within bcore, which is handled implicitly
        @return root module, controller type, hops"""
        hops = list()

        current_hop = executable
        while True:
            next_hop = self._resolve_link(current_hop)
            if next_hop is None:
                break
            # end 
            hops.append(next_hop)
            current_hop = next_hop
        # end for each hop to resolve

        if not hops:
            raise AssertionError("executable '%s' must be a symbolic link to the bootstrapper" % executable)
        # end handle no symlink

        actual_executable = hops.pop()

        
        root_package_path = self._root_package_path(actual_executable)
        if root_package_path is None:
            if root_package_path is None:
                msg = "Unable to find our 'bprocess' package from bootstrapper location at %s"
                msg += " - please make sure your executable is a symbolic link to the bootstrapper"
                raise AssertionError(msg % actual_executable)
            # end second attempt to make resolution
        # end handle root_package not found
        

        module = self._init_root_package_from_path(root_package_path)
        try:
            return module, getattr(module, self.process_controller_type_name), hops
        except AttributeError:
            msg = "Didn't find %s interface in module %s" % (self.process_controller_type_name, str(module))
            raise AssertionError(msg)
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
            import traceback
            traceback.print_exc()
            raise ImportError("Failed to import root package %s from path %s - cannot proceed without main \
implementation: %s" % (module_for_import, root_package_path, str(err)))
        # end handle import
        
        return imported_module

    @classmethod
    def handle_controller_call(self, bprocess_mod, controller, controller_call):
        """Handle all exceptions a controller could throw, when making the call
        @param bprocess module
        @param controller_call a callable
        @note use this method if you want to behave similarly to the standard bootstrapper"""
        try:
            return controller_call()
        except bprocess_mod.DisplayHelpException, err:
            sys.stderr.write(err.help_string)
        except bprocess_mod.DisplayContextException:
            sys.stderr.write(controller.application().context().pformat())
        except bprocess_mod.DisplaySettingsException:
            sys.stderr.write(str(controller.application().context().settings().data()))
        except bprocess_mod.DisplayLoadedYamlException:
            for ctx in controller.application().context().stack():
                if hasattr(ctx, 'config_files'):
                    for path in ctx.config_files():
                        sys.stderr.write(path + '\n')
                    # end for each path
                # end if context compatible
            # end for each environment
        except Exception, err:
            if controller.is_debug_mode():
                # sys.stderr.write(controller.application().context().pformat())
                sys.stderr.write("AN UNHANDLED EXCEPTION OCCURRED WHEN TRYING TO LAUNCH PROGRAM\n")
                sys.stderr.write("Controller-Delegate: %s\n" % controller.delegate())
                raise
            else:
                sys.stderr.write("ERROR: %s\n" % str(err))
                sys.stderr.write("(Add ---debug flag or set BAPP_STARTUP_LOG_LEVEL=DEBUG environment variable for more information)\n")
            # end handle debugging
        #end

    ## -- End Utiltiies -- @}
    
    # -------------------------
    ## @name Interface
    # @{
    
    def main(self, executable, args = list()):
        """Main entry point
        Initialize this instance
        @param executable file we are running (never /bin/python)
        @param args all arguments the program received"""
        root_module, process_controller_type, hops = self._boot_info(executable)

        # allow extensions to be used transparently to help starting the right interpreter on windows.
        # No special handling though to assure similar operation on all platforms
        executable = os.path.splitext(executable)[0]
        controller = process_controller_type(executable, args, context_paths = hops)


        # if we are spawned, we return with whatever the spawned process says. Otherwise, this 
        # will not return
        self.handle_controller_call(root_module, controller, lambda: sys.exit(controller.execute().returncode))

        # If we end up here, there was an exceptional condition
        sys.exit(2)
        
        
    ## -- End Interface -- @}
# end class Bootstrapper


if __name__ == '__main__':
    Bootstrapper().main(__file__, sys.argv[1:])
    

