#-*-coding:utf-8-*-
"""
@package bprocess.tests.base
@brief Utilities for all kinds of testing tasks

@author Sebastian Thiel
@copyright [GNU Lesser General Public License](https://www.gnu.org/licenses/lgpl.html)
"""
from __future__ import unicode_literals
from __future__ import division
__all__ = ['NosetestDelegate', 'PluginLoadingProcessAwareApplication']


import logging

import bapp
from bkvstore import KeyValueStoreSchema
from bprocess import (ProcessControllerDelegate,
                      ProcessAwareApplication,
                      ControlledProcessInformation,
                      PythonPackageIterator)
from butility import ( abstractmethod,
                       wraps,
                       Path )
from bapp.tests import preserve_application


log = logging.getLogger('bprocess.tests.base')



# ==============================================================================
# @name Base Classes
# ------------------------------------------------------------------------------
# Classes to use for all test-cases
# # @{


class PluginLoadingProcessAwareApplication(ProcessAwareApplication):
    """An application to load Plugins in any case, even if we have not been started by the wrapper.
    This works by specifying the entrypoint package, and it will do the right thing depending on 
    whether or not a wrapper was involved.
    @note useful for standalone testing on CI, where no wrapper is involved (as it comes in through 
        the parent assembly)
    """
    __slots__ = ('_package_name')

    # -------------------------
    ## @name Interface
    # @{

    @classmethod
    def new(cls, *args, **kwargs):
        """All parameters as in ProcessAwareApplication, but requires a package_name kwargs to 
        provide an entry point in case we were launched without wrapper"""
        package_name = kwargs.pop('package_name')
        if not package_name:
            raise ValueError("A package_name must be set to allow plugin loading if no wrapper is involved")
        # end assure package_name is set
        inst = super(PluginLoadingProcessAwareApplication, cls).new(*args, **kwargs)
        if not ControlledProcessInformation.has_data():
            PythonPackageIterator().import_modules(store=inst.context().settings(), package_name=package_name)
        # end 
        return inst
    
    ## -- End Interface -- @}

# end class PluginLoadingProcessAwareApplication


class NosetestDelegate(ProcessControllerDelegate):
    """This delegate does nothing more but to parse nose-specific arguments in the PostLaunch data structure.
    It also provides functionality to pick up the previously stored information and launch nose from it
    @note this requires nose to be available in the python path, ideally the wrapper provides it as well"""
    __slots__ = ()
    
    nose_schema = KeyValueStoreSchema('nosetests', { 'args' : list })
    
    def pre_start(self, executable, env, args, cwd, resolve):
        """Parse out all arguments until '--' and place them into extra process information.
        @note will place a new environment to assure we get those arguments over into the launched application"""
        try:
            sep_index = args.index('--')
            noseargs = args[:sep_index]

            def set_context_override(schema, value):
                value.args.extend(noseargs)
            # end 
            self.DelegateContextOverrideType('NosetestsOverride').setup(self._app.context(),
                                                                        set_context_override, 
                                                                        self.nose_schema)
            args = args[sep_index+1:]
            
            log.info("Starting nosetest with args: %s", ' '.join(noseargs))
        except ValueError:
            log.info('No nosetests arguments found - specify them using <nosetest flags> -- <hostapplication flags>')
        # end handle no special nosetests args
        
        return super(NosetestDelegate, self).pre_start(executable, env, args, cwd, resolve)
        
    # -------------------------
    ## @name Interface
    # @{
    
    @classmethod
    def start_nose(cls):
        """Start nose with the arguments previously specified on the commandline
        @return true if all tests succeeded, false on failure"""
        kvstore = ControlledProcessInformation().as_kvstore()
        value = kvstore.value_by_schema(cls.nose_schema)

        import nose        
        return nose.main(argv=['nosetests'] + value.args)
    ## -- End Interface -- @}


class PythonScriptNosetestDelegate(NosetestDelegate):
    """Provides a path to the script that, if executed, starts up nose with the required arguments.
    Its interface facilitates injecting the script into the arguments of the called process"""
    __slots__ = ()
    
    def entry_script_path(self):
        """@return path to python script that can serve as entrypoint"""
        return Path(__file__).dirname() / 'start-nose.py'
        
    def modify_args(self, args, script_path):
        """@return modified argument list containing entry_script_path() in a way that causes the hostapplication
        to execute it
        @param args program flags to modify
        @param script_path path to the script that is to be injected so that the program will execute it
        @note default implementation just returns script_path + args
        @note called from pre_start"""
        return [script_path] + args

    def pre_start(self, executable, env, args, cwd, resolve):
        executable, env, args, cwd = super(PythonScriptNosetestDelegate , self).pre_start(executable, env, args, cwd, resolve)
        args = self.modify_args(args, self.entry_script_path())
        assert isinstance(args, (list, tuple))
        return (executable, env, args, cwd)

# end class PythonScriptNosetestDelegate

## -- End Base Classes -- @}

